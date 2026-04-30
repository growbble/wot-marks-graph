"""
widget_renderer.py — Рендеринг виджета прогресса отметок и графика
напрямую через BigWorld GUI (без Flash/SWF).

Использует WGFlashComponent как канвас для рисования примитивов.
"""

import math
import BigWorld
import GUI

from wot_marks_graph.utils import hex_to_color, interpolate_color, clamp


class WidgetRenderer:
    """Рисует весь UI двумя WGFlashComponent слоями."""

    def __init__(self, on_drag_end_cb=None):
        self._on_drag_end = on_drag_end_cb

        # Размеры
        self.widget_w = 220
        self.widget_h = 60
        self.graph_w = 380
        self.graph_h = 220
        self.graph_panel_h = self.graph_h + 10

        # Компоненты
        self._root = None   # контейнер-невидимка для позиционирования
        self._widget = None # сам виджет
        self._graph = None  # панель графика

        # Состояние
        self._visible = True
        self._graph_expanded = False
        self._is_battle = False
        self._is_locked = False
        self._drag_offset = None

        # Данные
        self._tank_name = ""
        self._mark_pct = 0.0
        self._mark_change = 0.0
        self._graph_points = None  # список [{"x":..., "y":..., "ts":..., "mark":...}]

        # Цвета Catppuccin Mocha
        self.C_BG = hex_to_color("#1E1E2E", 0.9)
        self.C_SURFACE = hex_to_color("#313244", 0.85)
        self.C_OVERLAY = hex_to_color("#45475A", 0.5)
        self.C_TEXT = hex_to_color("#CDD6F4")
        self.C_SUBTEXT = hex_to_color("#A6ADC8")
        self.C_BLUE = hex_to_color("#89B4FA")
        self.C_GREEN = hex_to_color("#A6E3A1")
        self.C_RED = hex_to_color("#F38BA8")
        self.C_YELLOW = hex_to_color("#F9E2AF")

    def create(self, x, y):
        """Создать виджет на экране."""
        self._root = GUI.WGFlashComponent()
        self._root.size = (self.widget_w, self.widget_h + self.graph_panel_h + 10)
        self._root.position = (x, y)
        self._root.focus = True

        self._create_widget_layer()
        self._create_graph_layer()

        # Скрываем график изначально
        self._graph.visible = False

        self._redraw_widget()
        self._handle_mouse()

        GUI.addRoot(self._root)
        return self

    def _create_widget_layer(self):
        """Слой виджета (прогресс-бар, текст, кнопки)."""
        self._widget = GUI.WGFlashComponent()
        self._widget.size = (self.widget_w, self.widget_h)
        self._widget.position = (0, 0)
        self._root.addChild(self._widget, "widget")
        self._redraw_widget = self._widget_redraw

    def _widget_redraw(self):
        """Перерисовка слоя виджета."""
        self._draw_component(self._widget, self._render_widget_content)

    def _create_graph_layer(self):
        """Слой графика."""
        self._graph = GUI.WGFlashComponent()
        self._graph.size = (self.graph_w, self.graph_h + 10)
        self._graph.position = (0, self.widget_h + 2)
        self._root.addChild(self._graph, "graph_panel")

    # ============================================================
    # Рендеринг через Flash Canvas
    # ============================================================

    def _draw_component(self, comp, renderer):
        """Нарисовать через Flash Graphics битмап в компонент."""
        w, h = comp.size
        # Используем WGFlahsCanvas — если есть
        try:
            canvas = comp.getGraphics()
            canvas.clear()
            renderer(canvas, w, h)
            comp.refresh()
        except AttributeError:
            # Fallback без canvas — рисуем через setTexture
            pass

    def _render_widget_content(self, canvas, w, h):
        """Рисуем фон, прогресс-бар, текст, кнопки."""
        # Фон
        self._round_rect(canvas, 0, 0, w, h, 8, self.C_SURFACE)
        canvas.lineStyle(1, self.C_OVERLAY, 0.6)
        self._round_rect(canvas, 0, 0, w, h, 8, 0x000000, fill=False)

        # Заголовок (название танка)
        canvas.drawText(self._tank_name, 10, 6, self.C_TEXT, 11, bold=True)

        # Полоса прогресса
        bar_x, bar_y = 10, 30
        bar_w, bar_h = w - 70, 8
        fill_width = max(2, int(bar_w * (self._mark_pct / 100.0)))

        canvas.beginFill(self.C_OVERLAY, 0.5)
        self._round_rect(canvas, bar_x, bar_y, bar_w, bar_h, 4, 0, fill=False)
        canvas.endFill()

        color = self.C_BLUE
        if self._mark_pct >= 95:
            color = self.C_GREEN
        elif self._mark_pct <= 65:
            color = self.C_RED

        canvas.beginFill(color, 0.9)
        self._round_rect(canvas, bar_x, bar_y, fill_width, bar_h, 4, 0, fill=False)
        canvas.endFill()

        # Процент
        pct_text = f"{self._mark_pct:.1f}%"
        canvas.drawText(pct_text, 10, 44, self.C_TEXT, 11, bold=True)

        # Изменение
        if self._mark_change != 0:
            sign = "+" if self._mark_change > 0 else ""
            ch_text = f"{sign}{self._mark_change:.2f}%"
            ch_color = self.C_GREEN if self._mark_change > 0 else self.C_RED
            canvas.drawText(ch_text, 60, 44, ch_color, 10)

        # Кнопки
        btn_x = w - 16
        canvas.beginFill(self.C_OVERLAY, 0.8)
        canvas.drawCircle(btn_x, 20, 10)
        canvas.endFill()
        plus_char = "─" if self._graph_expanded else "+"
        canvas.drawText(plus_char, btn_x - 4, 14, self.C_TEXT, 14, bold=True)

        pin_x = w - 40
        canvas.beginFill(self.C_OVERLAY, 0.8)
        canvas.drawCircle(pin_x, 20, 10)
        canvas.endFill()
        pin_color = self.C_GREEN if self._is_locked else self.C_SUBTEXT
        canvas.drawText("📌", pin_x - 7, 10, pin_color, 12)

    def _render_graph_content(self, canvas, w, h):
        """Рисуем панель графика с точками."""
        if not self._graph_points or len(self._graph_points) < 2:
            canvas.drawText("Нет данных", 10, 10, self.C_SUBTEXT, 10)
            return

        # Фон
        self._round_rect(canvas, 0, 0, w, h, 8, self.C_BG)
        canvas.lineStyle(1, self.C_OVERLAY)
        self._round_rect(canvas, 0, 0, w, h, 8, 0, fill=False)

        margin = 50
        cw = w - margin * 2 + 20
        ch = h - 60

        points = self._graph_points
        marks = [p["mark"] for p in points]
        y_min = max(0, min(marks) - 2)
        y_max = min(100, max(marks) + 2)
        y_range = y_max - y_min if y_max > y_min else 1

        first_ts = points[0]["ts"]
        last_ts = points[-1]["ts"]
        t_range = last_ts - first_ts if last_ts > first_ts else 1

        # Сетка
        for i in range(6):
            ly = int(ch - (y_min + y_range * i / 5 - y_min) / y_range * ch)
            canvas.lineStyle(1, self.C_OVERLAY, 0.3)
            canvas.moveTo(0, ly)
            canvas.lineTo(cw, ly)

            if i % 2 == 0:
                y_label = f"{y_min + y_range * i / 5:.1f}%"
                canvas.drawText(y_label, -40, ly - 6, self.C_SUBTEXT, 8)

        # Линия графика
        canvas.lineStyle(2, self.C_BLUE, 0.9)
        first = True
        for idx, p in enumerate(points):
            px = (p["ts"] - first_ts) / t_range * cw
            py = ch - (p["mark"] - y_min) / y_range * ch
            if first:
                canvas.moveTo(px, py)
                first = False
            else:
                canvas.lineTo(px, py)

        # Точки
        for idx, p in enumerate(points):
            px = (p["ts"] - first_ts) / t_range * cw
            py = ch - (p["mark"] - y_min) / y_range * ch
            canvas.lineStyle(0)
            canvas.beginFill(self.C_YELLOW, 0.9)
            canvas.drawCircle(px, py, 3)
            canvas.endFill()

    def _round_rect(self, canvas, x, y, w, h, r=0, color=0x000000, fill=True):
        """Нарисовать скруглённый прямоугольник на канвасе."""
        if fill:
            canvas.beginFill(color, 1.0)
            canvas.drawRoundedRect(x, y, w, h, r)
            canvas.endFill()
        else:
            canvas.drawRoundedRect(x, y, w, h, r)

    # ============================================================
    # Обновление данных
    # ============================================================

    def set_tank_info(self, name):
        self._tank_name = name
        self._redraw()

    def set_mark_pct(self, pct, change=0.0):
        self._mark_pct = clamp(pct, 0, 100)
        self._mark_change = change
        self._redraw()

    def set_battle_mode(self, battle):
        self._is_battle = battle
        if battle and self._graph_expanded:
            self.toggle_graph()
        self._redraw()

    def set_locked(self, locked):
        self._is_locked = locked
        self._redraw()

    def toggle_graph(self):
        self._graph_expanded = not self._graph_expanded
        self._graph.visible = self._graph_expanded
        if self._graph_expanded:
            self._redraw_graph()
        self._redraw_widget()
        return self._graph_expanded

    def render_graph(self, points):
        """Обновить данные графика и перерисовать."""
        self._graph_points = points
        self._redraw_graph()

    def move_to(self, x, y):
        if self._root:
            self._root.position = (x, y)

    def get_position(self):
        if self._root:
            return self._root.position
        return (0, 0)

    def destroy(self):
        if self._root:
            try:
                GUI.delRoot(self._root)
            except Exception:
                pass
            self._root = None

    # ============================================================
    # Mouse handling
    # ============================================================

    def _handle_mouse(self):
        """Подписка на клики для кнопок и драга."""
        # WoT не даёт прямого MouseEvent на WGFlashComponent,
        # поэтому используем хук с проверкой ввода BigWorld
        pass

    def handle_click(self, screen_x, screen_y):
        """Обработать клик — вызвать из внешнего хука."""
        if not self._root or not self._visible:
            return False

        rx, ry = self.get_position()
        if not (rx <= screen_x <= rx + self.widget_w and
                ry <= screen_y <= ry + self.widget_h):
            return False

        local_x = screen_x - rx
        local_y = screen_y - ry

        # Кнопка +
        btn_x = self.widget_w - 16
        if math.hypot(local_x - btn_x, local_y - 20) < 12:
            return True  # сигнал onPlusClicked

        # Кнопка 📌
        pin_x = self.widget_w - 40
        if math.hypot(local_x - pin_x, local_y - 20) < 12:
            return True  # сигнал onPinClicked

        # Drag
        if self._is_battle and self._is_locked:
            return False
        self._drag_offset = (local_x, local_y)
        return True

    def handle_drag_release(self, screen_x, screen_y):
        if self._drag_offset:
            new_x = screen_x - self._drag_offset[0]
            new_y = screen_y - self._drag_offset[1]
            self.move_to(max(0, new_x), max(0, new_y))
            self._drag_offset = None
            if self._on_drag_end:
                self._on_drag_end(new_x, new_y)
            return True
        return False

    # ============================================================
    # Internal
    # ============================================================

    def _redraw(self):
        self._redraw_widget()

    def _redraw_graph(self):
        self._draw_component(self._graph, self._render_graph_content)
