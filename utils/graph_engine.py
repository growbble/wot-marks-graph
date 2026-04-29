"""
graph_engine.py — Логика построения точек графика, фильтрации,
автомасштабирования и генерации команд для Flash-отрисовки.
"""

import time
from utils.data_manager import get_filtered_battles


def auto_scale_y(values, padding=5):
    """
    Автомасштабирование оси Y.
    Возвращает (y_min, y_max, step).
    padding — % отступа сверху/снизу от диапазона.
    """
    if not values:
        return (0, 100, 10)

    vmin = min(values)
    vmax = max(values)
    span = vmax - vmin

    if span < 1:
        # Почти константа — расширить
        vmin = max(0, vmin - padding)
        vmax = min(100, vmax + padding)
        span = vmax - vmin

    if span < 5:
        vmin = max(0, vmin - 2)
        vmax = min(100, vmax + 2)
        span = vmax - vmin

    # Красивые шаги
    raw_step = span / 5.0
    if raw_step <= 2:
        step = 2
    elif raw_step <= 5:
        step = 5
    elif raw_step <= 10:
        step = 10
    else:
        step = 20

    # Округлить вниз/вверх
    y_min = max(0, int(vmin / step) * step)
    y_max = min(100, int(vmax / step + 1) * step)
    if y_max > 100:
        y_max = 100
    if y_min == y_max:
        y_min = max(0, y_min - step)
        y_max = min(100, y_max + step)

    return (y_min, y_max, step)


def generate_timeline_labels(x_values, filter_key, max_labels=6):
    """
    Сгенерировать метки для оси X.
    Возвращает список (x_pos, label_text).
    """
    if not x_values:
        return []

    x_min = min(x_values)
    x_max = max(x_values)
    span = x_max - x_min

    if span == 0:
        return [(x_min, _format_ts(x_min, filter_key))]

    step = max(1, span // max_labels)

    labels = []
    for i in range(max_labels + 1):
        xi = x_min + i * step
        if xi > x_max:
            break
        label_text = _format_ts(int(xi), filter_key)
        labels.append((xi, label_text))

    return labels


def _format_ts(ts, filter_key):
    """Форматировать timestamp в метку оси X."""
    from datetime import datetime

    dt = datetime.utcfromtimestamp(ts)
    if filter_key == "day":
        return dt.strftime("%H:%M")
    elif filter_key == "week":
        return dt.strftime("%a %Hh")
    else:
        return dt.strftime("%d.%m")


def build_graph_data(tank_id, filter_key):
    """
    Основная функция: принимает ID танка и ключ фильтра,
    возвращает структуру для Flash-отрисовки.

    Возвращает:
    {
        "has_data": bool,
        "y_min": float, "y_max": float, "y_step": float,
        "x_min": int, "x_max": int,
        "points": [(x_ratio, y_ratio, ts, mark), ...],
        "labels_x": [(x_ratio, text), ...],
        "labels_y": [(y_ratio, text), ...],
        "message": str  # если данных нет
    }
    """
    from utils.data_manager import load_history

    history = load_history()
    entry = history.get(str(tank_id))

    battles = get_filtered_battles(entry, filter_key)

    if len(battles) < 2:
        msg = "Нет данных" if len(battles) == 0 else "Недостаточно данных для графика"
        return {
            "has_data": False,
            "message": msg,
            "points": [],
            "labels_x": [],
            "labels_y": [],
        }

    ts_list = [b[0] for b in battles]
    mark_list = [b[1] for b in battles]

    ts_min = min(ts_list)
    ts_max = max(ts_list)
    ts_span = ts_max - ts_min if ts_max != ts_min else 1

    y_min, y_max, y_step = auto_scale_y(mark_list)
    y_span = y_max - y_min if y_max != y_min else 1

    # Нормализованные точки для Flash (0.0 — 1.0)
    points = []
    for ts, mark in battles:
        x_ratio = (ts - ts_min) / float(ts_span)
        y_ratio = (mark - y_min) / float(y_span)
        points.append((round(x_ratio, 4), round(y_ratio, 4), ts, mark))

    # Метки оси Y
    labels_y = []
    y_val = y_min
    while y_val <= y_max:
        y_ratio = (y_val - y_min) / float(y_span)
        labels_y.append((round(y_ratio, 4), "{:.1f}%".format(y_val)))
        y_val += y_step

    # Метки оси X
    raw_labels_x = generate_timeline_labels(ts_list, filter_key)
    labels_x = []
    for xi, text in raw_labels_x:
        x_ratio = (xi - ts_min) / float(ts_span)
        labels_x.append((round(x_ratio, 4), text))

    return {
        "has_data": True,
        "message": "",
        "y_min": y_min,
        "y_max": y_max,
        "y_step": y_step,
        "x_min": ts_min,
        "x_max": ts_max,
        "points": points,
        "labels_x": labels_x,
        "labels_y": labels_y,
    }


def estimate_mark_change(current_mark, current_damage, avg_damage_last_100):
    """
    Прогноз изменения отметки за текущий бой.
    Упрощённая модель: чем больше урон относительно среднего, тем сильнее сдвиг.
    """
    if avg_damage_last_100 <= 0 or current_damage <= 0:
        return 0.0

    ratio = current_damage / avg_damage_last_100
    # Эмпирическая формула — для реализма заменить на точную
    change = (ratio - 1.0) * 2.0
    change = max(-5.0, min(5.0, change))
    return round(change, 2)
