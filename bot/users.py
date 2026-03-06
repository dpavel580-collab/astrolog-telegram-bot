import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"


def load_users() -> dict:
    if not USERS_FILE.exists():
        save_users({})
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        save_users({})
        return {}


def save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def register_user(user) -> None:
    users = load_users()

    user_id = str(user.id)
    users[user_id] = {
        "user_id": user.id,
        "username": getattr(user, "username", None),
        "first_name": getattr(user, "first_name", ""),
        "last_name": getattr(user, "last_name", ""),
        "updated_at": datetime.utcnow().isoformat(),
    }

    save_users(users)


def get_users_count() -> int:
    return len(load_users())


def get_all_user_ids() -> list[int]:
    users = load_users()
    return [int(uid) for uid in users.keys()]