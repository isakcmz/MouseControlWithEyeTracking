import sys, threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QSlider, QHBoxLayout, QTabWidget, QCheckBox, QSplashScreen
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
import eye_mouse_calibrated as eye_mouse

class EyeMouseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eye Mouse Control")
        self.setWindowIcon(QIcon("../assets/eye_icon.png"))
        self.setGeometry(100, 100, 900, 650)

        self.running = False
        self.thread = None

        tabs = QTabWidget()
        tabs.addTab(self.create_control_tab(), "Kontrol")
        tabs.addTab(self.create_settings_tab(), "Ayarlar")

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)

        self.set_dark_theme()

    # --- Kontrol Sekmesi ---
    def create_control_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel("Durum: Beklemede")
        self.label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        self.btn_start = QPushButton("Başlat")
        self.btn_stop = QPushButton("Durdur")

        self.btn_start.clicked.connect(self.start_eye_mouse)
        self.btn_stop.clicked.connect(self.stop_eye_mouse)

        for btn in (self.btn_start, self.btn_stop):
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px; padding: 10px;
                    background-color: #3A7CA5; color: white; border-radius: 8px;
                }
                QPushButton:hover { background-color: #28597a; }
                QPushButton:pressed { background-color: #1d3f56; }
            """)

        layout.addWidget(self.label)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        w.setLayout(layout)
        return w

    # --- Ayarlar Sekmesi ---
    def create_settings_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.slider_smoothing  = self.create_slider(0, 100, 15, "Smoothing", "Hareket yumuşatma (0.00–1.00).")
        self.slider_ear        = self.create_slider(10, 30, 20, "EAR Threshold (x0.01)", "Göz kapalı algılama eşiği.")
        self.slider_cooldown   = self.create_slider(20, 80, 30, "Refractory (s x0.01)", "Tıklamalar arası bekleme süresi.")
        self.slider_dbl_window = self.create_slider(30, 120, 60, "Double Blink Window (s x0.01)", "İki kırpma arası max süre.")

        self.chk_right_click = QCheckBox("Sağ göz 2x → Sağ tık")
        self.chk_right_click.setChecked(True)
        self.chk_right_click.setToolTip("Kapalıysa sağ gözle sağ tık yapılmaz.")
        self.chk_right_click.setStyleSheet("color: #ffffff; font-size: 14px;")

        self.chk_double_click = QCheckBox("İki göz 2x → Çift tık (kapalı)")
        self.chk_double_click.setChecked(False)
        self.chk_double_click.setToolTip("Açarsan çift göz double-blink ile çift tık atar.")
        self.chk_double_click.setStyleSheet("color: #ffffff; font-size: 14px;")

        layout.addLayout(self.slider_smoothing["layout"])
        layout.addLayout(self.slider_ear["layout"])
        layout.addLayout(self.slider_cooldown["layout"])
        layout.addLayout(self.slider_dbl_window["layout"])
        layout.addWidget(self.chk_right_click)
        layout.addWidget(self.chk_double_click)

        w.setLayout(layout)
        return w

    def create_slider(self, min_val, max_val, init_val, label_text, tooltip):
        lay = QHBoxLayout()
        label = QLabel(f"{label_text}: {init_val/100:.2f}")
        label.setToolTip(tooltip)
        label.setStyleSheet("color: #ffffff; font-size: 14px;")

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(init_val)
        slider.valueChanged.connect(lambda v: label.setText(f"{label_text}: {v/100:.2f}"))
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 8px; background: #444; border-radius: 4px; }
            QSlider::handle:horizontal {
                background: #3A7CA5; border: 1px solid #1d3f56;
                width: 18px; margin: -5px 0; border-radius: 9px;
            }
            QSlider::handle:horizontal:hover { background: #28597a; }
        """)

        lay.addWidget(label)
        lay.addWidget(slider)
        return {"layout": lay, "slider": slider, "label": label}

    def start_eye_mouse(self):
        if self.running:
            return
        self.running = True
        self.label.setText("Durum: Çalışıyor...")

        smoothing      = self.slider_smoothing["slider"].value()   / 100
        ear_th         = self.slider_ear["slider"].value()         / 100
        refractory     = self.slider_cooldown["slider"].value()    / 100
        dbl_window_sec = self.slider_dbl_window["slider"].value()  / 100

        enable_right_click = self.chk_right_click.isChecked()
        enable_double_click = self.chk_double_click.isChecked()

        def run():
            eye_mouse.main(
                smoothing=smoothing,
                ear_click_th=ear_th,
                click_cooldown=refractory,
                enable_right_click=enable_right_click,
                enable_double_click=enable_double_click,
                dbl_blink_window=dbl_window_sec
            )
            self.label.setText("Durum: Beklemede")
            self.running = False

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop_eye_mouse(self):
        if self.running:
            eye_mouse.stop()
            self.label.setText("Durum: Durduruldu")
            self.running = False

    def set_dark_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QTabWidget::pane { border: 1px solid #444; background: #2b2b2b; }
            QTabBar::tab {
                background: #3A3A3A; color: #fff; padding: 8px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background: #3A7CA5; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Splash (opsiyonel)
    splash_pix = QPixmap("../assets/eye_icon.png")
    if not splash_pix.isNull():
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.show()
        splash.showMessage(" Eye Mouse Control Yükleniyor...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        QTimer.singleShot(1000, splash.close)

    win = EyeMouseApp()
    QTimer.singleShot(1000, win.showMaximized) if 'splash' in locals() else win.showMaximized()
    sys.exit(app.exec_())
