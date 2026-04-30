# WoT Marks Graph

Мод для **Lesta World of Tanks 1.42.0**, который показывает график прогресса отметок на стволе прямо в ангаре.

**Не требует компиляции Flash** — весь UI рисуется через BigWorld GUI из Python.

## Возможности

- 📊 График изменения процента отметки за день/неделю/месяц
- 🎯 Текущий процент отметки + изменение после боя
- 🖱️ Drag & Drop для перемещения виджета
- 🔒 Блокировка позиции в бою
- 💾 Автосохранение истории боёв (data/history.json)
- 🎨 Стиль Catppuccin Mocha (тёмная тема)

## Структура мода

```
wot-marks-graph/
├── scripts/client/gui/mods/wot_marks_graph/   ← Python-часть (автозагрузка)
│   ├── __init__.py                             ← Точка входа (init/fini)
│   ├── mod_core.py                             ← Ядро мода
│   ├── widget_renderer.py                      ← Рисование виджета через BigWorld GUI
│   ├── stat_tracker.py                         ← Статистика и история боёв
│   ├── config.py                               ← Конфигурация (data/config.json)
│   ├── vehicle_hook.py                         ← Получение текущего танка
│   └── utils.py                                ← Вспомогательные функции
├── data/                                       ← Данные (создаётся автоматически)
│   ├── config.json
│   └── history.json
└── README.md
```

## Установка

Просто скопируй папку `scripts/` в:

```
<папка_игры>/res_mods/1.42.0.7246/
```

Должно получиться:
```
res_mods/1.42.0.7246/scripts/client/gui/mods/wot_marks_graph/__init__.py
res_mods/1.42.0.7246/scripts/client/gui/mods/wot_marks_graph/mod_core.py
... (все файлы из scripts/)
```

Данные сохраняются в `data/` (папка создаётся автоматически при первом запуске).

## Использование

После установки и запуска игры:

- **Ангар**: виджет появляется в левом верхнем углу
- **Кнопка +** (или ─) — открыть/закрыть график
- **Кнопка 📌** — зафиксировать позицию в бою (зелёная = заблокировано)
- **Перетаскивание** — зажми и тащи виджет мышью
- **История** сохраняется автоматически после каждого боя

## Конфигурация

Файл `data/config.json` создаётся автоматически:

```json
{
  "hangar_position": {"x": 250, "y": 50},
  "battle_position": {"x": 250, "y": 100},
  "battle_locked": true,
  "filter": "week",
  "style": {
    "widget_width": 220,
    "widget_height": 60,
    "graph_width": 380,
    "graph_height": 220
  }
}
```

## Сборка из репозитория

```bash
git clone https://github.com/growbble/wot-marks-graph
cd wot-marks-graph
# Скопировать scripts/ в res_mods/ — и готово
cp -r scripts /path/to/game/res_mods/1.42.0.7246/
```

## Особенности

- 🚫 **Без Flash/SWF** — весь рендеринг через BigWorld GUI
- 🐍 **Чистый Python** — никаких компиляторов, просто копирование
- 📦 **Один файл мода** — никаких .wotmod архивов

## Лицензия

MIT
