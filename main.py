#!/usr/bin/env python3
"""
main.py — Точка входа мода MarksGraph для Lesta World of Tanks.

Алгоритм инициализации:
1. Загрузить config.json.
2. Определить контекст (ангар / бой).
3. Создать экземпляр основного виджета.
4. Если ангар — кнопка расширения + панель графика.
5. Если бой — проверить battle_locked, отключить drag при True.
6. Подписаться на игровые события.
"""

import os
import sys

# Добавить корень мода в sys.path (для импортов)
MOD_DIR = os.path.dirname(os.path.abspath(__file__))
if MOD_DIR not in sys.path:
    sys.path.insert(0, MOD_DIR)

from utils.data_manager import load_config, save_config, get_current_tank
from utils.api_hooks import (
    setup_hooks, event_bus, is_in_battle, get_current_mark_percent,
    emulate_tank_change, emulate_mark_update, emulate_battle_end,
    _emulation_mode as EMULATION_MODE,
)
from utils.widget_core import create_widget
from utils.graph_engine import build_graph_data, estimate_mark_change
from utils.data_manager import load_history, record_battle


# ── Точка входа ──────────────────────────────────────────────────────────────

def main():
    """Главная функция — вызывается при загрузке мода."""
    print("=" * 60)
    print("  MarksGraph v1.0.0 — Виджет отметок на стволе")
    print("  Стиль: Белое стекло (Glassmorphism)")
    print("=" * 60)

    # 1. Конфигурация
    config = load_config()
    if config["filter"] not in ("day", "week", "month"):
        config["filter"] = "week"

    # 2. Контекст
    in_battle = is_in_battle()
    print(f"  Контекст: {'БОЙ' if in_battle else 'АНГАР'}")

    # 3. Виджет
    widget = create_widget(config, is_battle=in_battle)

    # 4. Если ангар — подготовить график
    if not in_battle:
        _setup_hangar_mode(widget, config)
    else:
        _setup_battle_mode(widget, config)

    # 5. Подписка на события
    setup_hooks()

    # 6. Первое обновление
    _update_widget(widget)

    # 7. Запись виджета в глобальную область (для доступа из других модулей)
    _global_widget = widget

    print("=" * 60)
    print("  Мод загружен. Настройки: data/config.json")
    print("=" * 60)

    return widget


# ── Режимы ────────────────────────────────────────────────────────────────────

def _setup_hangar_mode(widget, config):
    """Настройка для ангара — кнопка расширения + график."""
    print("  Режим ангара: кнопка «+» и панель графика доступны")

    # Если конфиг говорит expanded=True — развернуть график при загрузке
    if config.get("expanded", False):
        # Восстановим состояние из конфига
        pass

    # Отобразить иконку фиксации (скрепка)
    widget._update_lock_icon()


def _setup_battle_mode(widget, config):
    """Настройка для боя — проверка блокировки, прогноз урона."""
    locked = config.get("battle_locked", False)
    if locked:
        print("  Перетаскивание в бою ЗАБЛОКИРОВАНО (скрепка замкнута)")
    else:
        print("  Перетаскивание в бою РАЗРЕШЕНО (скрепка разомкнута)")


# ── Обновление ────────────────────────────────────────────────────────────────

def _update_widget(widget):
    """Обновить виджет текущими данными."""
    tank = {
        "name": "T-34-85",  # будет заменено на get_current_tank()
        "mark": 85.3,
        "id": 111,
    }
    if not EMULATION_MODE:
        tank = get_current_tank()

    widget.update_tank_info(tank.get("name", "???"), tank.get("id"))
    widget.update_mark(
        percent=tank.get("mark", 0),
        change=0.0,  # в бою будет прогноз
    )


# ── Обработчики событий ──────────────────────────────────────────────────────

def on_mark_changed(mark_percent):
    """Вызывается из api_hooks при изменении отметки."""
    global _global_widget
    if _global_widget:
        _global_widget.update_mark(percent=mark_percent)


def on_battle_ended(new_mark):
    """Вызывается после боя."""
    global _global_widget
    # Записать в историю
    tank_info = get_current_tank() if not EMULATION_MODE else {
        "id": 111, "name": "T-34-85"}
    record_battle(
        tank_id=tank_info["id"],
        tank_name=tank_info["name"],
        mark_percent=new_mark,
    )
    # Обновить виджет
    if _global_widget:
        _global_widget.update_mark(percent=new_mark)


# Глобальная ссылка (чтобы не потерять)
_global_widget = None


# ── Точка входа для тестирования ─────────────────────────────────────────────

if __name__ == "__main__":
    import time

    widget = main()

    # Эмуляция смены танка
    print("\n  [ТЕСТ] Эмуляция использования:")
    time.sleep(0.5)

    # Сменить танк
    emulate_tank_change(222, "IS-7", 92.5)
    _update_widget(widget)
    time.sleep(0.3)

    # Открыть график
    widget._toggle_graph()
    time.sleep(0.3)

    # Построить график
    from utils.graph_engine import build_graph_data
    data = build_graph_data(222, "week")
    widget.render_graph(data, "week")
    time.sleep(0.3)

    # Сменить фильтр
    widget._on_filter_change("day")
    time.sleep(0.3)

    # Закрыть график
    widget._toggle_graph()
    time.sleep(0.3)

    # Имитация боя: обновление марки в реальном времени
    print("\n  [ТЕСТ] Симуляция боя:")
    for _ in range(3):
        emulate_mark_update(93.0 + _ * 0.5)
        time.sleep(0.2)

    # Фиксация
    widget._toggle_lock()
    widget._toggle_lock()

    print("\n\n  ✅ Тест завершён.")
    print("  Папка мода:", MOD_DIR)
    print("  Файлы данных: data/config.json, data/history.json")
