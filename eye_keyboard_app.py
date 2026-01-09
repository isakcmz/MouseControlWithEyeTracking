import sys
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSizePolicy, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QFont, QCursor, QPainter, QColor


# =======================
# KLAVYE / VERİLER
# =======================

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

# Yazdıkça çıkacak örnek kelimeler (istersen büyütürüz)
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


# =======================
# GAZE BUTTON (DWELL)
# =======================

class GazeButton(QPushButton):
    """
    - Dwell ile tıklama
    - Harf/normal tuşlar: aynı hover içinde tekrar tekrar basmaz (eeee yapmaz)
    - repeat=True olan tuşlarda (Sil gibi) hover'da tekrarlar
    """
    def __init__(self, text="", dwell_ms=1200, repeat=False, parent=None):
        super().__init__(text, parent)
        self.dwell_ms = dwell_ms
        self.repeat = repeat

        self.hovered = False
        self.progress = 0
        self.fired_while_hovered = False

        self._alive = True  # güvenlik

        self.dwell_timer = QTimer(self)
        self.dwell_timer.timeout.connect(self._tick)

        self.repeat_timer = QTimer(self)
        self.repeat_timer.timeout.connect(self._repeat_click)

        self.setMouseTracking(True)

    def cleanup(self):
        """Widget silinmese bile dwell timerları kapat."""
        self._alive = False
        try:
            self.dwell_timer.stop()
            self.repeat_timer.stop()
        except Exception:
            pass
        self.hovered = False
        self.progress = 0
        self.fired_while_hovered = False
        self.update()

    def start_dwell(self):
        if not self._alive:
            return
        if not self.isVisible() or not self.isEnabled():
            return
        if not self.hovered:
            self.hovered = True
            self.progress = 0
            self.fired_while_hovered = False
            self.dwell_timer.start(50)
            self.update()

    def stop_dwell(self):
        if not self._alive:
            return
        self.hovered = False
        self.progress = 0
        self.fired_while_hovered = False
        self.dwell_timer.stop()
        self.repeat_timer.stop()
        self.update()

    def _tick(self):
        if not self._alive:
            self.dwell_timer.stop()
            return

        if self.fired_while_hovered and not self.repeat:
            self.dwell_timer.stop()
            return

        self.progress += 50

        if self.progress >= self.dwell_ms:
            self.dwell_timer.stop()
            self.progress = 0
            self.fired_while_hovered = True

            # click tetikle
            self.click()

            if self.repeat:
                self.repeat_timer.start(140)

        self.update()

    def _repeat_click(self):
        if not self._alive:
            self.repeat_timer.stop()
            return
        if self.hovered and self.repeat:
            self.click()
        else:
            self.repeat_timer.stop()

    def paintEvent(self, e):
        if not self._alive:
            return
        super().paintEvent(e)
        if self.progress > 0:
            p = QPainter(self)
            w = int((self.progress / self.dwell_ms) * self.width())
            p.fillRect(0, self.height() - 4, w, 4, QColor(0, 200, 255))
            p.end()


# =======================
# APP
# =======================

class EyeKeyboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.text = ""
        self.simulation_mode = True
        self.current_view = "letters"

        self.all_buttons = []  # gaze kontrol listesi

        # gaze koordinatları (istersen dış tracker burayı besler)
        self.gaze_x = 0
        self.gaze_y = 0

        self._build_ui()

        # gaze kontrol timer
        self.gaze_timer = QTimer(self)
        self.gaze_timer.timeout.connect(self._check_gaze)
        self.gaze_timer.start(30)

    # ---------- UI ----------
    def _build_ui(self):
        self.setWindowTitle("Göz Takip Klavyesi")
        self.setStyleSheet("""
        QMainWindow { background-color: #1e1e1e; }
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

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("👁️  Göz Takip Klavyesi  •  Bekleme: 1.2s")
        title.setStyleSheet("color:#bdbdbd; font-size:14px;")
        root.addWidget(title)

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
            padding: 22px;
            font-size: 26px;
            color: #eaeaea;
        }
        """)
        self.text_display.setFixedHeight(150) # Sabit yükseklik
        root.addWidget(self.text_display)

        # Öneri bar (SABİT buton havuzu -> deleteLater YOK)
        self.sug_frame = QFrame()
        self.sug_layout = QHBoxLayout(self.sug_frame)
        self.sug_layout.setSpacing(10)
        self.sug_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.sug_frame)

        self.suggestion_buttons = []
        for _ in range(10):
            b = self._make_button("", action="SUGGESTION", w=160, h=52, repeat=False)
            b.setVisible(False)
            b.setStyleSheet("""
            QPushButton {
                background-color:#333333;
                border-radius:22px;
                padding:8px 16px;
                font-size:15px;
                color:white;
            }
            QPushButton:hover { background-color:#444444; }
            """)
            self.suggestion_buttons.append(b)
            self.sug_layout.addWidget(b)

        self.sug_layout.addStretch()

        # Sayfalar: letters / numbers / phrases / internet
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

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

        # Alt kontrol bar
        bottom = QWidget()
        bottom.setStyleSheet("""
        QWidget {
            background-color: #252525;
            border-radius: 18px;
            padding: 10px;
        }
        """)
        bottom_row = QHBoxLayout(bottom)
        bottom_row.setSpacing(12)

        self.btn_letters = self._make_button("⌨️  ABC", action="VIEW_LETTERS", w=160, h=62)
        self.btn_numbers = self._make_button("# 123", action="VIEW_NUMBERS", w=160, h=62)
        self.btn_phrases = self._make_button("💬 Cümleler", action="VIEW_PHRASES", w=180, h=62)
        self.btn_internet = self._make_button("🌐 İnternet", action="VIEW_INTERNET", w=180, h=62)

        bottom_row.addWidget(self.btn_letters)
        bottom_row.addWidget(self.btn_numbers)
        bottom_row.addWidget(self.btn_phrases)
        bottom_row.addWidget(self.btn_internet)
        bottom_row.addStretch()

        self.btn_sim = self._make_button("👁 Simülasyon ON", action="TOGGLE_SIM", w=220, h=62)
        self.btn_sim.setStyleSheet("""
        QPushButton {
            background-color: #1f7a4d;
            border-radius: 18px;
            padding: 12px 22px;
            font-size: 16px;
        }
        """)
        bottom_row.addWidget(self.btn_sim)

        root.addWidget(bottom)

        # ilk görünüm
        self.show_view("letters")
        self.update_suggestions()
        self.showMaximized()

    # ---------- Button factory (lambda yok) ----------
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
        if style:
            b.setStyleSheet(style)
        return b

    # ---------- Views ----------
    def show_view(self, name):
        self.current_view = name
        if name == "letters":
            self.pages.setCurrentWidget(self.page_letters)
        elif name == "numbers":
            self.pages.setCurrentWidget(self.page_numbers)
        elif name == "phrases":
            self.pages.setCurrentWidget(self.page_phrases)
        elif name == "internet":
            self.pages.setCurrentWidget(self.page_internet)

    # ---------- Letters page ----------
    def _build_letters_page(self):
        lay = QVBoxLayout(self.page_letters)
        lay.setSpacing(10)

        for row in KEYBOARD_ROWS:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(10)
            row_l.setAlignment(Qt.AlignCenter)
            for k in row:
                row_l.addWidget(self._make_key(k, "CHAR", w=150, h=130))
            lay.addWidget(row_w)

        lay.addWidget(self._bottom_keys_widget())

    # ---------- Numbers page ----------
    def _build_numbers_page(self):
        lay = QVBoxLayout(self.page_numbers)
        lay.setSpacing(12)

        for row in NUMBER_GRID:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(12)
            row_l.setAlignment(Qt.AlignCenter)
            for n in row:
                row_l.addWidget(self._make_key(n, "CHAR", w=150, h=100))
            lay.addWidget(row_w)

        lay.addWidget(self._bottom_keys_widget())

    def _bottom_keys_widget(self):
        bottom = QWidget()
        l = QHBoxLayout(bottom)
        l.setSpacing(14)
        l.setAlignment(Qt.AlignCenter)

        # Sil (repeat)
        sil = self._make_key(
            "Sil", "DEL",
            w=170, h=95, repeat=True,
            style="QPushButton{background:#3a2a2a; border-radius:18px;}"
        )

        # Boşluk (en büyük)
        bosluk = self._make_key(
            "Boşluk", "SPACE",
            w=460, h=95,
            style="QPushButton{background:#2f3e55; border-radius:18px; font-size:18px;}"
        )

        # Temizle
        temiz = self._make_key(
            "Temizle", "CLEAR",
            w=220, h=95,
            style="QPushButton{background:#5a2a2a; border-radius:18px;}"
        )

        # Google arama (klavye içinde)
        google = self._make_key(
            "Google", "GOOGLE",
            w=200, h=95,
            style="QPushButton{background:#203a43; border-radius:18px;}"
        )

        l.addWidget(sil)
        l.addWidget(bosluk)
        l.addWidget(temiz)
        l.addWidget(google)
        return bottom

    # ---------- Phrases page ----------
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

            # scroll yok: ilk 9 taneyi göster
            for p in phrases[:9]:
                b = self._make_key(
                    p, "PHRASE",
                    w=260, h=58,
                    style="QPushButton{background:#2a2a2a; border-radius:16px; font-size:14px; padding:8px;}"
                )
                b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                col.addWidget(b)

            col.addStretch()
            lay.addWidget(col_w)

    # ---------- Internet page ----------
    def _build_internet_page(self):
        lay = QHBoxLayout(self.page_internet)
        lay.setSpacing(40)
        lay.setAlignment(Qt.AlignCenter)

        def tile(text, action, bg):
            return self._make_key(
                text, action,
                w=240, h=200,
                style=f"""
                QPushButton {{
                    background:{bg};
                    border-radius:18px;
                    font-size:20px;
                    font-weight:bold;
                }}
                QPushButton:hover {{
                    background:#3a3a3a;
                }}
                """
            )

        lay.addWidget(tile("Google'da\nAra", "GOOGLE", "#203a43"))
        lay.addWidget(tile("YouTube", "YOUTUBE", "#5a2a2a"))
        lay.addWidget(tile("Instagram", "INSTAGRAM", "#3a2a4a"))
        lay.addWidget(tile("Wikipedia", "WIKIPEDIA", "#2a2a2a"))

    # ---------- Single handler (false yok) ----------
    def on_button_clicked(self, checked=False):
        btn = self.sender()
        if not btn:
            return

        action = btn.property("action")
        value = btn.property("value")

        # View switching
        if action == "VIEW_LETTERS":
            self.show_view("letters")
            return
        if action == "VIEW_NUMBERS":
            self.show_view("numbers")
            return
        if action == "VIEW_PHRASES":
            self.show_view("phrases")
            return
        if action == "VIEW_INTERNET":
            self.show_view("internet")
            return

        # Toggle sim
        if action == "TOGGLE_SIM":
            self.toggle_sim()
            return

        # Text actions
        if action == "CHAR":
            self.text += str(value)
            self._refresh_text()
            return

        if action == "SPACE":
            self.text += " "
            self._refresh_text()
            return

        if action == "DEL":
            if self.text:
                self.text = self.text[:-1]
            self._refresh_text()
            return

        if action == "CLEAR":
            self.text = ""
            self._refresh_text()
            return

        if action == "PHRASE":
            phrase = str(value)
            if self.text and not self.text.endswith(" "):
                self.text += " "
            self.text += phrase + " "
            self._refresh_text()
            return

        if action == "SUGGESTION":
            word = str(value).strip()
            if word:
                self.select_suggestion(word)
            return

        # Internet
        if action == "GOOGLE":
            self.open_google()
            return
        if action == "YOUTUBE":
            self.open_youtube()
            return
        if action == "INSTAGRAM":
            self.open_instagram()
            return
        if action == "WIKIPEDIA":
            self.open_wikipedia()
            return

    # ---------- Simulation ----------
    def toggle_sim(self):
        self.simulation_mode = not self.simulation_mode
        if self.simulation_mode:
            self.btn_sim.setText("👁 Simülasyon ON")
            self.btn_sim.setStyleSheet("""
            QPushButton { background-color:#1f7a4d; border-radius:18px; padding:12px 22px; font-size:16px; }
            """)
        else:
            self.btn_sim.setText("👁 Simülasyon OFF")
            self.btn_sim.setStyleSheet("""
            QPushButton { background-color:#555555; border-radius:18px; padding:12px 22px; font-size:16px; }
            """)

    # ---------- Gaze API ----------
    def update_gaze(self, x, y):
        """Dış göz takip sistemin burayı besleyebilir."""
        self.gaze_x = int(x)
        self.gaze_y = int(y)

    def _check_gaze(self):
        if self.simulation_mode:
            pos = QCursor.pos()
            self.gaze_x = pos.x()
            self.gaze_y = pos.y()

        for b in self.all_buttons:
            if not b.isVisible() or not b.isEnabled():
                b.stop_dwell()
                continue

            g = b.mapToGlobal(QPoint(0, 0))
            r = QRect(g, b.size())
            if r.contains(self.gaze_x, self.gaze_y):
                b.start_dwell()
            else:
                b.stop_dwell()

    # ---------- Text ----------
    def _refresh_text(self):
        self.text_display.setText(self.text if self.text else "Yazmaya başlamak için harflere bakın...")
        self.update_suggestions()

    # ---------- Suggestions (BUTONLAR SİLİNMİYOR; SADECE GÜNCELLENİYOR) ----------
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

        # 10 sabit buton havuzunu güncelle
        for i, b in enumerate(self.suggestion_buttons):
            if i < len(sug_list):
                w = sug_list[i]
                b.setText(w)
                b.setProperty("value", w)   # action zaten SUGGESTION
                b.setEnabled(True)
                b.setStyleSheet("""
                QPushButton {
                    background-color:#333333;
                    border-radius:22px;
                    padding:8px 16px;
                    font-size:15px;
                    color:white;
                }
                QPushButton:hover { background-color:#444444; }
                """)
            else:
                # Butonu gizleme, sadece boşalt ve disable et (Kaymayı önler)
                b.setText("")
                b.setProperty("value", "")
                b.setEnabled(False)
                b.setStyleSheet("background: transparent; border: none;") # Görünmez gibi yap ama yer kaplasın
            
            b.setVisible(True) # Her zaman görünür kalsın ki layout oynamasın

    def select_suggestion(self, word):
        parts = self.text.split()
        if parts and not self.text.endswith(" "):
            parts[-1] = word
            self.text = " ".join(parts) + " "
        else:
            self.text += word + " "
        self._refresh_text()

    # ---------- Internet ----------
    def open_google(self):
        q = self.text.strip()
        if q:
            webbrowser.open(f"https://www.google.com/search?q={q}")
        else:
            webbrowser.open("https://www.google.com")

    def open_youtube(self):
        webbrowser.open("https://www.youtube.com")

    def open_instagram(self):
        webbrowser.open("https://www.instagram.com")

    def open_wikipedia(self):
        q = self.text.strip()
        if q:
            webbrowser.open(f"https://tr.wikipedia.org/wiki/{q}")
        else:
            webbrowser.open("https://tr.wikipedia.org")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = EyeKeyboard()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
