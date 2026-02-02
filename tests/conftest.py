"""
Test Configuration and Fixtures
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.auth.user_store import init_default_admin

# Ensure default admin exists before tests
init_default_admin()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get auth headers by logging in as admin"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@ekoder.dev",
        "password": "admin123"
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


# Clinical validation test cases - real ED scenarios
CLINICAL_TEST_CASES = [
    {
        "id": 1,
        "description": "Chest pain - suspected cardiac",
        "text": "55 year old male presenting with central chest pain radiating to left arm. Pain started 2 hours ago. History of hypertension and smoking. ECG shows ST elevation in leads V1-V4. Troponin elevated.",
        "expected_codes": ["I21.0", "I21.1", "I21.9"],  # STEMI variants
        "complexity_range": (4, 6)
    },
    {
        "id": 2,
        "description": "Simple laceration",
        "text": "28 year old female with 3cm laceration to left forearm from kitchen knife. Clean wound, no tendon involvement. Wound cleaned and sutured with 5 interrupted sutures.",
        "expected_codes": ["S51.8", "T14.1"],
        "complexity_range": (1, 2)
    },
    {
        "id": 3,
        "description": "Pediatric fever",
        "text": "3 year old child with fever 39.2C for 2 days. Runny nose, mild cough. No rash. Ears clear. Throat mildly erythematous. Diagnosed viral upper respiratory tract infection.",
        "expected_codes": ["J06.9", "J00", "R50.9"],
        "complexity_range": (1, 2)
    },
    {
        "id": 4,
        "description": "Fractured ankle",
        "text": "45 year old male twisted ankle playing football. Significant swelling and bruising to lateral malleolus. X-ray confirms displaced fracture of lateral malleolus. Backslab applied, referred to orthopaedics.",
        "expected_codes": ["S82.6", "S82.60"],
        "complexity_range": (3, 4)
    },
    {
        "id": 5,
        "description": "Abdominal pain - appendicitis",
        "text": "22 year old female with 24 hour history of periumbilical pain now localised to RIF. Anorexia, nausea. Temperature 37.8. Tenderness McBurney's point with guarding. WCC elevated. CT confirms acute appendicitis.",
        "expected_codes": ["K35.8", "K35.9", "K35.80"],
        "complexity_range": (4, 5)
    },
    {
        "id": 6,
        "description": "Asthma exacerbation",
        "text": "8 year old known asthmatic with wheeze and respiratory distress. Unable to complete sentences. SpO2 92% on air. PEFR 50% predicted. Given salbutamol nebs x3 and prednisolone. Good response.",
        "expected_codes": ["J45.1", "J45.9", "J46"],
        "complexity_range": (3, 4)
    },
    {
        "id": 7,
        "description": "Head injury - minor",
        "text": "19 year old male fell off skateboard, hit head on pavement. Brief LOC at scene. GCS 15 on arrival. No vomiting. No focal neurology. CT head normal. Discharged with head injury advice.",
        "expected_codes": ["S06.0", "S00.9"],
        "complexity_range": (2, 3)
    },
    {
        "id": 8,
        "description": "Urinary tract infection",
        "text": "68 year old female with dysuria, frequency and suprapubic discomfort for 3 days. Temperature 37.5. Urine dipstick positive nitrites and leucocytes. Started on trimethoprim.",
        "expected_codes": ["N39.0", "N30.0"],
        "complexity_range": (2, 3)
    },
    {
        "id": 9,
        "description": "Allergic reaction",
        "text": "32 year old female with widespread urticaria and facial swelling after eating shellfish. No respiratory distress. BP stable. Given IM adrenaline, IV hydrocortisone and chlorphenamine.",
        "expected_codes": ["T78.0", "T78.3", "L50.0"],
        "complexity_range": (3, 4)
    },
    {
        "id": 10,
        "description": "Stroke presentation",
        "text": "72 year old male with sudden onset right-sided weakness and slurred speech. Symptom onset 90 minutes ago. AF on ECG. CT head shows left MCA territory infarct. Thrombolysis candidate.",
        "expected_codes": ["I63.9", "I63.5", "I64"],
        "complexity_range": (5, 6)
    },
    {
        "id": 11,
        "description": "Gastroenteritis",
        "text": "4 year old with vomiting x6 and diarrhoea x8 over 24 hours. Mildly dehydrated. Taking sips of oral rehydration solution. No blood in stool. Afebrile.",
        "expected_codes": ["A09", "K52.9"],
        "complexity_range": (2, 3)
    },
    {
        "id": 12,
        "description": "Back pain - mechanical",
        "text": "35 year old warehouse worker with acute low back pain after lifting heavy box. No leg symptoms. No red flags. Tenderness L4/5 paraspinal muscles. Normal neurology. Advised analgesia and mobilisation.",
        "expected_codes": ["M54.5", "M54.9", "S33.5"],
        "complexity_range": (1, 2)
    },
    {
        "id": 13,
        "description": "Sepsis",
        "text": "78 year old nursing home resident with confusion, fever 38.9, tachycardia 120, BP 85/50, respiratory rate 28. Source unclear. Lactate 4.2. Sepsis 6 pathway initiated. Blood cultures taken. IV antibiotics commenced.",
        "expected_codes": ["A41.9", "R65.1"],
        "complexity_range": (5, 6)
    }
]


@pytest.fixture
def clinical_cases():
    """Provide clinical test cases"""
    return CLINICAL_TEST_CASES
