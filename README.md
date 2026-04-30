# wot-marks-graph

Виджет прогресса отметок на стволе для **Lesta World of Tanks 1.42.0** с интерактивным графиком.

## Особенности

- 📊 **Интерактивный график** изменения процента отметки по боям
- 🎨 **Catppuccin Mocha** — тёмная тема, не режет глаза
- 🖱️ **Drag & Drop** — перемещение виджета
- 📌 **Pin** — блокировка от случайного перетаскивания
- ✅ SWF-виджет (Scaleform GFx) — плавно и красиво
- 💾 Автосохранение позиции и настроек

## Установка
1. Скачай последний [релиз](https://github.com/growbble/wot-marks-graph/releases)
2. Распакуй в `World_of_Tanks_LESTA/res_mods/1.42.0/`
3. Запусти игру — виджет появится в ангаре

## Установка из исходников (сборка SWF)
Если хочешь пересобрать `MarkWidget.swf`:

**Требования:** Apache Flex SDK 4.16.1+ с playerglobal.swc для Flash Player 11

```bash
mxmlc \
  +configname=flash \
  -target-player=11.0 \
  -swf-version=16 \
  -output=MarkWidget.swf \
  flash_src/MarkWidget.as
```

## Структура
```
wot-marks-graph/
├── flash_src/
│   └── MarkWidget.as          # AS3 исходник виджета
├── build/
│   └── MarkWidget.swf         # скомпилированный SWF
└── scripts/client/gui/mods/wot_marks_graph/
    ├── __init__.py             # точка входа
    ├── mod_core.py             # ядро мода
    ├── flash_bridge.py         # мост Python ↔ Scaleform
    ├── config.py               # настройки (JSON)
    ├── stat_tracker.py         # статистика машин
    ├── utils.py                # утилиты
    └── vehicle_hook.py         # получение текущего танка
```

## Цвета отметок
| %      | Цвет      |
|--------|-----------|
| < 65%  | Серый     |
| 65-85% | Синий      |
| 85-95% | Оранжевый |
| 95%+   | Золото    |

## Сборка SWF для Lesta WoT
Мод использует SWF-виджет через Scaleform GFx (встроен в Lesta WoT).
Компиляция: Apache Flex SDK 4.16.1, target Flash Player 11, SWF version 16.
Playerglobal.swc: https://github.com/nexussays/playerglobal

## Лицензия
MIT
