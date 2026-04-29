"""
widget_core.py — Создание и управление Flash-виджетом через GUIFlash.

Это ядро UI-компонента. В реальном клиенте использует Flash API.
Для тестирования без игры — эмулирует через консольный вывод и
генерацию HTML/CSS прототипов.
"""

import json
import os
import time

# Попытка импорта Lesta Flash API (вне игры — заглушка)
try:
    import gui.flash as Flash
    _HAS_FLASH = True
except ImportError:
    _HAS_FLASH = False

# Попытка импорта BigWorld для координат экрана
try:
    import BigWorld
    _HAS_BIGWORLD = True
except ImportError:
    _HAS_BIGWORLD = False


# ── Конфигурация экрана ──────────────────────────────────────────────────────

def get_screen_size():
    """Получить размер экрана игры."""
    if _HAS_BIGWORLD:
        try:
            w = BigWorld.screenWidth()
            h = BigWorld.screenHeight()
            return (w, h)
        except Exception:
            pass
    # Значения по умолчанию для Full HD
    return (1920, 1080)


# ── Цветовые константы (GLASSMORPHISM) ────────────────────────────────────────

# Базовый "белое стекло" стиль
STYLE_GLASS = """
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    box-shadow: 0 4px 30px rgba(255, 255, 255, 0.1);
    color: #FFFFFF;
"""

STYLE_LABEL = """
    font-family: 'Arial', sans-serif;
    font-size: 12px;
    font-weight: 600;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    color: #FFFFFF;
"""

STYLE_PROGRESS_BAR_TRACK = """
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    height: 6px;
"""

STYLE_PROGRESS_BAR_FILL = """
    background: linear-gradient(90deg, #66BBFF, #88CCFF);
    border-radius: 4px;
    height: 6px;
    transition: width 0.3s ease;
"""

STYLE_BUTTON = """
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    color: #FFFFFF;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
"""

STYLE_BUTTON_HOVER = """
    background: rgba(255, 255, 255, 0.25);
"""

# ── Виджет — ядро ─────────────────────────────────────────────────────────────

class MarksWidget:
    """
    Единый UI-компонент для ангара и боя.

    В реальном клиенте создаёт Flash-мувиклипы.
    В режиме эмуляции (без игры) — печатает прототип в консоль/файл.
    """

    def __init__(self, config):
        self.config = config
        self.widget_width = config["style"]["widget_width"]
        self.widget_height = config["style"]["widget_height"]
        self.graph_width = config["style"]["graph_width"]
        self.graph_height = config["style"]["graph_height"]
        self.is_battle = False
        self.is_expanded = False

        # Текущее состояние
        self.mark_percent = 0.0
        self.mark_change = 0.0  # +/- в бою
        self.tank_name = ""
        self.tank_id = None

        # Flash-ссылки (в реальном клиенте)
        self._flash_widget = None
        self._flash_graph = None
        self._flash_plus_btn = None

        # Состояние кнопки-трансформера
        self._plus_rotation = 0
        self._plus_is_cross = False
        self._animating = False

    # ── Жизненный цикл ──────────────────────────────────────────────────────

    def create(self, parent, x, y, is_battle=False):
        """
        Создать Flash-виджет в родительском контейнере.
        Возвращает ссылку на себя.
        """
        self.is_battle = is_battle

        if _HAS_FLASH:
            self._create_flash_widget(parent, x, y)
        else:
            self._create_emulated(is_battle)

        return self

    def _create_flash_widget(self, parent, x, y):
        """Создать через Flash Scaleform (реальный клиент)."""
        # В реальном клиенте:
        # self._flash_widget = parent.createMovieClip(
        #     "mark_widget.swf", x, y, self.widget_width, self.widget_height
        # )
        pass

    def _create_emulated(self, is_battle):
        """Эмуляция — прототип для отладки."""
        print(f"\n[MarksGraph] {'[БОЙ]' if is_battle else '[АНГАР]'} Виджет создан")
        print(f"  Размер: {self.widget_width}x{self.widget_height}")
        print(f"  Координаты: см. config.json")
        print(f"  Стиль: Белое стекло (Glassmorphism)")
        print(f"  График: {'есть' if not is_battle else 'только в бою прогноз'}")

    def destroy(self):
        """Уничтожить виджет."""
        if self._flash_widget:
            # self._flash_widget.remove()
            self._flash_widget = None
        self._flash_graph = None
        self._flash_plus_btn = None

    # ── Позиционирование ──────────────────────────────────────────────────────

    def set_position(self, x, y):
        """Переместить виджет."""
        if self._flash_widget:
            # self._flash_widget.x = x
            # self._flash_widget.y = y
            pass

    def get_position(self):
        """Вернуть текущую позицию."""
        cfg_key = "battle_position" if self.is_battle else "hangar_position"
        pos = self.config.get(cfg_key, {"x": 250, "y": 50})
        return (pos["x"], pos["y"])

    # ── Обновление данных ─────────────────────────────────────────────────────

    def update_mark(self, percent, change=0.0):
        """
        Обновить процент отметки.
        В бою change — прогноз изменения за текущий бой.
        """
        self.mark_percent = percent
        self.mark_change = change

        if _HAS_FLASH:
            # Вызвать ActionScript методы flash-ролика
            self._call_flash("setMarkPercent", percent, change)
        else:
            # Эмуляция — вывести в консоль
            change_str = f"{change:+0.2f}%" if change != 0 else ""
            bar_len = int(percent / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            color = "\033[92m" if change >= 0 else "\033[91m" if change < 0 else ""
            reset = "\033[0m"
            sign = "+" if change >= 0 else ""
            print(
                f"\r[MarksGraph] {self.tank_name or '???'}: "
                f"[{bar}] {percent:.1f}%  "
                f"{color}{sign}{change:.2f}%{reset}  ",
                end="", flush=True,
            )

    def update_tank_info(self, tank_name, tank_id):
        """Обновить информацию о танке."""
        self.tank_name = tank_name
        self.tank_id = tank_id
        if _HAS_FLASH:
            self._call_flash("setTankInfo", tank_name, tank_id)

    # ── Flash-коммуникация ────────────────────────────────────────────────────

    def _call_flash(self, method, *args):
        """Вызвать ActionScript-метод Flash-ролика."""
        if self._flash_widget:
            try:
                # self._flash_widget.call(method, *args)
                pass
            except Exception:
                pass

    def flash_callback(self, action, data):
        """
        Обратный вызов из Flash (ActionScript вызывает Python).
        action: 'plus_clicked', 'pin_clicked', 'filter_changed',
                'drag_ended', 'graph_hover'
        """
        if action == "plus_clicked":
            self._toggle_graph()
        elif action == "pin_clicked":
            self._toggle_lock()
        elif action == "filter_changed":
            self._on_filter_change(data)
        elif action == "drag_ended":
            self._on_drag_end(data)
        elif action == "graph_hover":
            self._on_graph_hover(data)

    # ── Анимация плюсика ──────────────────────────────────────────────────────

    def _toggle_graph(self):
        """Открыть/закрыть панель графика (только ангар)."""
        if self.is_battle:
            return

        self.is_expanded = not self.is_expanded
        self._plus_is_cross = self.is_expanded

        if _HAS_FLASH:
            # Анимация: поворот +45° за 150ms
            # self._call_flash("animatePlusRotation", 45 if self._plus_is_cross else -45)
            pass

        if self.is_expanded:
            self._open_graph_panel()
        else:
            self._close_graph_panel()

        print(f"\n[MarksGraph] График {'открыт' if self.is_expanded else 'закрыт'}")

    def _open_graph_panel(self):
        """Выдвинуть панель графика."""
        if _HAS_FLASH:
            # self._call_flash("animateGraphPanel", "open", self.graph_height)
            pass

    def _close_graph_panel(self):
        """Схлопнуть панель графика."""
        if _HAS_FLASH:
            # self._call_flash("animateGraphPanel", "close", 0)
            pass

    # ── Фиксация (скрепка) ────────────────────────────────────────────────────

    def _toggle_lock(self):
        """Переключить фиксацию позиции для боя."""
        current = self.config.get("battle_locked", False)
        self.config["battle_locked"] = not current
        self._update_lock_icon()
        print(
            f"\n[MarksGraph] Позиция в бою "
            f"{'зафиксирована' if self.config['battle_locked'] else 'разблокирована'}"
        )

    def _update_lock_icon(self):
        """Обновить иконку скрепки в Flash."""
        locked = self.config.get("battle_locked", False)
        color = self.config["style"]["lock_active_color"] if locked \
                else self.config["style"]["lock_inactive_color"]
        if _HAS_FLASH:
            # self._call_flash("setLockIcon", "locked" if locked else "unlocked", color)
            pass

    def is_locked(self):
        """Проверить, зафиксирована ли позиция в бою."""
        return self.config.get("battle_locked", False)

    # ── График ────────────────────────────────────────────────────────────────

    def render_graph(self, graph_data, filter_key):
        """
        Отрисовать график в Flash-панели.
        graph_data — результат graph_engine.build_graph_data()
        """
        if not graph_data["has_data"]:
            if _HAS_FLASH:
                # self._call_flash("showGraphMessage", graph_data["message"])
                pass
            print(f"\n[MarksGraph] График: {graph_data['message']}")
            return

        if _HAS_FLASH:
            # Передать точки и метки во Flash через JSON
            payload = json.dumps(graph_data)
            # self._call_flash("renderGraph", payload)
            pass
        else:
            # Эмуляция — ASCII-график
            self._print_ascii_graph(graph_data, filter_key)

    def _print_ascii_graph(self, data, filter_key):
        """
        Нарисовать ASCII-версию графика (для отладки без Flash).
        """
        if not data["has_data"]:
            return

        points = data["points"]
        labels_y = data["labels_y"]
        labels_x = data["labels_x"]

        HEIGHT = 12
        WIDTH = 40

        y_min = data["y_min"]
        y_max = data["y_max"]

        # Создать сетку
        grid = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]

        # Отрисовать точки
        max_x = max(p[0] for p in points) if points else 1
        for xr, yr, ts, mark in points:
            col = int(xr * (WIDTH - 1))
            row = HEIGHT - 1 - int(yr * (HEIGHT - 1))
            row = max(0, min(HEIGHT - 1, row))
            col = max(0, min(WIDTH - 1, col))
            if grid[row][col] in (" ", "·"):
                grid[row][col] = "●"

        # Соединить линии
        if len(points) > 1:
            for i in range(len(points) - 1):
                x1 = int(points[i][0] * (WIDTH - 1))
                y1 = HEIGHT - 1 - int(points[i][1] * (HEIGHT - 1))
                x2 = int(points[i+1][0] * (WIDTH - 1))
                y2 = HEIGHT - 1 - int(points[i+1][1] * (HEIGHT - 1))
                # Простое интерполирование
                steps = max(abs(x2 - x1), abs(y2 - y1))
                if steps > 0:
                    for s in range(1, steps):
                        sx = int(x1 + (x2 - x1) * s / steps)
                        sy = int(y1 + (y2 - y1) * s / steps)
                        if 0 <= sy < HEIGHT and 0 <= sx < WIDTH:
                            if grid[sy][sx] == " ":
                                grid[sy][sx] = "·"

        # Сборка строк
        print(f"\n[MarksGraph] График отметок (фильтр: {filter_key}):")
        print(f"  {y_max:.1f}% ─" + "─" * WIDTH)
        for r in range(HEIGHT):
            # Y-метка
            y_val = y_max - (y_max - y_min) * r / (HEIGHT - 1)
            if r == 0 or r == HEIGHT - 1 or r == HEIGHT // 2:
                label = f"{y_val:5.1f} │"
            else:
                label = "      │"
            print(label + "".join(grid[r]))
        print(f"  {'':>5} └" + "─" * WIDTH)

        # X-метки
        x_label_line = "       "
        for xr, text in labels_x[:6]:
            col = int(xr * (WIDTH - 1))
            while len(x_label_line) < col + 1:
                x_label_line += " "
            x_label_line += text[:5]
        print(x_label_line)

        print(f"  Всего точек: {len(points)}")
        print(f"  Диапазон: {y_min:.1f}% — {y_max:.1f}%")

    # ── Обработчики ───────────────────────────────────────────────────────────

    def _on_filter_change(self, filter_key):
        """Смена фильтра графика."""
        self.config["filter"] = filter_key
        if self.tank_id is not None:
            from utils.graph_engine import build_graph_data
            data = build_graph_data(self.tank_id, filter_key)
            self.render_graph(data, filter_key)

    def _on_drag_end(self, position):
        """Перетаскивание завершено — сохранить позицию."""
        key = "battle_position" if self.is_battle else "hangar_position"
        self.config[key] = {"x": position[0], "y": position[1]}

    def _on_graph_hover(self, point_index):
        """Наведение на точку графика."""
        pass


# ── Создание виджета ─────────────────────────────────────────────────────────

def create_widget(config, is_battle=False):
    """
    Фабричный метод: создать и вернуть настроенный виджет.
    """
    widget = MarksWidget(config)
    screen_w, screen_h = get_screen_size()
    pos_key = "battle_position" if is_battle else "hangar_position"
    pos = config.get(pos_key, {"x": screen_w // 2 - 110, "y": 50})
    widget.create(None, pos["x"], pos["y"], is_battle=is_battle)
    return widget
