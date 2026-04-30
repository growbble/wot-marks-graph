"""
utils.py — Вспомогательные функции для рендеринга.
"""

from gui import GUI


def hex_to_color(hex_str, alpha=1.0):
    """Преобразовать #RRGGBB в ARGB int для Scaleform."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a = int(alpha * 255)
    return (a << 24) | (r << 16) | (g << 8) | b


def interpolate_color(c1, c2, t):
    """Линейная интерполяция между двумя ARGB цветами."""
    t = clamp(t, 0, 1)
    a1 = (c1 >> 24) & 0xFF
    r1 = (c1 >> 16) & 0xFF
    g1 = (c1 >> 8) & 0xFF
    b1 = c1 & 0xFF

    a2 = (c2 >> 24) & 0xFF
    r2 = (c2 >> 16) & 0xFF
    g2 = (c2 >> 8) & 0xFF
    b2 = c2 & 0xFF

    a = int(a1 + (a2 - a1) * t)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return (a << 24) | (r << 16) | (g << 8) | b


def clamp(val, lo, hi):
    return max(lo, min(hi, val))
