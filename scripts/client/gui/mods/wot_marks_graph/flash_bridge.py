"""
flash_bridge.py — Мост между Python и Flash через Scaleform GFx.

Загружает SWF, управляет виджетом, передаёт колбэки.
"""

import GUI
import Math


class FlashBridge:
    def __init__(self):
        self._widget_mc = None
        self._graph_mc = None

    def load_widget(self, swf_path, linkage_name, x, y, w, h, callback=None):
        """
        Загрузить SWF и создать экземпляр мувиклипа.
        swf_path: путь к SWF относительно res_mods/версия/gui/scaleform/
        """
        try:
            # В Lesta WoT GUI.WGFlashComponent загружает SWF через Scaleform
            movie = GUI.WGFlashComponent()
            movie.source = swf_path
            movie.size = (w, h)
            movie.position = (x, y)
            movie.focus = True
            movie.moveFocus = True

            # Добавить на сцену
            GUI.addRoot(movie)

            self._widget_mc = movie

            if callback:
                callback(movie)

            print(f"[MarksGraph] Виджет загружен: {swf_path}")
        except Exception as e:
            print(f"[MarksGraph] Ошибка загрузки SWF {swf_path}: {e}")

    def destroy(self):
        if self._widget_mc:
            try:
                GUI.delRoot(self._widget_mc)
            except Exception:
                pass
            self._widget_mc = None
