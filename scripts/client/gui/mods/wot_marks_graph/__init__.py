# MarksGraph Mod for Lesta World of Tanks 1.42.0
# SWF-виджет прогресса отметок на стволе с интерактивным графиком
# Автозагрузка через WoT Mod System

import BigWorld

from wot_marks_graph.mod_core import MarksGraphCore

g_core = None


def init():
    """Точка входа — вызывается WoT при загрузке мода."""
    global g_core
    g_core = MarksGraphCore()
    g_core.initialize()
    BigWorld.callback(0.5, g_core.on_lobby_ready)


def fini():
    """Вызывается при выгрузке мода."""
    global g_core
    if g_core:
        g_core.destroy()
        g_core = None
