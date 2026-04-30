"""
mod_core.py — Ядро мода MarksGraph (Flash/SWF версия).

Загружает SWF-виджет через flash_bridge, управляет данными
и событиями в ангаре/бою.
"""

import os
import json
import BigWorld
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ViewEventType

from wot_marks_graph.config import ModConfig
from wot_marks_graph.stat_tracker import StatTracker
from wot_marks_graph.flash_bridge import initBridge, getBridge, fini as bridgeFini

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(
    MOD_DIR,
    '..', '..', '..', '..', '..', '..', '..', '..', 'data'
))


class MarksGraphCore:
    """Ядро мода — загрузка виджета, события, данные."""

    def __init__(self):
        self.config = ModConfig(DATA_DIR)
        self.stat_tracker = StatTracker(DATA_DIR)
        self._current_vehicle = None
        self._in_battle = False
        self._initialized = False

    def initialize(self):
        self.config.load()
        self.stat_tracker.load_history()
        self._setup_listeners()
        self._initialized = True

    def _setup_listeners(self):
        g_eventBus.addListener(
            ViewEventType.LOBBY_VIEW,
            self._on_lobby_view,
            EVENT_BUS_SCOPE.LOBBY,
        )

    def on_lobby_ready(self):
        """~0.5с после init — ангар готов."""
        if not self._initialized:
            self.initialize()
        self._create_widget()
        self._update_vehicle_info()

    # ==================== SWF Виджет ====================

    def _create_widget(self):
        """Создать Scaleform-мост и загрузить SWF."""
        bridge = initBridge()
        # TODO: добавить LoadView / attachMovie для MarkWidget.swf
        # Тут нужен контекст UiScaleformManager или AS_система
        # Пока просто создаём мост

    def _update_vehicle_info(self):
        try:
            from gui.shared import g_itemsCache
            from wot_marks_graph.vehicle_hook import get_current_vehicle

            vehicle = get_current_vehicle()
            if vehicle:
                mark = self.stat_tracker.get_mark_percent(
                    vehicle.intCD, vehicle.name
                )
                self._current_vehicle = vehicle
                self._update_widget(vehicle.name, mark)
        except Exception as e:
            print(f"[MarksGraph] info error: {e}")

    def _update_widget(self, tank_name, mark_data):
        """Отправить данные в SWF."""
        bridge = getBridge()
        if bridge is None:
            return

        if isinstance(mark_data, dict):
            percent = mark_data.get("mark", 0.0)
            mark_color = mark_data.get("markColor", 0x888888)
            change = mark_data.get("changeToday", 0.0)
            mark_label = mark_data.get("markLabel", "")
        else:
            percent = float(mark_data) if mark_data else 0.0
            mark_color = self._get_mark_color(percent)
            change = 0.0
            mark_label = self._get_mark_label(percent)

        bridge.setBattleData(tank_name)
        bridge.updateStats(percent, mark_color, change, mark_label)

    # ==================== События ====================

    def _on_lobby_view(self, event):
        """Ангар загружен — обновляем данные."""
        self._update_vehicle_info()

    def on_battle_started(self, vehicle_descr):
        """Вызывается при старте боя."""
        self._in_battle = True

    def on_battle_end(self, new_mark_percent):
        """Бой завершён — сохраняем статистику."""
        self._in_battle = False
        if self._current_vehicle:
            self.stat_tracker.record_battle(
                vehicle_name=self._current_vehicle.name,
                mark_percent=new_mark_percent,
            )
            self._update_widget(self._current_vehicle.name, new_mark_percent)

    # ==================== Вспомогательное ====================

    @staticmethod
    def _get_mark_color(pct):
        if pct >= 95:
            return 0xE8B800
        elif pct >= 85:
            return 0xCF7E44
        elif pct >= 65:
            return 0x4D9DE0
        return 0x888888

    @staticmethod
    def _get_mark_label(pct):
        if pct >= 95:
            return "3"
        elif pct >= 85:
            return "2"
        elif pct >= 65:
            return "1"
        return ""

    def destroy(self):
        try:
            g_eventBus.removeListener(
                ViewEventType.LOBBY_VIEW, self._on_lobby_view,
                EVENT_BUS_SCOPE.LOBBY,
            )
        except Exception:
            pass
        bridgeFini()
