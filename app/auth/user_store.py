"""
Simple JSON-based User Store
For production, replace with a proper database
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from uuid import uuid4

from app.auth.models import UserInDB, UserCreate, UserRole
from app.auth.utils import get_password_hash

# Store users in a JSON file
USERS_FILE = Path(__file__).parent.parent.parent / "data" / "users.json"


def _load_users() -> Dict[str, dict]:
    """Load users from JSON file"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def _save_users(users: Dict[str, dict]):
    """Save users to JSON file"""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2, default=str)


def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Find user by email"""
    users = _load_users()
    for user_id, user_data in users.items():
        if user_data.get('email') == email:
            return UserInDB(**user_data)
    return None


def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Find user by ID"""
    users = _load_users()
    user_data = users.get(user_id)
    if user_data:
        return UserInDB(**user_data)
    return None


def create_user(user_data: UserCreate) -> UserInDB:
    """Create a new user"""
    users = _load_users()

    # Check if email already exists
    if get_user_by_email(user_data.email):
        raise ValueError("Email already registered")

    user_id = str(uuid4())
    new_user = UserInDB(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
        created_at=datetime.utcnow(),
        is_active=True
    )

    users[user_id] = new_user.model_dump()
    _save_users(users)

    return new_user


def update_last_login(user_id: str):
    """Update user's last login timestamp"""
    users = _load_users()
    if user_id in users:
        users[user_id]['last_login'] = datetime.utcnow().isoformat()
        _save_users(users)


def init_default_admin():
    """Create a default admin user if no users exist"""
    print(f"Checking for users in {USERS_FILE}...")
    users = _load_users()
    print(f"Found {len(users)} existing users")
    if not users:
        try:
            create_user(UserCreate(
                email="admin@ekoder.dev",
                name="Admin",
                password="admin123",  # Change this in production!
                role=UserRole.ADMIN
            ))
            print("Created default admin user: admin@ekoder.dev / admin123")
        except Exception as e:
            print(f"ERROR creating admin user: {e}")
    else:
        print(f"Admin already exists: {list(users.values())[0].get('email', 'unknown')}")
