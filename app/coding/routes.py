"""
Coding API Routes
POST /api/v1/code - Submit clinical text for coding
POST /api/v1/code/upload - Upload file for coding
"""
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
import logging

from app.coding.models import CodingRequest, CodingResponse, CandidateCode, HealthResponse
from app.coding.file_parser import parse_file
from app.coding.retriever import retriever
from app.coding.llm import build_prompt, query_llama, extract_code, extract_reasoning
from app.coding.sanitizer import sanitize_text
from app.audit.models import AuditAction
from app.audit.logger import log_event
from app.auth.utils import get_current_user_optional

router = APIRouter(prefix="/api/v1", tags=["coding"])
logger = logging.getLogger(__name__)

COMPLEXITY_LABELS = {
    1: "Minor (1)",
    2: "Low (2)",
    3: "Moderate (3)",
    4: "Significant (4)",
    5: "High (5)",
    6: "Very High (6)"
}


@router.post("/code", response_model=CodingResponse)
async def code_clinical_text(
    request: CodingRequest,
    http_request: Request,
    current_user=Depends(get_current_user_optional)
) -> CodingResponse:
    """
    Submit clinical text for ICD-10-AM coding

    Returns suggested code with reasoning and candidate list.
    All suggestions are flagged for human review (ACCD requirement).
    """
    start_time = time.time()
    error_msg = None
    suggested_code = None
    descriptor = None
    complexity = None
    candidate_count = 0

    try:
        # Sanitize input
        clean_text = sanitize_text(request.clinical_text)
        logger.info(f"Processing case: {len(clean_text)} characters")

        # Step 1: Retrieve candidates
        candidates = retriever.find_candidates(clean_text)
        valid_codes = [c['code'] for c in candidates]
        candidate_count = len(candidates)

        if not candidates:
            error_msg = "No matching codes found. Please review manually."
            return CodingResponse(error=error_msg)

        # Step 2: Query LLM
        prompt = build_prompt(clean_text, candidates)
        response_text, error = query_llama(prompt)

        if error:
            logger.error(f"LLM error: {error}")
            error_msg = f"LLM unavailable: {error}. Please select from candidates."
            return CodingResponse(
                candidates=[
                    CandidateCode(
                        code=c['code'],
                        descriptor=c['descriptor'],
                        score=c['score'],
                        source=c['source'],
                        complexity=c.get('complexity', 1)
                    )
                    for c in candidates[:10]
                ],
                error=error_msg
            )

        # Step 3: Extract code and reasoning
        suggested_code = extract_code(response_text, valid_codes)
        reasoning = extract_reasoning(response_text)

        # Find descriptor and complexity for suggested code
        confidence = 0.0
        if suggested_code:
            for c in candidates:
                if c['code'] == suggested_code:
                    descriptor = c['descriptor']
                    confidence = min(c['score'] * 100, 99.0)  # Cap at 99%
                    complexity = c.get('complexity', 1)
                    break

        return CodingResponse(
            suggested_code=suggested_code,
            descriptor=descriptor,
            reasoning=reasoning,
            confidence=round(confidence, 1),
            complexity=complexity,
            complexity_label=COMPLEXITY_LABELS.get(complexity) if complexity else None,
            candidates=[
                CandidateCode(
                    code=c['code'],
                    descriptor=c['descriptor'],
                    score=c['score'],
                    source=c['source'],
                    complexity=c.get('complexity', 1)
                )
                for c in candidates[:10]
            ],
            requires_human_review=True
        )

    except Exception as e:
        logger.exception("Coding error")
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Log the event for audit trail
        processing_time = int((time.time() - start_time) * 1000)
        try:
            log_event(
                action=AuditAction.SUBMIT_CASE,
                user_id=current_user.id if current_user else None,
                user_email=current_user.email if current_user else None,
                clinical_text=request.clinical_text,
                suggested_code=suggested_code,
                suggested_descriptor=descriptor,
                complexity=complexity,
                candidate_count=candidate_count,
                ip_address=http_request.client.host if http_request.client else None,
                user_agent=http_request.headers.get("user-agent"),
                processing_time_ms=processing_time,
                error=error_msg
            )
        except Exception as audit_error:
            logger.error(f"Failed to log audit event: {audit_error}")


@router.post("/code/upload", response_model=CodingResponse)
async def code_uploaded_file(
    http_request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user_optional)
) -> CodingResponse:
    """
    Upload a file (txt, pdf, docx) for ICD-10-AM coding

    Supported formats: .txt, .pdf, .docx
    """
    start_time = time.time()
    error_msg = None
    suggested_code = None
    descriptor = None
    complexity = None
    candidate_count = 0
    clinical_text = None

    try:
        # Read and parse file
        content = await file.read()
        clinical_text, error = parse_file(content, file.filename)

        if error:
            error_msg = error
            return CodingResponse(error=error)

        if not clinical_text or len(clinical_text.strip()) < 10:
            error_msg = "File is empty or contains insufficient text."
            return CodingResponse(error=error_msg)

        # Use the same logic as text endpoint
        clean_text = sanitize_text(clinical_text)
        logger.info(f"Processing uploaded file: {file.filename} ({len(clean_text)} chars)")

        # Retrieve candidates
        candidates = retriever.find_candidates(clean_text)
        valid_codes = [c['code'] for c in candidates]
        candidate_count = len(candidates)

        if not candidates:
            error_msg = "No matching codes found. Please review manually."
            return CodingResponse(error=error_msg)

        # Query LLM
        prompt = build_prompt(clean_text, candidates)
        response_text, llm_error = query_llama(prompt)

        if llm_error:
            logger.error(f"LLM error: {llm_error}")
            error_msg = f"LLM unavailable: {llm_error}. Please select from candidates."
            return CodingResponse(
                candidates=[
                    CandidateCode(
                        code=c['code'],
                        descriptor=c['descriptor'],
                        score=c['score'],
                        source=c['source'],
                        complexity=c.get('complexity', 1)
                    )
                    for c in candidates[:10]
                ],
                error=error_msg
            )

        # Extract code and reasoning
        suggested_code = extract_code(response_text, valid_codes)
        reasoning = extract_reasoning(response_text)

        confidence = 0.0
        if suggested_code:
            for c in candidates:
                if c['code'] == suggested_code:
                    descriptor = c['descriptor']
                    confidence = min(c['score'] * 100, 99.0)
                    complexity = c.get('complexity', 1)
                    break

        return CodingResponse(
            suggested_code=suggested_code,
            descriptor=descriptor,
            reasoning=reasoning,
            confidence=round(confidence, 1),
            complexity=complexity,
            complexity_label=COMPLEXITY_LABELS.get(complexity) if complexity else None,
            candidates=[
                CandidateCode(
                    code=c['code'],
                    descriptor=c['descriptor'],
                    score=c['score'],
                    source=c['source'],
                    complexity=c.get('complexity', 1)
                )
                for c in candidates[:10]
            ],
            requires_human_review=True,
            extracted_text=clinical_text
        )

    except Exception as e:
        logger.exception("File upload coding error")
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Log the event for audit trail
        processing_time = int((time.time() - start_time) * 1000)
        try:
            log_event(
                action=AuditAction.UPLOAD_FILE,
                user_id=current_user.id if current_user else None,
                user_email=current_user.email if current_user else None,
                clinical_text=clinical_text,
                filename=file.filename,
                suggested_code=suggested_code,
                suggested_descriptor=descriptor,
                complexity=complexity,
                candidate_count=candidate_count,
                ip_address=http_request.client.host if http_request.client else None,
                user_agent=http_request.headers.get("user-agent"),
                processing_time_ms=processing_time,
                error=error_msg
            )
        except Exception as audit_error:
            logger.error(f"Failed to log audit event: {audit_error}")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health and retriever status"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        codes_loaded=len(retriever.codes) if retriever._initialized else 0,
        embeddings_loaded=retriever.embeddings is not None if retriever._initialized else False
    )
