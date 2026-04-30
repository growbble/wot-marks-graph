# flash_bridge.py — мост Python <-> Flash (Scaleform GFx)
# Загружает SWF-виджет и передаёт данные через ExternalInterface

import json
import logging
from gui.shared import g_eventBus, events
from gui.Scaleform.daapi.view.meta.Meta import Meta as FlashMeta
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule

from .config import MOD_CONFIG

_logger = logging.getLogger("WOT_MG_FB")
_logger.setLevel(logging.DEBUG)

# ============================================================================
# Путь к SWF относительно res_mods/<version>/ или встроенной папки
# Некоторые лаунчеры грузят SWF из gui/flash/
# ============================================================================
SWF_PATH = "wot_marks_graph/MarkWidget.swf"

class MarksGraphBridge(BaseDAAPIModule):
    """
    Scaleform-мост: загружает AS3-виджет MarkWidget.swf
    и общается с ним через AS_Signal / ExternalInterface.
    
    При инициализации говорит AS3-виджету имя танка и текущий %.
    При обновлении статистики отправляет новые данные.
    Получает от AS3 события: перетаскивание / нажатия кнопок.
    """

    def __init__(self):
        super().__init__()
        self._widgetLoaded = False
        self._ctx = {}
        _logger.info("Bridge created")

    def _populate(self):
        """Вызывается AVMP1-рантаймом когда SWF загружен"""
        super()._populate()
        self._widgetLoaded = True
        _logger.info("Widget loaded, populating data")

        if self._ctx.get("tankName"):
            self._callAS("onTankChanged", self._ctx["tankName"])
        if self._ctx.get("percent") is not None:
            self._callAS("onDataUpdate", json.dumps({
                "percent": self._ctx["percent"],
                "markColor": self._ctx.get("markColor", 0x888888),
                "targets": [65, 85, 95],
                "changeToday": self._ctx.get("changeToday", 0.0),
                "markLabel": self._ctx.get("markLabel", ""),
            }))

    def _dispose(self):
        self._widgetLoaded = False
        super()._dispose()

    def setBattleData(self, vehicleName, vehicleType=""):
        self._ctx["tankName"] = vehicleName
        if self._widgetLoaded:
            self._callAS("onTankChanged", vehicleName)

    def updateStats(self, percent, markColor, changeToday, markLabel, points=None):
        self._ctx.update({
            "percent": percent,
            "markColor": markColor,
            "changeToday": changeToday,
            "markLabel": markLabel,
        })
        if self._widgetLoaded:
            data = {
                "percent": percent,
                "markColor": markColor,
                "targets": [65, 85, 95],
                "changeToday": changeToday,
                "markLabel": markLabel,
            }
            if points:
                data["points"] = points
            self._callAS("onDataUpdate", json.dumps(data))

    # --- Сигналы из AS3 ---

    def onDragged(self, xPos, yPos):
        """Виджет сообщил новую позицию после перетаскивания"""
        _logger.info(f"Widget dragged to ({xPos}, {yPos})")
        self._ctx["posX"] = xPos
        self._ctx["posY"] = yPos
        # Можно сохранить в конфиг

    def onToggleGraph(self, expanded):
        """Виджет развернул/свернул график"""
        _logger.info(f"Graph expanded={expanded}")

    def onPinChanged(self, pinned):
        pass

    # --- Вспомогательное ---

    def _callAS(self, method, *args):
        if not self._widgetLoaded:
            return
        try:
            self.as_call(method, *args)
        except Exception as ex:
            _logger.error(f"AS call failed: {ex}")


# === Глобальный экземпляр ===
_bridge = None


def initBridge(appNS=None):
    global _bridge
    if _bridge is None:
        _bridge = MarksGraphBridge()
    return _bridge


def getBridge():
    return _bridge


def fini():
    global _bridge
    if _bridge is not None:
        _bridge._dispose()
        _bridge = None
