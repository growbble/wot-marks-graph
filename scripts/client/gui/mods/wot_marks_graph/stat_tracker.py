"""
stat_tracker.py — Отслеживание отметок и история боёв.

Работает со статистикой игрока через WoT API.
Сохраняет историю в data/history.json.
"""

import json
import os
import time
from collections import defaultdict

from gui.shared.utils.requesters import StatsRequester
from gui.shared import g_itemsCache


class StatTracker:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.history_path = os.path.join(data_dir, "history.json")
        self.history = []  # [{"timestamp", "vehicle_name", "mark"}]
        self.last_known_mark = 95.0

    def load_history(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []
        else:
            self.history = []
            self.save_history()

    def save_history(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def record_battle(self, vehicle_name, mark_percent):
        self.history.append({
            "timestamp": int(time.time()),
            "vehicle_name": vehicle_name,
            "mark": round(mark_percent, 2),
        })
        self.last_known_mark = mark_percent
        self.save_history()

    def get_mark_percent(self, vehicle_intcd, vehicle_name):
        """
        Получить процент отметки из WoT статистики.
        В Lesta WoT доступен через avrMastery в персональной статистике.
        """
        try:
            stats = g_itemsCache.items.getVehicleDossier(vehicle_intcd)
            if stats and hasattr(stats, 'getStats'):
                s = stats.getStats()
                if s and 'avrMastery' in s:
                    mark = float(s['avrMastery'])
                    self.last_known_mark = mark
                    return mark
        except Exception as e:
            print(f"[MarksGraph] get_mark error: {e}")

        # Fallback: ищем последнюю запись в истории для этого танка
        for entry in reversed(self.history):
            if entry["vehicle_name"] == vehicle_name:
                return entry["mark"]
        return self.last_known_mark

    def get_last_known_mark(self):
        return self.last_known_mark

    def build_graph_data(self, vehicle_name, filter_key):
        """
        Построить данные для графика по истории.
        Возвращает dict для передачи во Flash.
        """
        # Отфильтровать записи для конкретного танка
        filtered = [e for e in self.history if e["vehicle_name"] == vehicle_name]

        if not filtered:
            return {
                "has_data": False,
                "message": "Нет данных для этого танка",
                "points": [],
                "labels_y": [],
                "labels_x": [],
                "y_min": 0,
                "y_max": 100,
            }

        # Фильтр по времени
        now = time.time()
        time_range = {
            "day": 86400,
            "week": 604800,
            "month": 2592000,
        }.get(filter_key, 604800)

        recent = [e for e in filtered if now - e["timestamp"] <= time_range]

        if not recent:
            return {
                "has_data": False,
                "message": f"Нет данных за {filter_key}",
                "points": [],
                "labels_y": [],
                "labels_x": [],
                "y_min": 0,
                "y_max": 100,
            }

        # Нормализовать
        first_ts = recent[0]["timestamp"]
        total_range = recent[-1]["timestamp"] - first_ts or 1

        marks = [e["mark"] for e in recent]
        y_min = max(0, min(marks) - 2)
        y_max = min(100, max(marks) + 2)

        import math
        points = []
        for e in recent:
            xr = (e["timestamp"] - first_ts) / total_range
            yr = (e["mark"] - y_min) / (y_max - y_min) if y_max > y_min else 0.5
            points.append([xr, yr, e["timestamp"], e["mark"]])

        # Метки по X (несколько дат)
        labels_x = []
        step = max(1, len(recent) // 5)
        for i in range(0, len(recent), step):
            e = recent[i]
            xr = (e["timestamp"] - first_ts) / total_range
            from datetime import datetime
            label = datetime.fromtimestamp(e["timestamp"]).strftime("%d.%m")
            labels_x.append([xr, label])

        # Метки по Y
        labels_y = []
        for p in range(0, 6):
            val = y_min + (y_max - y_min) * p / 5
            labels_y.append(round(val, 1))

        return {
            "has_data": True,
            "message": "",
            "points": points,
            "labels_y": labels_y,
            "labels_x": labels_x,
            "y_min": round(y_min, 1),
            "y_max": round(y_max, 1),
        }
