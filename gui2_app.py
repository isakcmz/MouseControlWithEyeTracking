import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QSlider, QHBoxLayout, QTabWidget, QCheckBox, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QColor

import eye_mouse_calibrated as eye_mouse

# --- Modern Dark Theme Stylesheet ---
STYLESHEET = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #313244;
    background: #1e1e2e;
    border-radius: 8px;
    margin-top: -1px;
}
QTabBar::tab {
    background: #313244;
    color: #a6adc8;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #89b4fa;
    color: #1e1e2e;
}
QTabBar::tab:hover:!selected {
    background: #45475a;
}

/* Push Buttons */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 16px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton#StartBtn {
    background-color: #a6e3a1;
    color: #1e1e2e;
}
QPushButton#StartBtn:hover {
    background-color: #94e2d5;
}
QPushButton#StopBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#StopBtn:hover {
    background-color: #eba0ac;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #313244;
    height: 8px;
    background: #313244;
    margin: 2px 0;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #89b4fa;
    border: 1px solid #89b4fa;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: #b4befe;
}

/* Labels */
QLabel#Header {
    font-size: 24px;
    font-weight: bold;
    color: #89b4fa;
    margin-bottom: 10px;
}
QLabel#Status {
    font-size: 18px;
    font-weight: bold;
    color: #f9e2af; /* Yellow initially */
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    font-size: 15px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #585b70;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
"""

class ModernEyeMouse(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eye Mouse Pro")
        self.setGeometry(200, 200, 900, 600)
        self.setStyleSheet(STYLESHEET)
        
        # Application State
        self.running = False
        self.thread = None

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("Eye Mouse Kontrol Merkezi", objectName="Header")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), "Panel")
        self.tabs.addTab(self.create_settings_tab(), "Ayarlar")
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

    def create_dashboard_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        # Status Display
        self.status_label = QLabel("DURUM: HAZIR", objectName="Status")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Control Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        self.btn_start = QPushButton("BAŞLAT")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_eye_mouse)
        
        self.btn_stop = QPushButton("DURDUR")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_eye_mouse)
        self.btn_stop.setEnabled(False) # Initially disabled

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addStretch()

        # Info Frame
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 20px;")
        info_lay = QVBoxLayout(info_frame)
        
        info_title = QLabel("Nasıl Kullanılır?")
        info_title.setStyleSheet("font-weight: bold; color: #89b4fa; font-size: 16px;")
        
        info_text = QLabel(
            "1. 'Başlat' düğmesine basın.\n"
            "2. Göz hareketlerinizle imleci yönetin.\n"
            "3. Sol tık için SOL gözünüzü hızlıca iki kere kırpın.\n"
            "4. Sağ tık için SAĞ gözünüzü hızlıca iki kere kırpın."
        )
        info_text.setStyleSheet("color: #a6adc8; line-height: 140%;")
        
        info_lay.addWidget(info_title)
        info_lay.addWidget(info_text)

        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addLayout(btn_layout)
        layout.addSpacing(20)
        layout.addWidget(info_frame)
        layout.addStretch()
        
        w.setLayout(layout)
        return w

    def create_settings_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        # Settings Controls
        self.sliders = {}
        
        self.add_slider(layout, "Hareket Yumuşatma (Smoothing)", 0, 100, 15, "smoothing", 
                       "İmleç titremesini azaltır ama gecikme yaratabilir.")
        
        self.add_slider(layout, "EAR Eşiği (Hassasiyet)", 10, 30, 20, "ear", 
                       "Gözün kapalı sayılması için eşik değer.")
        
        self.add_slider(layout, "Tıklama Bekleme Süresi (Cooldown)", 20, 80, 30, "cooldown", 
                       "Yanlışlıkla peş peşe tıklamayı önler.")
        
        self.add_slider(layout, "Double Blink Süresi", 30, 120, 60, "dbl_window", 
                       "İki kırpma arasındaki maksimum süre.")

        # Checkboxes
        check_lay = QHBoxLayout()
        self.chk_right_click = QCheckBox("Sağ Göz Çift Kırpma -> Sağ Tık")
        self.chk_right_click.setChecked(True)
        self.chk_right_click.setCursor(Qt.PointingHandCursor)
        
        check_lay.addWidget(self.chk_right_click)
        check_lay.addStretch()

        layout.addLayout(check_lay)
        layout.addStretch()
        
        w.setLayout(layout)
        return w

    def add_slider(self, parent_layout, label_text, min_v, max_v, init_v, key, tooltip):
        container = QWidget()
        lay = QVBoxLayout()
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(5)

        header_lay = QHBoxLayout()
        lbl_title = QLabel(label_text)
        lbl_val = QLabel(f"{init_v/100:.2f}")
        lbl_val.setStyleSheet("color: #89b4fa; font-weight: bold;")
        
        header_lay.addWidget(lbl_title)
        header_lay.addStretch()
        header_lay.addWidget(lbl_val)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_v)
        slider.setMaximum(max_v)
        slider.setValue(init_v)
        slider.setToolTip(tooltip)
        slider.setCursor(Qt.PointingHandCursor)
        
        # Update function
        def update_val(val):
            lbl_val.setText(f"{val/100:.2f}")
            
        slider.valueChanged.connect(update_val)
        
        lay.addLayout(header_lay)
        lay.addWidget(slider)
        
        container.setLayout(lay)
        parent_layout.addWidget(container)
        
        self.sliders[key] = slider

    # --- Logic ---

    def start_eye_mouse(self):
        if self.running:
            return
            
        self.running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("DURUM: ÇALIŞIYOR (KAMERA AÇIK)")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;") # Green

        # Get values
        smoothing      = self.sliders["smoothing"].value()   / 100
        ear_th         = self.sliders["ear"].value()         / 100
        refractory     = self.sliders["cooldown"].value()    / 100
        dbl_window_sec = self.sliders["dbl_window"].value()  / 100
        enable_rc      = self.chk_right_click.isChecked()

        def run():
            try:
                eye_mouse.main(
                    smoothing=smoothing,
                    ear_click_th=ear_th,
                    click_cooldown=refractory,
                    enable_right_click=enable_rc,
                    dbl_blink_window=dbl_window_sec
                )
            except Exception as e:
                print(f"Error: {e}")
            finally:
                # When main loop exits
                self.stop_visuals()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop_eye_mouse(self):
        if self.running:
            eye_mouse.stop()
            # UI updates will happen in stop_visuals called by thread exiting or manual trigger
            self.stop_visuals()

    def stop_visuals(self):
        self.running = False
        # Use QTimer to safely update UI from another thread if needed, 
        # but since we are calling this from main thread (btn click) or want to ensure it runs on main:
        # We can just update if we are sure specific thread restrictions aren't strict for setText 
        # (PyQt allows signals, but simple setText usually works if not high freq).
        # Better practice: specific signals. For simplicity in this script:
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("DURUM: DURDURULDU")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f38ba8;") # Red


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernEyeMouse()
    window.show()
    sys.exit(app.exec_())
