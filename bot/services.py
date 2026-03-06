from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets"

EXTS = (".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP")


def find_image(*names: str):
    for name in names:
        for ext in EXTS:
            p = ASSETS_DIR / f"{name}{ext}"
            if p.exists():
                return str(p)
    return None


SERVICES = [
    {
        "id": "natal",
        "title": "🌟 Натальна карта",
        "price_uah": 3500,
        "form_type": "birth",
        "image": find_image("natal"),
    },
    {
        "id": "solar",
        "title": "☀️ Соляр (прогноз на рік)",
        "price_uah": 2500,
        "form_type": "birth",
        "image": find_image("solar"),
    },
    {
        "id": "lunar",
        "title": "🌙 Лунар (прогноз на місяць)",
        "price_uah": 500,
        "form_type": "birth",
        "image": find_image("lunar"),
    },
    {
        "id": "tarot1",
        "title": "🃏 Розклад таро 1 сфера",
        "price_uah": 800,
        "form_type": "tarot",
        "image": find_image("tarot1"),
    },
    {
        "id": "tarot3",
        "title": "🔮🃏 Розклад таро 3 сфери",
        "price_uah": 1800,
        "form_type": "tarot",
        "image": find_image("tarot3"),
    },
    {
        "id": "child_natal",
        "title": "👶⭐ Дитяча натальна карта",
        "price_uah": 2500,
        "form_type": "child_birth",
        "image": find_image("child_natal"),
    },
    {
        "id": "relations",
        "title": "💞 Розбір в сфері стосунків",
        "price_uah": 2000,
        "form_type": "birth",
        "image": find_image("relations"),
    },
    {
        "id": "work_finance",
        "title": "💼💰 Розбір в сфері роботи та фінансів",
        "price_uah": 2000,
        "form_type": "birth",
        "image": find_image("work_finance"),
    },
    {
        "id": "consult",
        "title": "🎥🕒 Індивідуальна відео консультація 1 година",
        "price_uah": 3000,
        "form_type": "consult",
        "image": find_image("consult", "consultation", "consultations"),
    },
]


def get_service(service_id: str):
    return next((s for s in SERVICES if s["id"] == service_id), None)