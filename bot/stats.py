import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

STATS_FILE = DATA_DIR / "stats.json"

DEFAULT_STATS = {
    "start": 0,
    "service_open": 0,
    "requisites_open": 0,
    "form_started": 0,
    "form_completed": 0,
    "updated_at": None,
}


def load_stats() -> dict:
    if not STATS_FILE.exists():
        save_stats(DEFAULT_STATS.copy())
        return DEFAULT_STATS.copy()

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        save_stats(DEFAULT_STATS.copy())
        return DEFAULT_STATS.copy()


def save_stats(stats: dict) -> None:
    stats["updated_at"] = datetime.utcnow().isoformat()
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def inc_stat(key: str) -> None:
    stats = load_stats()
    if key not in stats:
        stats[key] = 0
    stats[key] += 1
    save_stats(stats)


def format_stats() -> str:
    stats = load_stats()

    return (
        "📊 Загальна статистика\n\n"
        f"Старт: {stats.get('start', 0)}\n"
        f"Відкрито карток: {stats.get('service_open', 0)}\n"
        f"Відкрито реквізити: {stats.get('requisites_open', 0)}\n"
        f"Розпочато заповнення: {stats.get('form_started', 0)}\n"
        f"Завершено заповнення: {stats.get('form_completed', 0)}"
    )