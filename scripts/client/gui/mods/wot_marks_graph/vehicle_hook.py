"""
vehicle_hook.py — Получение текущего танка через WoT Lesta API.
"""

from gui.shared import g_itemsCache


def get_current_vehicle():
    """Вернуть объект текущего выбранного танка или None."""
    try:
        # В Lesta WoT текущий танк (vehicle) доступен через itemsCache
        # в diff — индекс 0 соответствует выбранному в ангаре
        items = g_itemsCache.items
        if not items:
            return None

        v_data = items.getVehicle(None)
        if v_data:
            return v_data

        # Fallback — перебор по инвентарю
        for v in items.getVehicles(True).values():
            if v.isInInventory and v.activeInNationGroup:
                return v
    except Exception as e:
        print(f"[MarksGraph] get_current_vehicle error: {e}")
        return None

    return None
