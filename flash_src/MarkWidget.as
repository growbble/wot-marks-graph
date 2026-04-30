/**
 * MarkWidget.as — Flash-виджет отметок на стволе для Lesta WoT.
 * Стиль: Catppuccin Mocha (тёмный).
 * 
 * Компилируется через Apache Flex SDK 4.16.1 (без Scaleform CLIK).
 */

package {
    import flash.display.MovieClip;
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.events.MouseEvent;
    import flash.geom.Rectangle;
    import flash.external.ExternalInterface;
    import flash.geom.Point;

    public class MarkWidget extends MovieClip {
        // Размеры
        private var _w:Number = 220;
        private var _h:Number = 60;
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
        
        public function MarkWidget() {
            super();
            init();
        }
        
        private function init():void {
            createBackground();
            createProgressBar();
            createLabels();
            createButtons();
            createGraphPanel();
            setupDragging();
            registerCallbacks();
            updateDisplay();
        }
        
        private function createBackground():void {
            _bg = new Sprite();
            _bg.graphics.beginFill(C_SURFACE, 0.85);
            _bg.graphics.drawRoundRect(0, 0, _w, _h, 8);
            _bg.graphics.endFill();
            _bg.graphics.lineStyle(1, C_OVERLAY, 0.6);
            _bg.graphics.drawRoundRect(0, 0, _w, _h, 8);
            addChild(_bg);
        }
        
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
            _progressFill.x = barX;
            _progressFill.y = barY;
            addChild(_progressFill);
        }
        
        private function createLabels():void {
            _labelTank = makeTextField(11, C_TEXT, true);
            _labelTank.x = 10; _labelTank.y = 6;
            _labelTank.text = "Загрузка...";
            addChild(_labelTank);
            
            _labelPercent = makeTextField(11, C_BLUE, true);
            _labelPercent.x = 10; _labelPercent.y = 44;
            _labelPercent.text = "95.0%";
            addChild(_labelPercent);
            
            _labelChange = makeTextField(10, C_SUBTEXT, false);
            _labelChange.x = 60; _labelChange.y = 45;
            addChild(_labelChange);
        }
        
        private function makeTextField(size:Number, color:Number, bold:Boolean):TextField {
            var tf:TextField = new TextField();
            var fmt:TextFormat = new TextFormat();
            fmt.font = "$TextFont";
            fmt.size = size;
            fmt.color = color;
            fmt.bold = bold;
            tf.defaultTextFormat = fmt;
            tf.autoSize = TextFieldAutoSize.LEFT;
            tf.selectable = false;
            tf.mouseEnabled = false;
            return tf;
        }
        
        private function createButtons():void {
            _btnPlus = makeCircleButton(_w - 16, 20, "+", 14, C_TEXT);
            _btnPlus.addEventListener(MouseEvent.CLICK, onPlusClick);
            addChild(_btnPlus);
            
            _btnPin = makeCircleButton(_w - 40, 20, "📌", 12, C_SUBTEXT);
            _btnPin.addEventListener(MouseEvent.CLICK, onPinClick);
            addChild(_btnPin);
        }
        
        private function makeCircleButton(cx:Number, cy:Number, label:String, fontSize:Number, color:Number):Sprite {
            var btn:Sprite = new Sprite();
            btn.graphics.beginFill(C_OVERLAY, 0.8);
            btn.graphics.drawCircle(0, 0, 10);
            btn.graphics.endFill();
            btn.x = cx; btn.y = cy;
            
            var tf:TextField = makeTextField(fontSize, color, true);
            tf.text = label;
            tf.x = -tf.textWidth / 2;
            tf.y = -tf.textHeight / 2 + 1;
            btn.addChild(tf);
            btn.buttonMode = true;
            return btn;
        }
        
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
            
            _graphCanvas = new Sprite();
            _graphCanvas.x = 20;
            _graphCanvas.y = 20;
            _graphPanel.addChild(_graphCanvas);
        }
        
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
        
        // === Вызывается из Python ===
        
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
            _btnPlus.visible = !battle;
            if (battle && _isExpanded) toggleGraph();
        }
        
        public function setLockIcon(locked:Boolean):void {
            _isLocked = locked;
            var color:Number = locked ? C_GREEN : C_SUBTEXT;
            setButtonTextColor(_btnPin, color);
        }
        
        public function disableDrag():void { _isLocked = true; }
        public function enableDrag():void { _isLocked = false; }
        
        public function toggleGraph():Boolean {
            _isExpanded = !_isExpanded;
            _graphPanel.visible = _isExpanded;
            setButtonText(_btnPlus, _isExpanded ? "−" : "+");
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
                
                // Линия
                _graphCanvas.graphics.lineStyle(2, C_BLUE, 0.9);
                _graphCanvas.graphics.moveTo(points[0][0] * cw, ch - points[0][1] * ch);
                for (var i:Number = 1; i < points.length; i++) {
                    var px:Number = points[i][0] * cw;
                    var py:Number = ch - points[i][1] * ch;
                    _graphCanvas.graphics.lineTo(px, py);
                }
                
                // Точки
                for (i = 0; i < points.length; i++) {
                    px = points[i][0] * cw;
                    py = ch - points[i][1] * ch;
                    _graphCanvas.graphics.lineStyle(0);
                    _graphCanvas.graphics.beginFill(C_YELLOW, 0.9);
                    _graphCanvas.graphics.drawCircle(px, py, 3);
                    _graphCanvas.graphics.endFill();
                }
                
                // Y-сетка
                var labelsY:Array = data.labels_y;
                for (i = 0; i < labelsY.length; i++) {
                    var ly:Number = ch - (labelsY[i] - data.y_min) / (data.y_max - data.y_min) * ch;
                    _graphCanvas.graphics.lineStyle(1, C_OVERLAY, 0.3);
                    _graphCanvas.graphics.moveTo(0, ly);
                    _graphCanvas.graphics.lineTo(cw, ly);
                }
            } catch (e:Error) {}
        }
        
        private function setButtonText(btn:Sprite, txt:String):void {
            var tf:TextField = btn.getChildAt(0) as TextField;
            if (tf) { tf.text = txt; tf.x = -tf.textWidth / 2; }
        }
        
        private function setButtonTextColor(btn:Sprite, color:Number):void {
            var tf:TextField = btn.getChildAt(0) as TextField;
            if (tf) tf.textColor = color;
        }
        
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
                var fmt:TextFormat = _labelChange.getTextFormat();
                fmt.color = changeColor;
                _labelChange.setTextFormat(fmt);
                _labelChange.text = sign + _markChange.toFixed(2) + "%";
            } else {
                _labelChange.text = "";
            }
        }
        
        private function onPlusClick(e:MouseEvent):void {
            toggleGraph();
            notifyPlusClicked();
        }
        
        private function onPinClick(e:MouseEvent):void {
            notifyPinClicked();
        }
        
        private function registerCallbacks():void {
            ExternalInterface.addCallback("setTankInfo", setTankInfo);
            ExternalInterface.addCallback("setMarkPercent", setMarkPercent);
            ExternalInterface.addCallback("setBattleMode", setBattleMode);
            ExternalInterface.addCallback("setLockIcon", setLockIcon);
            ExternalInterface.addCallback("disableDrag", disableDrag);
            ExternalInterface.addCallback("enableDrag", enableDrag);
            ExternalInterface.addCallback("toggleGraph", toggleGraph);
            ExternalInterface.addCallback("renderGraph", renderGraph);
        }
        
        private function notifyPlusClicked():void {
            ExternalInterface.call("onPlusClicked");
        }
        
        private function notifyPinClicked():void {
            ExternalInterface.call("onPinClicked");
        }
        
        private function notifyDragEnded(x:Number, y:Number):void {
            ExternalInterface.call("onDragEnded", x, y);
        }
    }
}
