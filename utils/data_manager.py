"""
data_manager.py — Загрузка/сохранение конфига и истории боёв.
Работает с JSON-файлами в папке data/ мода.
"""

import json
import os
import time
import threading

# Пути к файлам (относительно папки мода)
MOD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(MOD_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")

_MAX_BATTLES = 5000
_save_lock = threading.Lock()


# ── Конфиг ──────────────────────────────────────────────────────────────────

def get_default_config():
    """Безопасные настройки по умолчанию."""
    return {
        "hangar_position": {"x": 250, "y": 300},
        "battle_position": {"x": 250, "y": 50},
        "battle_locked": False,
        "expanded": False,
        "filter": "week",
        "style": {
            "widget_width": 220,
            "widget_height": 32,
            "graph_width": 250,
            "graph_height": 190,
            "opacity": 0.85,
            "glass_blur": 10,
            "accent_color": "0x88CCFF",
            "text_color": "0xFFFFFF",
            "positive_color": "0x44FF88",
            "negative_color": "0xFF4466",
            "lock_active_color": "0xFFD700",
            "lock_inactive_color": "0xAAAAAA",
            "animation_duration_ms": 300,
        },
    }


def load_config():
    """Загрузить config.json. Если нет или ошибка — вернуть default."""
    try:
        if not os.path.exists(CONFIG_PATH):
            cfg = get_default_config()
            save_config(cfg)
            return cfg
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Дополнить отсутствующими полями из default
        default = get_default_config()
        for key, val in default.items():
            if key not in cfg:
                cfg[key] = val
            elif isinstance(val, dict):
                for k2, v2 in val.items():
                    if k2 not in cfg[key]:
                        cfg[key][k2] = v2
        return cfg
    except Exception:
        return get_default_config()


def save_config(cfg):
    """Сохранить config.json (потокобезопасно)."""
    try:
        with _save_lock:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # Не падаем при ошибке записи


# ── История боёв ─────────────────────────────────────────────────────────────

def load_history():
    """Загрузить history.json. Если нет — вернуть {}."""
    try:
        if not os.path.exists(HISTORY_PATH):
            return {}
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_history(history):
    """Сохранить history.json (потокобезопасно)."""
    try:
        with _save_lock:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def record_battle(tank_id, tank_name, mark_percent, timestamp=None):
    """
    Записать результат боя в историю.
    Возвращает True, если запись новая (не дубликат), иначе False.
    """
    if timestamp is None:
        timestamp = int(time.time())

    history = load_history()
    tid = str(tank_id)

    if tid not in history:
        history[tid] = {"tank_name": tank_name, "battles": []}

    battles = history[tid]["battles"]

    # Проверка на дубликат (по timestamp)
    if battles and battles[-1]["ts"] == timestamp:
        return False
    if battles and battles[-1]["mark"] == mark_percent:
        # Если последний бой с таким же процентом — не дублируем
        if abs(battles[-1]["ts"] - timestamp) < 30:
            return False

    battles.append({"ts": timestamp, "mark": round(mark_percent, 2)})

    # Лимит — удалить старые
    if len(battles) > _MAX_BATTLES:
        battles[:] = battles[-_MAX_BATTLES:]

    history[tid] = {"tank_name": tank_name, "battles": battles}
    save_history(history)
    return True


# ── Фильтрация ───────────────────────────────────────────────────────────────

def get_filtered_battles(history_entry, filter_key, now_ts=None):
    """
    Вернуть список боёв (ts, mark) для заданного фильтра.
    filter_key: 'day' | 'week' | 'month'
    """
    if not history_entry or "battles" not in history_entry:
        return []

    if now_ts is None:
        now_ts = int(time.time())

    ranges = {"day": 86400, "week": 604800, "month": 2592000}
    cutoff = ranges.get(filter_key, 604800)

    filtered = []
    for b in history_entry["battles"]:
        if now_ts - b["ts"] <= cutoff:
            filtered.append((b["ts"], b["mark"]))

    return filtered


# ── Текущий танк (заглушка — при интеграции заменяется на BigWorld API) ─────

_current_tank_id = None
_current_tank_name = ""
_current_mark_percent = 0.0
_current_tank_nation = ""
_current_tank_tier = 0

def set_current_tank(tank_id, tank_name, mark_percent, nation="", tier=0):
    """Установить данные текущего танка (вызывается из api_hooks)."""
    global _current_tank_id, _current_tank_name, _current_mark_percent
    global _current_tank_nation, _current_tank_tier
    _current_tank_id = tank_id
    _current_tank_name = tank_name
    _current_mark_percent = mark_percent
    _current_tank_nation = nation
    _current_tank_tier = tier


def get_current_tank():
    """Вернуть словарь с данными текущего танка."""
    return {
        "id": _current_tank_id,
        "name": _current_tank_name,
        "mark": _current_mark_percent,
        "nation": _current_tank_nation,
        "tier": _current_tank_tier,
    }
