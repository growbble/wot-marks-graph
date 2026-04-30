"""
mod_core.py — Ядро мода MarksGraph для Lesta WoT.

Получает процент отметки из статистики игрока, управляет Flash-виджетом,
сохраняет историю боёв.
"""

import os
import json
import time
import BigWorld
import GUI
import Math

from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ViewEventType, ViewEvent
from helpers import getClientLanguage

from wot_marks_graph.config import ModConfig
from wot_marks_graph.stat_tracker import StatTracker
from wot_marks_graph.flash_bridge import FlashBridge

# Путь к данным мода (рядом с модом, в res_mods/1.42.0/scripts/client/gui/mods/)
MOD_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(MOD_DIR, '..', '..', '..', '..', '..', '..', '..', '..', 'data')
DATA_DIR = os.path.normpath(DATA_DIR)


class MarksGraphCore:
    """Ядро мода — управление жизненным циклом."""

    def __init__(self):
        self.config = ModConfig(DATA_DIR)
        self.stat_tracker = StatTracker(DATA_DIR)
        self.flash = FlashBridge()
        self._current_vehicle = None
        self._in_battle = False
        self._widget_instance = None
        self._battle_subscriptions = []

    def initialize(self):
        """Подготовка без UI (в ангаре ещё не загружен)."""
        self.config.load()
        self.stat_tracker.load_history()
        self._setup_listeners()

    def _setup_listeners(self):
        """Подписка на события ангара и боя."""
        # Смена танка в ангаре
        g_eventBus.addListener(
            ViewEventType.LOBBY_VIEW,
            self._on_lobby_view,
            EVENT_BUS_SCOPE.LOBBY,
        )
        # Начало боя
        g_eventBus.addListener(
            ViewEventType.BATTLE_LOADING,
            self._on_battle_loading,
            EVENT_BUS_SCOPE.BATTLE,
        )
        # Конец боя
        g_eventBus.addListener(
            ViewEventType.BATTLE_RESULTS,
            self._on_battle_results,
            EVENT_BUS_SCOPE.BATTLE,
        )

    def on_lobby_ready(self):
        """Вызывается через ~0.5с после init — ангар уже загружен."""
        self._create_hangar_widget()
        self._update_vehicle_info()

    def _create_hangar_widget(self):
        """Создать Flash-виджет в ангаре."""
        cfg = self.config.data
        pos = cfg.get("hangar_position", {"x": 250, "y": 50})

        # Загружаем SWF через Scaleform
        self.flash.load_widget(
            "marks_graph/MarkWidget.swf",
            "MarkWidget",
            pos["x"],
            pos["y"],
            cfg["style"]["widget_width"],
            cfg["style"]["widget_height"],
            callback=self._on_widget_created,
        )

    def _on_widget_created(self, widget_mc):
        """Виджет загружен — настроить колбэки."""
        self._widget_instance = widget_mc
        # Настроим Flash → Python колбэки
        widget_mc.onPlusClicked = self._on_plus_clicked
        widget_mc.onPinClicked = self._on_pin_clicked
        widget_mc.onFilterChanged = self._on_filter_changed
        widget_mc.onDragEnded = self._on_drag_ended

        # Настроим позиционные колбэки из Flash
        if self.config.data.get("battle_locked", False):
            self._widget_instance.setLockIcon(True)

    def _update_vehicle_info(self):
        """Получить данные текущего танка из WoT API."""
        try:
            from gui.shared.utils.requesters import StatsRequester
            from gui.shared.gui_items import GUIItem
            from items.vehicles import VehicleDescriptor

            # Получаем ID текущего танка из интерфейса
            from gui.shared import g_itemsCache
            vehicle = g_itemsCache.items.getVehicle(0)  # ID будет заменён реальным

            if vehicle:
                mark = self.stat_tracker.get_mark_percent(
                    vehicle.intCD, vehicle.name
                )
                self._current_vehicle = vehicle
                self._update_widget_data(vehicle.name, mark)
        except Exception as e:
            print(f"[MarksGraph] get_vehicle_info error: {e}")

    def _update_widget_data(self, tank_name, mark_percent):
        """Обновить данные на Flash-виджете."""
        if self._widget_instance:
            self._widget_instance.setTankInfo(tank_name)
            self._widget_instance.setMarkPercent(mark_percent, 0.0)

    # === Обработчики событий ===

    def _on_lobby_view(self, event):
        """Смена вида в ангаре (переключение между танками)."""
        BigWorld.callback(0.3, self._update_vehicle_info)

    def _on_battle_loading(self, event):
        """Загрузка боя — переключить виджет в боевой режим."""
        self._in_battle = True
        if self._widget_instance:
            self._widget_instance.setBattleMode(True)
            if self.config.data.get("battle_locked", False):
                self._widget_instance.disableDrag()

        # Подписка на обновление процента отметки в бою
        self._battle_subscriptions = []

    def _on_battle_results(self, event):
        """Окончание боя — сохранить результат."""
        self._in_battle = False
        try:
            # Получить результат боя и новый процент отметки
            from gui.battle_results import BattleResults
            br = BattleResults()
            new_mark = self._get_post_battle_mark(br)
            if self._current_vehicle:
                self.stat_tracker.record_battle(
                    vehicle_name=self._current_vehicle.name,
                    mark_percent=new_mark,
                )
                self._update_widget_data(self._current_vehicle.name, new_mark)
                # Построить график
                self._render_graph()
        except Exception as e:
            print(f"[MarksGraph] battle_results error: {e}")

        if self._widget_instance:
            self._widget_instance.setBattleMode(False)
            self._widget_instance.enableDrag()

    def _get_post_battle_mark(self, br):
        """Извлечь процент отметки из результатов боя."""
        try:
            # В Lesta WoT процент отметки доступен через personal/avrMastery
            if hasattr(br, 'personal') and hasattr(br.personal, 'avrMastery'):
                return br.personal.avrMastery
        except Exception:
            pass
        return self.stat_tracker.get_last_known_mark()

    # === Callbacks из Flash ===

    def _on_plus_clicked(self):
        """Кнопка + нажата — открыть/закрыть график."""
        if self._widget_instance:
            expanded = self._widget_instance.toggleGraph()
            if expanded:
                self._render_graph()

    def _on_pin_clicked(self):
        """Кнопка скрепки — фиксация позиции."""
        cfg = self.config.data
        cfg["battle_locked"] = not cfg.get("battle_locked", False)
        self.config.save()
        if self._widget_instance:
            self._widget_instance.setLockIcon(cfg["battle_locked"])

    def _on_filter_changed(self, filter_key):
        """Смена фильтра графика."""
        self.config.data["filter"] = filter_key
        self.config.save()
        self._render_graph()

    def _on_drag_ended(self, x, y):
        """Перетаскивание завершено — сохранить позицию."""
        key = "battle_position" if self._in_battle else "hangar_position"
        self.config.data[key] = {"x": x, "y": y}
        self.config.save()

    def _render_graph(self):
        """Построить и отправить данные графика во Flash."""
        if not self._current_vehicle:
            return
        filter_key = self.config.data.get("filter", "week")
        graph_data = self.stat_tracker.build_graph_data(
            self._current_vehicle.name,
            filter_key,
        )
        if self._widget_instance:
            self._widget_instance.renderGraph(json.dumps(graph_data))

    def destroy(self):
        """Очистка при выгрузке мода."""
        try:
            g_eventBus.removeListener(
                ViewEventType.LOBBY_VIEW,
                self._on_lobby_view,
                EVENT_BUS_SCOPE.LOBBY,
            )
            g_eventBus.removeListener(
                ViewEventType.BATTLE_LOADING,
                self._on_battle_loading,
                EVENT_BUS_SCOPE.BATTLE,
            )
            g_eventBus.removeListener(
                ViewEventType.BATTLE_RESULTS,
                self._on_battle_results,
                EVENT_BUS_SCOPE.BATTLE,
            )
        except Exception:
            pass
        if self.flash:
            self.flash.destroy()
