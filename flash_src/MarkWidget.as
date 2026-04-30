/**
 * MarkWidget.as — Flash-виджет отметок на стволе для Lesta WoT.
 * Стиль: Catppuccin Mocha (тёмный) с полупрозрачным фоном.
 * 
 * Компиляция: Scaleform SDK 4.2 + Flash CS6
 * 
 * Управляющие элементы:
 *   - Полоса прогресса + текущий %
 *   - Кнопка-плюс (+) для открытия/закрытия графика
 *   - Кнопка-скрепка для фиксации позиции в бою
 *   - Drag & Drop для перемещения
 *   - Нижняя полоса в ангаре (кнопка расширения)
 */

import flash.display.MovieClip;
import flash.display.Sprite;
import flash.text.TextField;
import flash.text.TextFormat;
import flash.text.TextFieldAutoSize;
import flash.events.MouseEvent;
import flash.geom.Rectangle;
import flash.external.ExternalInterface;
import scaleform.clik.events.InputEvent;
import scaleform.clik.ui.InputDetails;
import scaleform.clik.constants.InputValue;

class MarkWidget extends MovieClip {
    // Размеры
    private var _w:Number;
    private var _h:Number;
    private var _graphW:Number = 380;
    private var _graphH:Number = 220;
    
    // Компоненты
    private var _bg:Sprite;
    private var _progressBar:Sprite;
    private var _progressFill:Sprite;
    private var _labelTank:TextField;
    private var _labelPercent:TextField;
    private var _labelChange:TextField;
    private var _btnPlus:Sprite;
    private var _btnPin:Sprite;
    private var _graphPanel:Sprite;
    private var _graphCanvas:Sprite;
    
    // Состояние
    private var _isExpanded:Boolean = false;
    private var _isLocked:Boolean = false;
    private var _isBattle:Boolean = false;
    private var _markPercent:Number = 0;
    private var _markChange:Number = 0;
    private var _tankName:String = "";
    
    // Цвета Catppuccin Mocha
    private var C_BG:Number = 0x1E1E2E;
    private var C_SURFACE:Number = 0x313244;
    private var C_OVERLAY:Number = 0x45475A;
    private var C_TEXT:Number = 0xCDD6F4;
    private var C_SUBTEXT:Number = 0xA6ADC8;
    private var C_BLUE:Number = 0x89B4FA;
    private var C_GREEN:Number = 0xA6E3A1;
    private var C_RED:Number = 0xF38BA8;
    private var C_YELLOW:Number = 0xF9E2AF;
    
    // Scaleform callback регистрация
    private var _initialized:Boolean = false;
    
    public function MarkWidget() {
        super();
        addFrameScript(0, init);
    }
    
    private function init():void {
        if (_initialized) return;
        _initialized = true;
        
        _w = 220;
        _h = 60;
        
        createBackground();
        createProgressBar();
        createLabels();
        createButtons();
        createGraphPanel();
        setupDragging();
        registerCallbacks();
        
        // Начальное состояние
        updateDisplay();
    }
    
    // === Основной фон ===
    private function createBackground():void {
        _bg = new Sprite();
        _bg.graphics.beginFill(C_SURFACE, 0.85);
        _bg.graphics.drawRoundRect(0, 0, _w, _h, 8);
        _bg.graphics.endFill();
        // Рамка
        _bg.graphics.lineStyle(1, C_OVERLAY, 0.6);
        _bg.graphics.drawRoundRect(0, 0, _w, _h, 8);
        addChild(_bg);
    }
    
    // === Прогресс-бар ===
    private function createProgressBar():void {
        var barY:Number = 30;
        var barX:Number = 10;
        var barW:Number = _w - 70;
        var barH:Number = 8;
        
        // Трек
        _progressBar = new Sprite();
        _progressBar.graphics.beginFill(C_OVERLAY, 0.5);
        _progressBar.graphics.drawRoundRect(0, 0, barW, barH, 4);
        _progressBar.graphics.endFill();
        _progressBar.x = barX;
        _progressBar.y = barY;
        addChild(_progressBar);
        
        // Заполнение
        _progressFill = new Sprite();
        _progressFill.graphics.beginFill(C_BLUE, 0.9);
        _progressFill.graphics.drawRoundRect(0, 0, barW * 0.5, barH, 4);
        _progressFill.graphics.endFill();
        _progressFill.x = barX;
        _progressFill.y = barY;
        addChild(_progressFill);
    }
    
    // === Текстовые метки ===
    private function createLabels():void {
        var fmtTank:TextFormat = new TextFormat();
        fmtTank.font = "$TextFont";
        fmtTank.size = 11;
        fmtTank.color = C_TEXT;
        fmtTank.bold = true;
        
        var fmtPercent:TextFormat = new TextFormat();
        fmtPercent.font = "$TextFont";
        fmtPercent.size = 11;
        fmtPercent.color = C_BLUE;
        fmtPercent.bold = true;
        
        var fmtChange:TextFormat = new TextFormat();
        fmtChange.font = "$TextFont";
        fmtChange.size = 10;
        fmtChange.color = C_SUBTEXT;
        
        // Имя танка
        _labelTank = createTextField(fmtTank);
        _labelTank.x = 10;
        _labelTank.y = 6;
        _labelTank.text = "Загрузка...";
        addChild(_labelTank);
        
        // Процент
        _labelPercent = createTextField(fmtPercent);
        _labelPercent.x = 10;
        _labelPercent.y = 44;
        _labelPercent.text = "95.0%";
        addChild(_labelPercent);
        
        // Изменение
        _labelChange = createTextField(fmtChange);
        _labelChange.x = 60;
        _labelChange.y = 45;
        _labelChange.text = "";
        addChild(_labelChange);
    }
    
    private function createTextField(fmt:TextFormat):TextField {
        var tf:TextField = new TextField();
        tf.defaultTextFormat = fmt;
        tf.autoSize = TextFieldAutoSize.LEFT;
        tf.selectable = false;
        tf.mouseEnabled = false;
        return tf;
    }
    
    // === Кнопки ===
    private function createButtons():void {
        // Кнопка "+" (открыть/закрыть график)
        _btnPlus = new Sprite();
        _btnPlus.graphics.beginFill(C_OVERLAY, 0.8);
        _btnPlus.graphics.drawCircle(0, 0, 10);
        _btnPlus.graphics.endFill();
        _btnPlus.x = _w - 16;
        _btnPlus.y = 20;
        // Текст "+"
        var plusTf:TextField = createTextField(new TextFormat("$TextFont", 14, C_TEXT, true));
        plusTf.text = "+";
        plusTf.x = -6;
        plusTf.y = -10;
        _btnPlus.addChild(plusTf);
        _btnPlus.buttonMode = true;
        _btnPlus.addEventListener(MouseEvent.CLICK, onPlusClick);
        addChild(_btnPlus);
        
        // Кнопка скрепки (фиксация)
        _btnPin = new Sprite();
        _btnPin.graphics.beginFill(C_OVERLAY, 0.8);
        _btnPin.graphics.drawCircle(0, 0, 10);
        _btnPin.graphics.endFill();
        _btnPin.x = _w - 40;
        _btnPin.y = 20;
        var pinTf:TextField = createTextField(new TextFormat("$TextFont", 12, C_SUBTEXT));
        pinTf.text = "📌";
        pinTf.x = -7;
        pinTf.y = -9;
        _btnPin.addChild(pinTf);
        _btnPin.buttonMode = true;
        _btnPin.addEventListener(MouseEvent.CLICK, onPinClick);
        addChild(_btnPin);
    }
    
    // === Панель графика ===
    private function createGraphPanel():void {
        _graphPanel = new Sprite();
        _graphPanel.graphics.beginFill(C_BG, 0.9);
        _graphPanel.graphics.drawRoundRect(0, 0, _graphW, _graphH, 8);
        _graphPanel.graphics.endFill();
        _graphPanel.graphics.lineStyle(1, C_OVERLAY);
        _graphPanel.graphics.drawRoundRect(0, 0, _graphW, _graphH, 8);
        _graphPanel.x = 0;
        _graphPanel.y = _h + 4;
        _graphPanel.visible = false;
        addChild(_graphPanel);
        
        // Canvas для отрисовки графика
        _graphCanvas = new Sprite();
        _graphCanvas.x = 20;
        _graphCanvas.y = 20;
        _graphPanel.addChild(_graphCanvas);
    }
    
    // === Drag & Drop ===
    private function setupDragging():void {
        this.addEventListener(MouseEvent.MOUSE_DOWN, onDragStart);
        this.addEventListener(MouseEvent.MOUSE_UP, onDragEnd);
    }
    
    private function onDragStart(e:MouseEvent):void {
        if (_isBattle && _isLocked) return;
        this.startDrag(false, new Rectangle(0, 0, 1920 - _w, 1080 - _h));
    }
    
    private function onDragEnd(e:MouseEvent):void {
        if (_isBattle && _isLocked) return;
        this.stopDrag();
        notifyDragEnded(this.x, this.y);
    }
    
    // === Методы, вызываемые из Python ===
    
    public function setTankInfo(tankName:String):void {
        _tankName = tankName;
        _labelTank.text = tankName;
    }
    
    public function setMarkPercent(percent:Number, change:Number):void {
        _markPercent = percent;
        _markChange = change;
        updateDisplay();
    }
    
    public function setBattleMode(battle:Boolean):void {
        _isBattle = battle;
        // В бою скрываем кнопку графика
        _btnPlus.visible = !battle;
        if (battle && _isExpanded) {
            toggleGraph();
        }
    }
    
    public function setLockIcon(locked:Boolean):void {
        _isLocked = locked;
        var color:Number = locked ? C_GREEN : C_SUBTEXT;
        var tf:TextField = _btnPin.getChildAt(0) as TextField;
        if (tf) tf.textColor = color;
    }
    
    public function disableDrag():void {
        _isLocked = true;
    }
    
    public function enableDrag():void {
        _isLocked = false;
    }
    
    public function toggleGraph():Boolean {
        _isExpanded = !_isExpanded;
        _graphPanel.visible = _isExpanded;
        // Анимируем поворот плюсика
        var tf:TextField = _btnPlus.getChildAt(0) as TextField;
        if (tf) tf.text = _isExpanded ? "−" : "+";
        return _isExpanded;
    }
    
    public function renderGraph(jsonData:String):void {
        _graphCanvas.graphics.clear();
        
        if (jsonData == null || jsonData == "") return;
        
        try {
            var data:Object = JSON.parse(jsonData);
            if (!data.has_data) return;
            
            var cw:Number = _graphW - 60;
            var ch:Number = _graphH - 60;
            var points:Array = data.points;
            
            if (points.length < 2) return;
            
            // Отрисовать линии
            _graphCanvas.graphics.lineStyle(2, C_BLUE, 0.9);
            _graphCanvas.graphics.moveTo(points[0][0] * cw, ch - points[0][1] * ch);
            
            for (var i:Number = 1; i < points.length; i++) {
                var px:Number = points[i][0] * cw;
                var py:Number = ch - points[i][1] * ch;
                _graphCanvas.graphics.lineTo(px, py);
            }
            
            // Нарисовать точки
            for (i = 0; i < points.length; i++) {
                px = points[i][0] * cw;
                py = ch - points[i][1] * ch;
                _graphCanvas.graphics.lineStyle(0);
                _graphCanvas.graphics.beginFill(C_YELLOW, 0.9);
                _graphCanvas.graphics.drawCircle(px, py, 3);
                _graphCanvas.graphics.endFill();
            }
            
            // Y-метки
            var fmt:TextFormat = new TextFormat("$TextFont", 8, C_SUBTEXT);
            var labelsY:Array = data.labels_y;
            for (i = 0; i < labelsY.length; i++) {
                var ly:Number = ch - (labelsY[i] - data.y_min) / (data.y_max - data.y_min) * ch;
                // Линия сетки
                _graphCanvas.graphics.lineStyle(1, C_OVERLAY, 0.3);
                _graphCanvas.graphics.moveTo(0, ly);
                _graphCanvas.graphics.lineTo(cw, ly);
                // Текст
                if (i % 2 == 0) {
                    var tf:TextField = createTextField(fmt);
                    tf.text = labelsY[i] + "%";
                    tf.x = -35;
                    tf.y = ly - 6;
                    _graphCanvas.addChild(tf);
                }
            }
            
        } catch (e:Error) {
            // Ошибка парсинга — игнорируем
        }
    }
    
    // === Обновление дисплея ===
    private function updateDisplay():void {
        var pct:Number = Math.max(0, Math.min(100, _markPercent));
        var barW:Number = _w - 70;
        var fillW:Number = barW * (pct / 100);
        
        _progressFill.graphics.clear();
        var color:Number = C_BLUE;
        if (pct >= 95) color = C_GREEN;
        else if (pct <= 65) color = C_RED;
        
        _progressFill.graphics.beginFill(color, 0.9);
        _progressFill.graphics.drawRoundRect(0, 0, fillW, 8, 4);
        _progressFill.graphics.endFill();
        
        _labelPercent.text = pct.toFixed(1) + "%";
        
        if (_markChange != 0) {
            var sign:String = _markChange > 0 ? "+" : "";
            var changeColor:Number = _markChange > 0 ? C_GREEN : C_RED;
            var fmtCh:TextFormat = _labelChange.getTextFormat();
            fmtCh.color = changeColor;
            _labelChange.setTextFormat(fmtCh);
            _labelChange.text = sign + _markChange.toFixed(2) + "%";
        } else {
            _labelChange.text = "";
        }
    }
    
    // === Обработчики кликов ===
    private function onPlusClick(e:MouseEvent):void {
        var expanded:Boolean = toggleGraph();
        notifyPlusClicked();
    }
    
    private function onPinClick(e:MouseEvent):void {
        notifyPinClicked();
    }
    
    // === Callback-регистрация для Python ===
    private function registerCallbacks():void {
        // Scaleform ExternalInterface
        ExternalInterface.addCallback("setTankInfo", null, setTankInfo);
        ExternalInterface.addCallback("setMarkPercent", null, setMarkPercent);
        ExternalInterface.addCallback("setBattleMode", null, setBattleMode);
        ExternalInterface.addCallback("setLockIcon", null, setLockIcon);
        ExternalInterface.addCallback("disableDrag", null, disableDrag);
        ExternalInterface.addCallback("enableDrag", null, enableDrag);
        ExternalInterface.addCallback("toggleGraph", null, toggleGraph);
        ExternalInterface.addCallback("renderGraph", null, renderGraph);
    }
    
    // === AS→Python уведомления ===
    private function notifyPlusClicked():void {
        ExternalInterface.call("onPlusClicked");
    }
    
    private function notifyPinClicked():void {
        ExternalInterface.call("onPinClicked");
    }
    
    private function notifyDragEnded(x:Number, y:Number):void {
        ExternalInterface.call("onDragEnded", x, y);
    }
    
    private function notifyFilterChanged(filterKey:String):void {
        ExternalInterface.call("onFilterChanged", filterKey);
    }
}
