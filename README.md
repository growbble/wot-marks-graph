# WoT Marks Graph

Мод для **Lesta World of Tanks 1.42.0**, который показывает график прогресса отметок на стволе прямо в ангаре.

## Возможности

- 📊 График изменения процента отметки за день/неделю/месяц
- 🎯 Текущий процент отметки + прогноз после боя
- 🖱️ Drag & Drop для перемещения виджета
- 🔒 Блокировка позиции в бою
- 💾 Автосохранение истории боёв (data/history.json)
- 🎨 Стиль Catppuccin Mocha (тёмная тема)

## Структура мода

```
wot-marks-graph/
├── scripts/client/gui/mods/wot_marks_graph/   ← Python-часть (автозагрузка)
│   ├── __init__.py                             ← Точка входа
│   ├── mod_core.py                             ← Ядро
│   ├── config.py                               ← Конфигурация
│   ├── stat_tracker.py                         ← Статистика и история
│   └── flash_bridge.py                         ← Мост к Flash
├── flash_src/                                  ← ActionScript 3 исходники
│   └── MarkWidget.as                           ← Flash-виджет
├── data/                                       ← Данные (config.json, history.json)
└── README.md
```

## Установка

### 1. Скомпилировать Flash-виджет

Открой `flash_src/MarkWidget.as` в **Flash CS6** с **Scaleform SDK 4.2**:

1. Создай новый **Flash CS6 AIR Project** (или Scaleform CLIK project)
2. Класс документа: `MarkWidget`
3. Убедись, что в библиотеке есть Scaleform CLIK компоненты (можно импортировать)
4. Скомпилируй в `MarkWidget.swf`
5. Скопируй `MarkWidget.swf` в папку:
   ```
   res_mods/1.42.0.7246/gui/scaleform/marks_graph/MarkWidget.swf
   ```

### 2. Скопировать Python-часть

Скопируй папку `scripts` в:

```
<папка_игры>/res_mods/1.42.0.7246/
```

Должно получиться:
```
res_mods/1.42.0.7246/scripts/client/gui/mods/wot_marks_graph/__init__.py
res_mods/1.42.0.7246/scripts/client/gui/mods/wot_marks_graph/mod_core.py
...
```

### 3. Данные

Папка `data/` создаётся автоматически при первом запуске мода рядом с `res_mods/`.

## Использование

После установки и запуска игры:

- **Ангар**: виджет появляется в левом верхнем углу
- **Кнопка +** — открыть/закрыть график
- **Кнопка 📌** — зафиксировать позицию в бою
- **Перетаскивание** — зажми ЛКМ на виджете и тащи
- **История** сохраняется автоматически после каждого боя

## Компиляция Flash

Требования:
- Flash CS6
- Scaleform SDK 4.2 (с установленными CLIK компонентами)
- `scaleform.clik.controls` в classpath

Альтернативно — скомпилировать через командную строку Scaleform:
```
gfxexport MarkWidget.swf MarkWidget.as -swfversion 11
```

## Сборка из репозитория

```bash
# Клонировать
git clone https://github.com/growbble/wot-marks-graph
cd wot-marks-graph

# Папка для SWF
mkdir -p build/swf

# Скомпилируй MarkWidget.swf и положи в build/swf/
# Затем скопируй всё в res_mods:
# cp -r scripts build/swf/MarkWidget.swf data /path/to/game/res_mods/1.42.0.7246/
```

## Конфигурация

Файл `data/config.json` создаётся автоматически. Можно редактировать вручную:

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

## Лицензия

MIT
