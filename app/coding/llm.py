"""
LLM Integration: Llama-3.3-70B via HuggingFace API
Handles prompt building and code extraction
"""
import re
import requests
from typing import List, Dict, Optional, Tuple

from app.config import settings


# Few-shot examples for clinical coding
FEW_SHOT_EXAMPLES = """
EXAMPLE 1: Substance-Induced Psychosis
Case: 30yo male, erratic behaviour, grandiose delusions, UDS positive for methamphetamine. Diagnosis: Substance-induced psychosis.
WRONG: F30.9 (Manic episode) - Misses the substance cause
CORRECT: F15.01 (Intoxication from methylamphetamine) - Codes the specific substance

EXAMPLE 2: Urinary Retention with Underlying Tumor
Case: Hematuria for 5 months, now acute urinary retention due to clot. Known bladder tumor. Admitted for TURBT.
WRONG: D41.9 (Bladder neoplasm) - Codes underlying disease, not ED presentation
CORRECT: R33 (Urinary retention) - Codes the acute reason for ED attendance

EXAMPLE 3: Arterial vs Traumatic Injury
Case: Blue hand after blood draw, no pulses by Doppler, angiogram shows brachial artery occlusion, thrombectomy performed.
WRONG: S55.9 (Vessel injury of forearm) - S codes are for trauma/lacerations
CORRECT: I74.9 (Embolism or thrombosis of artery) - Codes vascular occlusion
"""


def build_prompt(clinical_text: str, candidate_codes: List[Dict]) -> str:
    """Build the prompt for Llama-3.3-70B"""
    codes_text = "\n".join([
        f"  {c['code']} - {c['descriptor']}"
        for c in candidate_codes
    ])

    return f"""You are an expert clinical coder for Australian Emergency Departments using the ICD-10-AM ED Short List.

=== CRITICAL CODING RULES ===
1. Code the PRINCIPAL REASON FOR ED ATTENDANCE TODAY, not underlying chronic conditions
2. For substance-induced conditions: code the SUBSTANCE (F10-F19), not the psychiatric symptom
3. Acute injuries use S/T codes; chronic/vascular conditions use I/M codes
4. If patient has symptom caused by disease, code the SYMPTOM if that's why they came to ED
5. You MUST choose from the candidate codes below - no other codes are valid
6. DIAGNOSIS vs SYMPTOM HIERARCHY: If a definitive diagnosis is confirmed (by imaging, labs, or clinical assessment), ALWAYS code the diagnosis, NOT the presenting symptom.
   - Fracture confirmed on imaging -> Code the fracture, not "pain"
   - Pericarditis confirmed on ECG -> Code pericarditis, not "chest pain"
   - Delirium diagnosed -> Code delirium, not "hallucinations"
   Only code symptoms (R codes) when no diagnosis is established.

=== WORKED EXAMPLES ===
{FEW_SHOT_EXAMPLES}

=== CANDIDATE CODES (choose from these ONLY) ===
{codes_text}

=== CLINICAL CASE ===
{clinical_text}

=== YOUR TASK ===
Select the single BEST code from the candidates above.

Respond in this EXACT format:
CODE: [code]
REASONING: [one sentence explaining why]
"""


def query_llama(prompt: str) -> Tuple[str, Optional[str]]:
    """
    Query Llama-3.3-70B via HuggingFace API

    Returns:
        Tuple of (response_text, error_message)
    """
    headers = {
        "Authorization": f"Bearer {settings.HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.1
    }

    try:
        response = requests.post(
            settings.HF_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return content, None

        return "", f"API error: {response.status_code} - {response.text[:200]}"

    except requests.Timeout:
        return "", "Request timed out (120s). HuggingFace API may be busy."
    except Exception as e:
        return "", f"Request failed: {str(e)}"


def extract_code(response_text: str, valid_codes: List[str]) -> Optional[str]:
    """Extract the suggested code from LLM response"""
    # Try to match CODE: format
    match = re.search(r'CODE:\s*([A-Z]\d{2}\.?\d{0,2})', response_text, re.IGNORECASE)
    if match:
        code = match.group(1)
        if code in valid_codes:
            return code

    # Fallback: find any valid code in response
    for code in valid_codes:
        if code in response_text:
            return code

    return None


def extract_reasoning(response_text: str) -> str:
    """Extract the reasoning from LLM response"""
    match = re.search(r'REASONING:\s*(.+)', response_text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().split('\n')[0]
    return ""
