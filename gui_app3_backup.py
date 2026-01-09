
import sys
import threading
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QSlider, QHBoxLayout, QStackedWidget, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QIcon

import eye_mouse_calibrated as eye_mouse

# --- Modern Stylesheet (Sidebar & Glassmorphism) ---
# [class="..."] selector syntax is required when using setProperty("class", ...)
STYLESHEET = """
QWidget {
    background-color: #11111b; /* Çok koyu arka plan */
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* Sidebar */
QFrame#Sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}

/* Sidebar Buttons */
QPushButton[class="SidebarBtn"] {
    background-color: transparent;
    color: #a6adc8;
    border: none;
    text-align: left;
    padding: 15px 20px;
    font-size: 16px;
    font-weight: bold;
    border-radius: 8px;
}
QPushButton[class="SidebarBtn"]:hover {
    background-color: #313244;
    color: #cdd6f4;
}
QPushButton[class="SidebarBtn"]:checked {
    background-color: #89b4fa;
    color: #1e1e2e;
}

/* Main Content Area */
QWidget#ContentArea {
    background-color: #11111b;
}

/* Camera Frame */
QLabel#CameraView {
    background-color: #000;
    border: 2px solid #313244;
    border-radius: 12px;
}

/* Action Buttons */
QPushButton[class="ActionBtn"] {
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 16px;
    border: none;
}
QPushButton#StartBtn { background-color: #a6e3a1; color: #1e1e2e; }
QPushButton#StartBtn:hover { background-color: #94e2d5; }

QPushButton#StopBtn { background-color: #f38ba8; color: #1e1e2e; }
QPushButton#StopBtn:hover { background-color: #eba0ac; }

/* Sliders & Labels */
QSlider::groove:horizontal {
    height: 6px;
    background: #313244;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #89b4fa;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QLabel[class="Title"] {
    font-size: 24px;
    font-weight: bold;
    color: #89b4fa;
    margin-bottom: 20px;
}
"""

class EyeMousePro(QWidget):
    # Video frame sinyali (Thread-safe güncelleme için)
    frame_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eye Mouse Ultra")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet(STYLESHEET)
        
        self.running = False
        self.thread = None

        # Ana Düzen (Sidebar + Content)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(10, 30, 10, 30)
        side_layout.setSpacing(10)

        # Logo / Başlık
        lbl_logo = QLabel("👁️ Eye Mouse")
        lbl_logo.setStyleSheet("font-size: 22px; font-weight: bold; color: #cba6f7; padding-left: 10px;")
        side_layout.addWidget(lbl_logo)
        side_layout.addSpacing(30)

        # Navigasyon Butonları
        self.btn_dashboard = self.create_sidebar_btn("🎥 Kamera / Kontrol", True)
        self.btn_settings = self.create_sidebar_btn("⚙️ Ayarlar", False)
        
        side_layout.addWidget(self.btn_dashboard)
        side_layout.addWidget(self.btn_settings)
        side_layout.addStretch()

        # Alt Bilgi
        lbl_ver = QLabel("v3.0.0 Pro")
        lbl_ver.setStyleSheet("color: #585b70; padding-left: 10px;")
        side_layout.addWidget(lbl_ver)

        # --- Content Area ---
        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        self.pages = QStackedWidget()
        
        self.pages.addWidget(self.create_dashboard_page())
        self.pages.addWidget(self.create_settings_page())
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.addWidget(self.pages)

        # Birleştir
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)

        # Sinyal Bağlantıları
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0, self.btn_dashboard))
        self.btn_settings.clicked.connect(lambda: self.switch_page(1, self.btn_settings))
        self.frame_signal.connect(self.update_camera_feed)

    def create_sidebar_btn(self, text, active):
        btn = QPushButton(text)
        # Replacing invalid addClassName with setProperty
        btn.setProperty("class", "SidebarBtn") 
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def switch_page(self, index, active_btn):
        self.pages.setCurrentIndex(index)
        # Buton durumlarını güncelle
        self.btn_dashboard.setChecked(False)
        self.btn_settings.setChecked(False)
        active_btn.setChecked(True)

    # --- Sayfa 1: Dashboard (Kamera) ---
    def create_dashboard_page(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Üst Panel (Başlık + Butonlar)
        top_bar = QHBoxLayout()
        
        lbl_title = QLabel("Canlı İzleme", objectName="Title")
        lbl_title.setProperty("class", "Title")
        
        self.btn_start = QPushButton("BAŞLAT")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setProperty("class", "ActionBtn")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_eye_mouse)

        self.btn_stop = QPushButton("DURDUR")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setProperty("class", "ActionBtn")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_eye_mouse)

        top_bar.addWidget(lbl_title)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_start)
        top_bar.addSpacing(10)
        top_bar.addWidget(self.btn_stop)

        # Kamera Alanı
        self.lbl_camera = QLabel()
        self.lbl_camera.setObjectName("CameraView")
        self.lbl_camera.setAlignment(Qt.AlignCenter)
        self.lbl_camera.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_camera.setMinimumSize(640, 480)
        self.lbl_camera.setText("Kamera Kapalı\nBaşlatmak için yukarıdaki butona basın.")
        self.lbl_camera.setStyleSheet("color: #585b70; font-size: 16px;")

        layout.addLayout(top_bar)
        layout.addSpacing(20)
        layout.addWidget(self.lbl_camera)
        
        w.setLayout(layout)
        return w

    # --- Sayfa 2: Ayarlar ---
    def create_settings_page(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop)

        lbl_title = QLabel("Hassasiyet Ayarları")
        lbl_title.setProperty("class", "Title")
        
        layout.addWidget(lbl_title)
        layout.addSpacing(30)

        self.sliders = {}
        self.add_setting(layout, "Yumuşatma (Smoothing)", 0, 100, 15, "smoothing")
        self.add_setting(layout, "Tıklama Hassasiyeti (EAR)", 10, 30, 20, "ear")
        self.add_setting(layout, "Tıklama Hızı (Cooldown)", 20, 80, 30, "cooldown")
        self.add_setting(layout, "Double Blink Aralığı", 30, 120, 60, "dbl_window")

        w.setLayout(layout)
        return w

    def add_setting(self, layout, text, min_v, max_v, init_v, key):
        lbl = QLabel(f"{text}: {init_v/100:.2f}")
        lbl.setStyleSheet("color: #a6adc8; font-weight: bold;")
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_v)
        slider.setMaximum(max_v)
        slider.setValue(init_v)
        slider.valueChanged.connect(lambda v: lbl.setText(f"{text}: {v/100:.2f}"))
        
        layout.addWidget(lbl)
        layout.addWidget(slider)
        layout.addSpacing(20)
        
        self.sliders[key] = slider

    # --- Logic ---
    def start_eye_mouse(self):
        if self.running: return

        self.running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_camera.setText("Kamera Başlatılıyor...")

        # Parametreleri al
        smoothing      = self.sliders["smoothing"].value()   / 100
        ear_th         = self.sliders["ear"].value()         / 100
        refractory     = self.sliders["cooldown"].value()    / 100
        dbl_window_sec = self.sliders["dbl_window"].value()  / 100

        def run():
            try:
                # show_preview=False çünkü biz GUI'de göstereceğiz
                eye_mouse.main(
                    smoothing=smoothing,
                    ear_click_th=ear_th,
                    click_cooldown=refractory,
                    dbl_blink_window=dbl_window_sec,
                    enable_right_click=True,
                    show_preview=False,
                    frame_callback=self.frame_signal.emit  # Frame'i sinyale gönder
                )
            except Exception as e:
                print(f"Hata: {e}")
            finally:
                self.stop_visuals()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop_eye_mouse(self):
        if self.running:
            eye_mouse.stop()
            # UI güncellemesi stop_visuals ile yapılacak
            
    def stop_visuals(self):
        self.running = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_camera.setText("Kamera Kapalı")
        # Görüntüyü temizle

    @pyqtSlot(np.ndarray)
    def update_camera_feed(self, frame):
        """Backend'den gelen frame'i ekranda göster"""
        if not self.running: return

        # Frame zaten RGB geliyor (eye_mouse_calibrated içinde çevirdik)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Ölçekle ve göster
        pixmap = QPixmap.fromImage(qt_img)
        self.lbl_camera.setPixmap(pixmap.scaled(
            self.lbl_camera.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EyeMousePro()
    win.show()
    sys.exit(app.exec_())
