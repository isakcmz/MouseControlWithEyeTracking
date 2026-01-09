
import sys
import threading
import cv2
import numpy as np
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QSlider, QHBoxLayout, QStackedWidget, QFrame, QSizePolicy,
    QGridLayout, QMainWindow, QShortcut
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QPoint, QRect, QSize
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QCursor, QPainter, QColor

import eye_mouse_calibrated as eye_mouse

# ==========================================
#  MAIN APP STYLES (SIDEBAR ETC)
# ==========================================
MAIN_STYLESHEET = """
QWidget {
    background-color: #11111b; /* Main app bg */
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

/* Sliders */
QSlider::groove:horizontal { height: 6px; background: #313244; border-radius: 3px; }
QSlider::handle:horizontal { background: #89b4fa; width: 16px; margin: -5px 0; border-radius: 8px; }

QLabel[class="Title"] { font-size: 24px; font-weight: bold; color: #89b4fa; margin-bottom: 20px; }
"""

# ==========================================
#  ORIGINAL KEYBOARD DATA & CLASSES
# ==========================================

KEYBOARD_ROWS = [
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'Ğ', 'Ü'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ş', 'İ'],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Ö', 'Ç']
]

NUMBER_GRID = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['.', '0', ',']
]

TURKISH_WORDS = {
    'M':  ['Merhaba', 'Müsait', 'Mutlu', 'Mümkün', 'Mesaj', 'Merak'],
    'ME': ['Merhaba', 'Mesaj', 'Merak', 'Meşgul', 'Merkez'],
    'MER': ['Merhaba', 'Merkez', 'Mersi'],
    'G':  ['Günaydın', 'Görüşürüz', 'Güzel', 'Gerek'],
    'GU': ['Günaydın', 'Güzel', 'Güle'],
    'Y':  ['Yardım', 'Yarın', 'Yemek', 'Yeter'],
    'YA': ['Yardım', 'Yarın', 'Yavaş'],
    'T':  ['Teşekkür', 'Tamam', 'Tabii', 'Telefon'],
    'TE': ['Teşekkür', 'Tekrar', 'Telefon'],
    'N':  ['Nasılsın', 'Nasıl', 'Ne', 'Nerede'],
    'NA': ['Nasılsın', 'Nasıl'],
    'NAS': ['Nasılsın', 'Nasıl'],
    'S':  ['Selam', 'Sağol', 'Sonra', 'Su'],
    'SE': ['Selam', 'Seni', 'Seviyorum'],
    'E':  ['Evet', 'Emin', 'Eğer'],
    'H':  ['Hayır', 'Hadi', 'Hasta'],
    'D':  ['Doktor', 'Dur', 'Dinlen'],
    'L':  ['Lütfen', 'Lazım'],
    'A':  ['Anladım', 'Acil', 'Ağrı'],
    'AN': ['Anladım', 'Anne', 'Anlamadım'],
}

PHRASE_CATEGORIES = [
    ("Günlük", [
        "Merhaba", "Günaydın", "İyi akşamlar", "Teşekkür ederim",
        "Lütfen", "Evet", "Hayır", "Anlamadım", "Tekrar eder misiniz?"
    ]),
    ("İhtiyaç", [
        "Su istiyorum", "Yemek istiyorum", "Tuvalete gitmem gerekiyor",
        "Yardım eder misiniz?", "Üşüyorum", "Sıcak", "Yastık isterim", "Battaniye isterim"
    ]),
    ("Sağlık", [
        "Ağrım var", "İyi hissetmiyorum", "İyiyim",
        "Doktor çağırır mısınız?", "Hemşire çağırır mısınız?",
        "İlaca ihtiyacım var", "Başım dönüyor", "Nefes alamıyorum"
    ]),
    ("Konfor", [
        "Işığı açar mısınız?", "Işığı kapatır mısınız?",
        "TV açar mısınız?", "TV kapatır mısınız?",
        "Müzik istiyorum", "Pencereyi açar mısınız?", "Pencereyi kapatır mısınız?"
    ])
]

class GazeButton(QPushButton):
    def __init__(self, text="", dwell_ms=1200, repeat=False, parent=None):
        super().__init__(text, parent)
        self.dwell_ms = dwell_ms
        self.repeat = repeat
        self.hovered = False
        self.progress = 0
        self.fired_while_hovered = False
        self._alive = True
        self.dwell_timer = QTimer(self)
        self.dwell_timer.timeout.connect(self._tick)
        self.repeat_timer = QTimer(self)
        self.repeat_timer.timeout.connect(self._repeat_click)
        self.setMouseTracking(True)
    
    def cleanup(self):
        self._alive = False
        try:
            self.dwell_timer.stop()
            self.repeat_timer.stop()
        except: pass
        self.hovered = False
    
    def start_dwell(self):
        if not self._alive or not self.isVisible() or not self.isEnabled(): return
        if not self.hovered:
            self.hovered = True
            self.progress = 0
            self.dwell_timer.start(50)
            self.update()
    
    def stop_dwell(self):
        if not self._alive: return
        self.hovered = False
        self.progress = 0
        self.dwell_timer.stop()
        self.repeat_timer.stop()
        self.update()
    
    def _tick(self):
        if not self._alive: return
        if self.fired_while_hovered and not self.repeat:
            self.dwell_timer.stop()
            return
        self.progress += 50
        if self.progress >= self.dwell_ms:
            self.dwell_timer.stop()
            self.progress = 0
            self.fired_while_hovered = True
            self.click()
            if self.repeat: self.repeat_timer.start(140)
        self.update()
    
    def _repeat_click(self):
        if self.hovered and self.repeat and self._alive:
            self.click()
        else:
            self.repeat_timer.stop()
    
    def paintEvent(self, e):
        if not self._alive: return
        super().paintEvent(e)
        if self.progress > 0:
            p = QPainter(self)
            w = int((self.progress / self.dwell_ms) * self.width())
            p.fillRect(0, self.height() - 4, w, 4, QColor(0, 200, 255))
            p.end()

class EyeKeyboard(QWidget):
    request_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self.simulation_mode = True
        self.current_view = "letters"
        self.all_buttons = []
        self.gaze_x = 0
        self.gaze_y = 0
        
        self._build_ui()
        
        self.gaze_timer = QTimer(self)
        self.gaze_timer.timeout.connect(self._check_gaze)
        self.gaze_timer.start(30)

    def _build_ui(self):
        # Override stylesheets heavily to match original app
        # Background hardcoded to #1e1e1e to match original app regardless of parent theme
        self.setStyleSheet("""
        EyeKeyboard { background-color: #1e1e1e; }
        QLabel { color: #eaeaea; }
        QPushButton {
            background-color: #2a2a2a;
            color: #ffffff;
            border: none;
            border-radius: 16px;
            font-size: 18px;
            padding: 10px;
        }
        QPushButton:hover { background-color: #3a3a3a; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("👁️  Göz Takip Klavyesi  •  Bekleme: 1.2s")
        title.setStyleSheet("color:#bdbdbd; font-size:14px; background: transparent;")
        layout.addWidget(title)
        
        # Text
        self.text_display = QLabel("Yazmaya başlamak için harflere bakın...")
        self.text_display.setWordWrap(True)
        self.text_display.setFont(QFont("Segoe UI", 22))
        self.text_display.setStyleSheet("""
        QLabel {
            background-color: #252525;
            border-radius: 18px;
            padding: 22px;
            font-size: 26px;
            color: #eaeaea;
        }
        """)
        self.text_display.setFixedHeight(150)
        layout.addWidget(self.text_display)
        
        # Suggestions
        self.sug_frame = QFrame()
        self.sug_layout = QHBoxLayout(self.sug_frame)
        self.sug_layout.setSpacing(10)
        self.sug_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sug_frame)
        self.suggestion_buttons = []
        for _ in range(10):
            b = self._make_button("", action="SUGGESTION", w=160, h=52, repeat=False)
            b.setVisible(True)
            b.setEnabled(False)
            b.setStyleSheet("background: transparent;")
            self.suggestion_buttons.append(b)
            self.sug_layout.addWidget(b)
        self.sug_layout.addStretch()
        
        # Pages Stack
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)
        
        self.page_letters = QWidget()
        self.page_numbers = QWidget()
        self.page_phrases = QWidget()
        self.page_internet = QWidget()
        
        self.pages.addWidget(self.page_letters)
        self.pages.addWidget(self.page_numbers)
        self.pages.addWidget(self.page_phrases)
        self.pages.addWidget(self.page_internet)
        
        self._build_letters_page()
        self._build_numbers_page()
        self._build_phrases_page()
        self._build_internet_page()
        
        # Bottom Bar
        bottom = QWidget()
        bottom.setStyleSheet("background-color: #252525; border-radius: 18px; padding: 10px;")
        bottom_row = QHBoxLayout(bottom)
        bottom_row.setSpacing(12)
        bottom_row.setContentsMargins(10,5,10,5)
        
        self.btn_letters = self._make_button("⌨️ ABC", "VIEW_LETTERS", 160, 62)
        self.btn_numbers = self._make_button("# 123", "VIEW_NUMBERS", 160, 62)
        self.btn_phrases = self._make_button("💬 Cümle", "VIEW_PHRASES", 180, 62)
        self.btn_internet = self._make_button("🌐 Net", "VIEW_INTERNET", 180, 62)
        
        bottom_row.addWidget(self.btn_letters)
        bottom_row.addWidget(self.btn_numbers)
        bottom_row.addWidget(self.btn_phrases)
        bottom_row.addWidget(self.btn_internet)
        bottom_row.addStretch()
        
        # Simulation + Exit
        self.btn_sim = self._make_button("👁 Sim ON", "TOGGLE_SIM", 180, 62)
        self.btn_sim.setStyleSheet("background-color: #1f7a4d; border-radius: 18px; font-size: 16px;")
        
        self.btn_back = self._make_button("🔙 ÇIKIŞ", "BACK", 160, 62)
        self.btn_back.setStyleSheet("background-color: #bd2c40; border-radius: 18px; font-size: 16px; font-weight: bold;")
        
        bottom_row.addWidget(self.btn_sim)
        bottom_row.addWidget(self.btn_back)
        
        layout.addWidget(bottom)
        
        self.show_view("letters")
        self.update_suggestions()

    def _make_button(self, text, action, w=120, h=95, repeat=False):
        b = GazeButton(text, dwell_ms=1200, repeat=repeat)
        b.setFixedSize(w, h)
        b.setFont(QFont("Segoe UI", 20, QFont.Bold))
        b.setProperty("action", action)
        b.setProperty("value", text)
        b.clicked.connect(self.on_button_clicked)
        self.all_buttons.append(b)
        return b

    def _make_key(self, text, action="CHAR", w=120, h=95, repeat=False, style=""):
        b = self._make_button(text, action, w=w, h=h, repeat=repeat)
        if style: b.setStyleSheet(style)
        return b

    def show_view(self, name):
        self.current_view = name
        if name == "letters": self.pages.setCurrentWidget(self.page_letters)
        elif name == "numbers": self.pages.setCurrentWidget(self.page_numbers)
        elif name == "phrases": self.pages.setCurrentWidget(self.page_phrases)
        elif name == "internet": self.pages.setCurrentWidget(self.page_internet)

    def _build_letters_page(self):
        lay = QVBoxLayout(self.page_letters)
        lay.setSpacing(10)
        for row in KEYBOARD_ROWS:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(10)
            row_l.setAlignment(Qt.AlignCenter)
            for k in row: row_l.addWidget(self._make_key(k, "CHAR", 150, 130))
            lay.addWidget(row_w)
        lay.addWidget(self._bottom_keys_widget())

    def _build_numbers_page(self):
        lay = QVBoxLayout(self.page_numbers)
        lay.setSpacing(12)
        for row in NUMBER_GRID:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(12)
            row_l.setAlignment(Qt.AlignCenter)
            for n in row: row_l.addWidget(self._make_key(n, "CHAR", 150, 100))
            lay.addWidget(row_w)
        lay.addWidget(self._bottom_keys_widget())

    def _bottom_keys_widget(self):
        bottom = QWidget()
        l = QHBoxLayout(bottom)
        l.setSpacing(14)
        l.setAlignment(Qt.AlignCenter)
        sil = self._make_key("Sil", "DEL", 170, 95, repeat=True, style="QPushButton{background:#3a2a2a; border-radius:18px;}")
        bosluk = self._make_key("Boşluk", "SPACE", 460, 95, style="QPushButton{background:#2f3e55; border-radius:18px; font-size:18px;}")
        temiz = self._make_key("Temizle", "CLEAR", 220, 95, style="QPushButton{background:#5a2a2a; border-radius:18px;}")
        google = self._make_key("Google", "GOOGLE", 200, 95, style="QPushButton{background:#203a43; border-radius:18px;}")
        l.addWidget(sil)
        l.addWidget(bosluk)
        l.addWidget(temiz)
        l.addWidget(google)
        return bottom

    def _build_phrases_page(self):
        lay = QHBoxLayout(self.page_phrases)
        lay.setSpacing(18)
        lay.setAlignment(Qt.AlignTop)
        for title, phrases in PHRASE_CATEGORIES:
            col_w = QWidget()
            col = QVBoxLayout(col_w)
            col.setSpacing(10)
            lab = QLabel(title)
            lab.setStyleSheet("color:#00c8ff; font-weight:bold; font-size:16px;")
            col.addWidget(lab)
            for p in phrases[:9]:
                b = self._make_key(p, "PHRASE", 260, 58, style="QPushButton{background:#2a2a2a; border-radius:16px; font-size:14px; padding:8px;}")
                col.addWidget(b)
            col.addStretch()
            lay.addWidget(col_w)

    def _build_internet_page(self):
        lay = QHBoxLayout(self.page_internet)
        lay.setSpacing(40)
        lay.setAlignment(Qt.AlignCenter)
        def tile(text, action, bg):
            return self._make_key(text, action, 240, 200, style=f"QPushButton{{background:{bg}; border-radius:18px; font-size:20px; font-weight:bold;}} QPushButton:hover{{background:#3a3a3a;}}")
        lay.addWidget(tile("Google'da\nAra", "GOOGLE", "#203a43"))
        lay.addWidget(tile("YouTube", "YOUTUBE", "#5a2a2a"))
        lay.addWidget(tile("Instagram", "INSTAGRAM", "#3a2a4a"))
        lay.addWidget(tile("Wikipedia", "WIKIPEDIA", "#2a2a2a"))

    def on_button_clicked(self):
        btn = self.sender()
        if not btn: return
        action = btn.property("action")
        value = btn.property("value")

        if action == "VIEW_LETTERS": self.show_view("letters"); return
        if action == "VIEW_NUMBERS": self.show_view("numbers"); return
        if action == "VIEW_PHRASES": self.show_view("phrases"); return
        if action == "VIEW_INTERNET": self.show_view("internet"); return
        
        if action == "BACK":
            self.request_back.emit()
            return

        if action == "TOGGLE_SIM":
            self.toggle_sim()
            return

        if action == "CHAR": self.text += str(value)
        elif action == "SPACE": self.text += " "
        elif action == "DEL": self.text = self.text[:-1]
        elif action == "CLEAR": self.text = ""
        elif action == "PHRASE": self.text += str(value) + " "
        elif action == "SUGGESTION":
            word = str(value).strip()
            if word: self.select_suggestion(word)
        
        if action == "GOOGLE": self.open_google()
        elif action == "YOUTUBE": webbrowser.open("https://www.youtube.com")
        elif action == "INSTAGRAM": webbrowser.open("https://www.instagram.com")
        elif action == "WIKIPEDIA": webbrowser.open("https://tr.wikipedia.org")

        self.update_suggestions()
        self._refresh_text()

    def select_suggestion(self, word):
        parts = self.text.split()
        if parts and not self.text.endswith(" "): parts[-1] = word
        else: self.text += word + " "
        self.text += " "
        self._refresh_text()

    def _refresh_text(self):
        self.text_display.setText(self.text if self.text else "Yazmaya başlamak için harflere bakın...")
        
    def update_suggestions(self):
        words = self.text.split()
        current = words[-1].upper() if words and not self.text.endswith(" ") else ""
        sug_list = []
        if current:
            for L in range(len(current), 0, -1):
                pref = current[:L]
                if pref in TURKISH_WORDS:
                    for w in TURKISH_WORDS[pref]:
                        if w.upper().startswith(current) and w not in sug_list:
                            sug_list.append(w)
        else:
            sug_list = ["Merhaba", "Günaydın", "Teşekkür", "Lütfen", "Evet", "Hayır", "Yardım", "Doktor", "Su", "Tamam"]
        
        for i, b in enumerate(self.suggestion_buttons):
            if i < len(sug_list):
                w = sug_list[i]
                b.setText(w)
                b.setProperty("value", w)
                b.setEnabled(True)
                b.setStyleSheet("QPushButton { background-color:#333333; border-radius:22px; padding:8px 16px; font-size:15px; color:white; } QPushButton:hover { background-color:#444444; }")
            else:
                b.setText("")
                b.setProperty("value", "")
                b.setEnabled(False)
                b.setStyleSheet("background: transparent; border: none;")

    def open_google(self):
        q = self.text.strip()
        webbrowser.open(f"https://www.google.com/search?q={q}" if q else "https://www.google.com")

    def toggle_sim(self):
        self.simulation_mode = not self.simulation_mode
        if self.simulation_mode:
            self.btn_sim.setText("👁 Sim ON")
            self.btn_sim.setStyleSheet("background-color: #1f7a4d; border-radius: 18px; font-size: 16px;")
        else:
            self.btn_sim.setText("👁 Sim OFF")
            self.btn_sim.setStyleSheet("background-color: #555555; border-radius: 18px; font-size: 16px;")

    def _check_gaze(self):
        if self.simulation_mode:
            pos = QCursor.pos()
            self.gaze_x = pos.x()
            self.gaze_y = pos.y()
        for b in self.all_buttons:
             if not b.isVisible() or not b.isEnabled():
                 b.stop_dwell()
                 continue
             g = b.mapToGlobal(QPoint(0,0))
             if QRect(g, b.size()).contains(self.gaze_x, self.gaze_y): b.start_dwell()
             else: b.stop_dwell()


# ==========================================
#  MAIN APP (GUI V4) - INTEGRATION
# ==========================================
class EyeMouseAppV4(QWidget):
    frame_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eye Mouse OS (v4)")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(MAIN_STYLESHEET)
        
        self.running = False
        self.thread = None

        # --- ROOT LAYOUT ---
        # We use a StackedLayout at the VERY TOP
        # Index 0: Dashboard (Sidebar + Camera/Settings)
        # Index 1: Keyboard (Full Screen)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0,0,0,0)
        self.root_layout.setSpacing(0)
        
        self.main_stack = QStackedWidget()
        self.root_layout.addWidget(self.main_stack)
        
        # --- PAGE 1: DASHBOARD CONTAINER ---
        self.dashboard_widget = QWidget()
        dashboard_layout = QHBoxLayout(self.dashboard_widget)
        dashboard_layout.setContentsMargins(0,0,0,0)
        dashboard_layout.setSpacing(0)
        
        # 1. Sidebar (Inside Dashboard)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(250)
        side_lay = QVBoxLayout(self.sidebar)
        side_lay.setContentsMargins(10, 30, 10, 30)

        lbl_logo = QLabel("👁️ EyeOS")
        lbl_logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #cba6f7; margin-bottom: 20px;")
        side_lay.addWidget(lbl_logo)
        
        self.btn_cam = self._mk_side_btn("🎥 Kamera", True)
        self.btn_set = self._mk_side_btn("⚙️ Ayarlar", False)
        # Instead of switching stack index in same view, this switches ROOT stack
        self.btn_key = self._mk_side_btn("⌨️ Klavye", False) 
        
        side_lay.addWidget(self.btn_cam)
        side_lay.addWidget(self.btn_set)
        side_lay.addWidget(self.btn_key)
        side_lay.addStretch()
        
        # 2. Content Stack (Camera vs Settings)
        self.content_stack = QStackedWidget()
        self.page_cam = self._create_camera_page()
        self.page_set = self._create_settings_page()
        self.content_stack.addWidget(self.page_cam)
        self.content_stack.addWidget(self.page_set)
        
        dashboard_layout.addWidget(self.sidebar)
        dashboard_layout.addWidget(self.content_stack)
        
        # --- PAGE 2: KEYBOARD (Global) ---
        self.full_keyboard = EyeKeyboard()
        self.full_keyboard.request_back.connect(self.go_back_to_dashboard)
        
        # Add to Main Stack
        self.main_stack.addWidget(self.dashboard_widget) # Index 0
        self.main_stack.addWidget(self.full_keyboard)   # Index 1
        
        # Connections
        self.btn_cam.clicked.connect(lambda: self._nav_dashboard(0))
        self.btn_set.clicked.connect(lambda: self._nav_dashboard(1))
        self.btn_key.clicked.connect(self.switch_to_keyboard)
        
        # Signals
        self.frame_signal.connect(self.update_feed)
        
        # Shortcut: 'Q' to Stop
        self.shortcut_stop = QShortcut(QKeySequence("Q"), self)
        self.shortcut_stop.activated.connect(self.stop_engine)

    def _mk_side_btn(self, text, active):
        b = QPushButton(text)
        b.setProperty("class", "SidebarBtn")
        b.setCheckable(True)
        b.setChecked(active)
        b.setCursor(Qt.PointingHandCursor)
        return b

    def _nav_dashboard(self, idx):
        # Stay on Page 0 (Dashboard), switch Content Stack
        self.main_stack.setCurrentIndex(0)
        self.content_stack.setCurrentIndex(idx)
        
        # Visuals
        self.btn_cam.setChecked(idx == 0)
        self.btn_set.setChecked(idx == 1)
        self.btn_key.setChecked(False)

    def switch_to_keyboard(self):
        # Switch to Page 1 (Full Screen Keyboard)
        self.main_stack.setCurrentIndex(1)
        self.btn_key.setChecked(True) # Visual only, though sidebar hidden
        
    def go_back_to_dashboard(self):
        # Return to Page 0
        self.main_stack.setCurrentIndex(0)
        # Restore button states
        idx = self.content_stack.currentIndex()
        self.btn_cam.setChecked(idx == 0)
        self.btn_set.setChecked(idx == 1)
        self.btn_key.setChecked(False)

    def _create_camera_page(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30,30,30,30)

        head = QLabel("Kontrol Merkezi")
        head.setProperty("class", "Title")
        
        # Buttons
        h = QHBoxLayout()
        self.btn_start = QPushButton("BAŞLAT")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setProperty("class", "ActionBtn")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_engine)
        
        self.btn_stop = QPushButton("DURDUR")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setProperty("class", "ActionBtn")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_engine)
        
        h.addWidget(self.btn_start)
        h.addWidget(self.btn_stop)
        h.addStretch()
        
        # Feed
        self.lbl_feed = QLabel("Kamera Kapalı")
        self.lbl_feed.setAlignment(Qt.AlignCenter)
        self.lbl_feed.setStyleSheet("background: #000; border: 2px solid #333; border-radius: 12px; color: #555;")
        self.lbl_feed.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        lay.addWidget(head)
        lay.addLayout(h)
        lay.addSpacing(20)
        lay.addWidget(self.lbl_feed)
        return w

    def _create_settings_page(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40,40,40,40)
        lay.setAlignment(Qt.AlignTop)
        
        t = QLabel("Ayarlar")
        t.setProperty("class", "Title")
        lay.addWidget(t)
        
        self.sliders = {}
        self._add_sl(lay, "Smoothing", 0, 100, 15, "smoothing")
        self._add_sl(lay, "EAR Threshold", 10, 30, 20, "ear")
        self._add_sl(lay, "Cooldown", 20, 80, 30, "cooldown")
        self._add_sl(lay, "Double Blink Win", 30, 120, 60, "dbl_window")
        
        lay.addSpacing(20)
        self._add_sl(lay, "Sensitivity (x0.1)", 5, 50, 16, "sensitivity")
        self._add_sl(lay, "Deadzone (px)", 0, 20, 4, "deadzone")
        return w

    def _add_sl(self, lay, txt, minv, maxv, val, key):
        l = QLabel(f"{txt}: {val/100:.2f}")
        s = QSlider(Qt.Horizontal)
        s.setRange(minv, maxv)
        s.setValue(val)
        s.valueChanged.connect(lambda v: l.setText(f"{txt}: {v/100:.2f}"))
        lay.addWidget(l)
        lay.addWidget(s)
        lay.addSpacing(15)
        self.sliders[key] = s

    # LOGIC
    def start_engine(self):
        if self.running: return
        self.running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_feed.setText("Başlatılıyor...")
        
        # Params
        p = {
            'smoothing': self.sliders['smoothing'].value()/100,
            'ear_click_th': self.sliders['ear'].value()/100,
            'click_cooldown': self.sliders['cooldown'].value()/100,
            'dbl_blink_window': self.sliders['dbl_window'].value()/100,
            'sens_gain': self.sliders['sensitivity'].value()/10,
            'deadzone_px': self.sliders['deadzone'].value()
        }
        
        def loop():
            try:
                eye_mouse.main(
                    **p,
                    enable_right_click=True,
                    show_preview=False,
                    frame_callback=self.frame_signal.emit
                )
            except Exception as e:
                print(e)
            finally:
                self.stop_visuals()
        
        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def stop_engine(self):
        if self.running: eye_mouse.stop()

    def stop_visuals(self):
        self.running = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_feed.setText("Kamera Kapalı")

    @pyqtSlot(np.ndarray)
    def update_feed(self, frame):
        if not self.running: return
        h, w, ch = frame.shape
        qt = QImage(frame.data, w, h, ch*w, QImage.Format_RGB888)
        self.lbl_feed.setPixmap(QPixmap.fromImage(qt).scaled(
            self.lbl_feed.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EyeMouseAppV4()
    win.showMaximized()
    sys.exit(app.exec_())
