"""
config.py — Конфигурация мода (JSON).
"""

import json
import os

DEFAULT_CONFIG = {
    "hangar_position": {"x": 250, "y": 50},
    "battle_position": {"x": 250, "y": 100},
    "battle_locked": True,
    "filter": "week",
    "style": {
        "widget_width": 220,
        "widget_height": 60,
        "graph_width": 380,
        "graph_height": 220,
        "lock_active_color": "#66BBFF",
        "lock_inactive_color": "#888888",
    },
}


class ModConfig:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, "config.json")
        self.data = {}

    def load(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.data = json.load(f)
                # Дополнить ключами по умолчанию, если чего-то не хватает
                for k, v in DEFAULT_CONFIG.items():
                    if k not in self.data:
                        self.data[k] = v
            except (json.JSONDecodeError, IOError):
                self.data = dict(DEFAULT_CONFIG)
                self.save()
        else:
            self.data = dict(DEFAULT_CONFIG)
            self.save()

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)
