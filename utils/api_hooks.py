"""
api_hooks.py — Перехватчики игровых событий для получения
процента отметки, данных о танке, окончания боя.

В Lesta WoT Python-моды используют BigWorld, Event, Account,
и Avatar API. Этот модуль предоставляет интерфейс для подписки
на события, независимо от точной версии клиента.

Для тестирования вне игры используется эмуляция.
"""

import time
from utils.data_manager import set_current_tank, record_battle


# ── Абстракция игровых событий ──────────────────────────────────────────────

class _EventBus:
    """Простая шина событий для мода (в игре заменяется на Event/GameEvents)."""
    def __init__(self):
        self._handlers = {}

    def on(self, event_name, handler):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def off(self, event_name, handler):
        if event_name in self._handlers:
            self._handlers[event_name] = [h for h in self._handlers[event_name]
                                          if h != handler]

    def emit(self, event_name, **kwargs):
        for handler in self._handlers.get(event_name, []):
            try:
                handler(**kwargs)
            except Exception as e:
                print(f"[MarksGraph] Error in handler for {event_name}: {e}")


event_bus = _EventBus()


# ── Заглушки для тестирования (когда игра не запущена) ──────────────────────

_emulation_mode = True  # False в реальном клиенте
_emulation_data = {
    "tank_id": 111,
    "tank_name": "T-34-85",
    "mark_percent": 85.3,
    "nation": "ussr",
    "tier": 6,
    "damage": 0,
    "avg_damage_100": 1200,
}


# ── Основные функции ─────────────────────────────────────────────────────────

def is_in_battle():
    """
    Определить, находимся ли мы в бою.
    В реальном клиенте: проверять наличие Avatar или battle session.
    """
    # Заглушка — всегда False (ангар). В реальном коде заменить.
    return False


def get_current_mark_percent():
    """
    Получить процент отметки текущего танка.
    В реальном клиенте:
      player = BigWorld.player()
      if player and hasattr(player, 'vehicleTypeDescriptor'):
          # Через маркеры или напрямую из статистики
          ...
    """
    return _emulation_data["mark_percent"]


def get_vehicle_info():
    """Получить информацию о текущем танке."""
    return {
        "id": _emulation_data["tank_id"],
        "name": _emulation_data["tank_name"],
        "nation": _emulation_data["nation"],
        "tier": _emulation_data["tier"],
    }


def setup_hooks():
    """
    Установить перехватчики игровых событий.

    В реальном клиенте:

    1. Подписка на смену танка в ангаре:
       from gui.shared import g_eventBus, EVENT_BUS_SCOPE
       g_eventBus.addListener('lobbyChanged', _on_lobby_changed, EVENT_BUS_SCOPE.LOBBY)

    2. Подписка на обновление статистики:
       from gui.shared.utils.requesters import StatsRequester
       # или через events

    3. Подписка на окончание боя:
       from gui.battle_results import BattleResults
    """
    # Подписаться на шину событий мода
    event_bus.on("tank_changed", _on_tank_changed)
    event_bus.on("battle_ended", _on_battle_ended)
    event_bus.on("mark_updated", _on_mark_updated)

    # Инициализировать текущий танк
    _update_current_tank()


def _update_current_tank():
    """Обновить данные текущего танка из игры."""
    info = get_vehicle_info()
    mark = get_current_mark_percent()
    set_current_tank(
        tank_id=info["id"],
        tank_name=info["name"],
        mark_percent=mark,
        nation=info["nation"],
        tier=info["tier"],
    )


def _on_tank_changed(**kwargs):
    """Обработчик смены танка."""
    _update_current_tank()


def _on_battle_ended(**kwargs):
    """Обработчик окончания боя."""
    # Получить новый процент отметки
    new_mark = kwargs.get("new_mark", get_current_mark_percent())
    info = get_vehicle_info()
    record_battle(
        tank_id=info["id"],
        tank_name=info["name"],
        mark_percent=new_mark,
    )
    _update_current_tank()


def _on_mark_updated(**kwargs):
    """Обработчик обновления процента отметки (в бою)."""
    new_mark = kwargs.get("mark", kwargs.get("percent", 0))
    if new_mark > 0:
        set_current_tank(
            tank_id=_emulation_data.get("tank_id"),
            tank_name=_emulation_data.get("tank_name"),
            mark_percent=new_mark,
        )


# ── Эмуляция для тестирования ───────────────────────────────────────────────

def emulate_tank_change(tank_id, tank_name, mark_percent):
    """Эмулировать смену танка (для отладки)."""
    _emulation_data["tank_id"] = tank_id
    _emulation_data["tank_name"] = tank_name
    _emulation_data["mark_percent"] = mark_percent
    event_bus.emit("tank_changed")


def emulate_battle_end(new_mark):
    """Эмулировать конец боя (для отладки)."""
    event_bus.emit("battle_ended", new_mark=new_mark)


def emulate_mark_update(mark):
    """Эмулировать обновление марки в бою (для отладки)."""
    _emulation_data["mark_percent"] = mark
    event_bus.emit("mark_updated", mark=mark)
