"""
mod_core.py — Ядро мода MarksGraph для Lesta WoT (без Flash).

Рисует виджет и график через BigWorld GUI напрямую.
"""

import os
import json
import time
import BigWorld
import GUI

from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ViewEventType

from wot_marks_graph.config import ModConfig
from wot_marks_graph.stat_tracker import StatTracker
from wot_marks_graph.widget_renderer import WidgetRenderer

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
# data/ — рядом с модом: res_mods/1.42.0/scripts/client/gui/mods/wot_marks_graph/../../../../../../data/
DATA_DIR = os.path.normpath(os.path.join(MOD_DIR, '..', '..', '..', '..', '..', '..', '..', '..', 'data'))


class MarksGraphCore:
    """Ядро мода — управление жизненным циклом."""

    def __init__(self):
        self.config = ModConfig(DATA_DIR)
        self.stat_tracker = StatTracker(DATA_DIR)
        self.widget = None
        self._current_vehicle = None
        self._in_battle = False
        self._mouse_hooked = False

    def initialize(self):
        self.config.load()
        self.stat_tracker.load_history()
        self._setup_listeners()

    def _setup_listeners(self):
        g_eventBus.addListener(
            ViewEventType.LOBBY_VIEW,
            self._on_lobby_view,
            EVENT_BUS_SCOPE.LOBBY,
        )
        g_eventBus.addListener(
            ViewEventType.BATTLE_LOADING,
            self._on_battle_loading,
            EVENT_BUS_SCOPE.BATTLE,
        )
        g_eventBus.addListener(
            ViewEventType.BATTLE_RESULTS,
            self._on_battle_results,
            EVENT_BUS_SCOPE.BATTLE,
        )

    def on_lobby_ready(self):
        """Вызывается через ~0.5с после init — ангар уже загружен."""
        self._create_widget()
        self._update_vehicle_info()

    def _create_widget(self):
        """Создать Python-виджет без Flash."""
        cfg = self.config.data
        pos = cfg.get("hangar_position", {"x": 250, "y": 50})

        self.widget = WidgetRenderer(on_drag_end_cb=self._on_drag_ended)
        self.widget.create(pos["x"], pos["y"])
        self.widget.set_locked(cfg.get("battle_locked", False))

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
                self._update_widget_data(vehicle.name, mark)
        except Exception as e:
            print(f"[MarksGraph] get_vehicle_info error: {e}")

    def _update_widget_data(self, tank_name, mark_percent):
        if self.widget:
            self.widget.set_tank_info(tank_name)
            self.widget.set_mark_pct(mark_percent, 0.0)

    # === Обработчики событий ===

    def _on_lobby_view(self, event):
        BigWorld.callback(0.3, self._update_vehicle_info)

    def _on_battle_loading(self, event):
        self._in_battle = True
        if self.widget:
            self.widget.set_battle_mode(True)
            if self.config.data.get("battle_locked", False):
                self.widget.set_locked(True)

    def _on_battle_results(self, event):
        self._in_battle = False
        try:
            from gui.battle_results import BattleResults
            br = BattleResults()
            new_mark = self._get_post_battle_mark(br)
            if self._current_vehicle:
                self.stat_tracker.record_battle(
                    vehicle_name=self._current_vehicle.name,
                    mark_percent=new_mark,
                )
                self._update_widget_data(self._current_vehicle.name, new_mark)
                self._render_graph()
        except Exception as e:
            print(f"[MarksGraph] battle_results error: {e}")

        if self.widget:
            self.widget.set_battle_mode(False)
            self.widget.set_locked(self.config.data.get("battle_locked", False))

    def _get_post_battle_mark(self, br):
        try:
            if hasattr(br, 'personal') and hasattr(br.personal, 'avrMastery'):
                return br.personal.avrMastery
        except Exception:
            pass
        return self.stat_tracker.get_last_known_mark()

    # === Обработчики UI ===

    def _on_plus_clicked(self):
        if self.widget:
            self.widget.toggle_graph()
            if self.widget._graph_expanded:
                self._render_graph()

    def _on_pin_clicked(self):
        cfg = self.config.data
        cfg["battle_locked"] = not cfg.get("battle_locked", False)
        self.config.save()
        if self.widget:
            self.widget.set_locked(cfg["battle_locked"])

    def _on_filter_changed(self, filter_key):
        self.config.data["filter"] = filter_key
        self.config.save()
        self._render_graph()

    def _on_drag_ended(self, x, y):
        key = "battle_position" if self._in_battle else "hangar_position"
        self.config.data[key] = {"x": x, "y": y}
        self.config.save()

    def _render_graph(self):
        if not self._current_vehicle:
            return
        filter_key = self.config.data.get("filter", "week")
        graph_data = self.stat_tracker.build_graph_data(
            self._current_vehicle.name,
            filter_key,
        )
        points = graph_data.get("points", [])
        if self.widget:
            self.widget.render_graph(points)

    def destroy(self):
        try:
            g_eventBus.removeListener(
                ViewEventType.LOBBY_VIEW, self._on_lobby_view,
                EVENT_BUS_SCOPE.LOBBY,
            )
            g_eventBus.removeListener(
                ViewEventType.BATTLE_LOADING, self._on_battle_loading,
                EVENT_BUS_SCOPE.BATTLE,
            )
            g_eventBus.removeListener(
                ViewEventType.BATTLE_RESULTS, self._on_battle_results,
                EVENT_BUS_SCOPE.BATTLE,
            )
        except Exception:
            pass
        if self.widget:
            self.widget.destroy()
            self.widget = None
