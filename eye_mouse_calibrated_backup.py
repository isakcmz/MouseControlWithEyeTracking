# src/eye_mouse_calibrated.py
import cv2, mediapipe as mp, numpy as np, time, joblib
from pynput.mouse import Controller, Button
import pyautogui

# --- Göz landmark indeksleri ---
LEFT_EYE  = [33,160,158,133,153,144]
RIGHT_EYE = [263,387,385,362,380,373]

mp_face = mp.solutions.face_mesh
mouse = Controller()
stop_flag = False

# ----------------- Yardımcılar -----------------
def ear(pts: np.ndarray) -> float:
    """Eye Aspect Ratio (EAR)"""
    A = np.linalg.norm(pts[1]-pts[5])
    B = np.linalg.norm(pts[2]-pts[4])
    C = np.linalg.norm(pts[0]-pts[3]) + 1e-6
    return (A + B) / (2.0 * C)

def get_pts(lmk, w, h, idxs):
    return np.array([[lmk[i].x*w, lmk[i].y*h] for i in idxs], dtype=np.float32)

def stop():
    global stop_flag
    stop_flag = True

# ----------------- Ana Döngü -----------------
def main(
    # hareket/klik
    smoothing=0.22,             # temel yumuşatma (yakında kullanılır)
    ear_click_th=0.20,
    click_cooldown=0.30,        # tıklamalar arası bekleme (s)
    enable_right_click=True,    # sağ göz 2x → sağ tık
    enable_double_click=False,  # iki göz 2x → çift tık (opsiyonel)
    dbl_blink_window=0.60,      # iki kırpma arası max süre (s)
    # stabilizasyon
    hold_on_blink=True,         # göz kapalıyken imleci tut
    hold_extra_ms=0.12,         # açıldıktan sonra şu kadar s daha tut
    deadzone_px=4,              # küçük titreşimleri yok say
    max_step_px=35,             # bir karede max adım
    # hız/yaklaşma
    sens_gain=1.6,              # 👈 Hız kazancı (dx,dy çarpanı)
    far_dist=120,               # 👈 Uzak hedef eşiği (px)
    alpha_far=0.35,              # 👈 Uzakta iken daha yüksek alpha (daha hızlı)
    frame_callback=None,        # 👈 GUI'ye frame göndermek için callback
    show_preview=True           # 👈 cv2.imshow açılsın mı?
):
    """
    Kalibrasyonlu göz→mouse kontrolü:
      • Aynı gözle 2 hızlı kırpma → tıklama (sol/sağ)
      • Hold-on-blink, deadzone, max-step
      • Hız kazancı (sens_gain) + uzak/ yakın hedefe göre adaptif smoothing
    """
    global stop_flag
    stop_flag = False

    pyautogui.FAILSAFE = True
    sw, sh = pyautogui.size()

    # Kalibrasyon modeli: (gaze_x, gaze_y) -> (screen_x, screen_y)
    model = joblib.load("../data/models/calibration_model.pkl")
    print("✅ Kalibrasyon modeli yüklendi.")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prev = None               # önceki imleç konumu
    last_click = 0.0          # global tıklama cooldown

    # --- Double-blink durumları ---
    left_closed  = False
    right_closed = False
    left_blink_count  = 0
    right_blink_count = 0
    left_last_blink_time  = 0.0
    right_last_blink_time = 0.0

    with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True) as fm:
        while True:
            if stop_flag:
                break

            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = fm.process(rgb)

            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark
                L = get_pts(lm, w, h, LEFT_EYE)
                R = get_pts(lm, w, h, RIGHT_EYE)

                now = time.time()
                L_ear = ear(L)
                R_ear = ear(R)

                # --- Hedef imleç konumu (kalibrasyon modeli) ---
                gaze = np.vstack((L, R)).mean(axis=0)
                pred = model.predict([[gaze[0], gaze[1]]])[0]
                tx = int(np.clip(pred[0], 0, sw - 1))
                ty = int(np.clip(pred[1], 0, sh - 1))

                # --- Stabil hareket (Hold + Deadzone + Max-step + Adaptif smoothing) ---
                any_closed = (L_ear < ear_click_th) or (R_ear < ear_click_th)
                just_reopened = (
                    (now - left_last_blink_time)  < hold_extra_ms or
                    (now - right_last_blink_time) < hold_extra_ms
                )

                if prev is None:
                    prev = (tx, ty)

                if hold_on_blink and (any_closed or just_reopened):
                    mx, my = prev
                else:
                    # fark + hız kazancı
                    dx = (tx - prev[0]) * sens_gain
                    dy = (ty - prev[1]) * sens_gain

                    # deadzone
                    if abs(dx) < deadzone_px: dx = 0
                    if abs(dy) < deadzone_px: dy = 0

                    # max step
                    if dx > 0:  dx = min(dx, max_step_px)
                    else:       dx = max(dx, -max_step_px)
                    if dy > 0:  dy = min(dy, max_step_px)
                    else:       dy = max(dy, -max_step_px)

                    # uzak/ yakın adaptif smoothing
                    dist = ((tx - prev[0])**2 + (ty - prev[1])**2) ** 0.5
                    alpha = alpha_far if dist > far_dist else smoothing

                    mx = prev[0] + dx
                    my = prev[1] + dy
                    mx = int(prev[0] * (1 - alpha) + mx * alpha)
                    my = int(prev[1] * (1 - alpha) + my * alpha)

                prev = (mx, my)
                mouse.position = (mx, my)

                # --- Double-blink tıklama mantığı ---
                # Sol göz: kapandı -> açıldı
                if not left_closed and L_ear < ear_click_th:
                    left_closed = True
                if left_closed and L_ear >= ear_click_th:
                    left_closed = False
                    if now - left_last_blink_time <= dbl_blink_window:
                        left_blink_count += 1
                    else:
                        left_blink_count = 1
                    left_last_blink_time = now

                    if left_blink_count >= 2 and (now - last_click) > click_cooldown:
                        mouse.click(Button.left, 1)
                        last_click = now
                        left_blink_count = 0

                # Sağ göz: kapandı -> açıldı
                if not right_closed and R_ear < ear_click_th:
                    right_closed = True
                if right_closed and R_ear >= ear_click_th:
                    right_closed = False
                    if now - right_last_blink_time <= dbl_blink_window:
                        right_blink_count += 1
                    else:
                        right_blink_count = 1
                    right_last_blink_time = now

                    if enable_right_click and right_blink_count >= 2 and (now - last_click) > click_cooldown:
                        mouse.click(Button.right, 1)
                        last_click = now
                        right_blink_count = 0

                # (Opsiyonel) iki göz için double-click
                if enable_double_click:
                    # İstersen burada iki göz için benzer pencere mantığıyla çift tık ekleyebilirsin.
                    pass

                # --- Görsel geri bildirim ---
                for (x, y) in np.vstack((L, R)):
                    cv2.circle(frame, (int(x), int(y)), 1, (0, 255, 0), -1)
                cv2.putText(
                    frame,
                    f"L:{L_ear:.2f} R:{R_ear:.2f} | L2x:{left_blink_count} R2x:{right_blink_count}  q:cikis",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2
                )

            # Callback varsa frame gönder
            if frame_callback is not None:
                # Frame'i GUI thread'inde işlenmesi için kopyalayabiliriz veya direk gönderebiliriz.
                # GUI genellikle RGB ister, biz zaten rgb değişkenine sahibiz.
                # Ancak çizimler 'frame' (BGR) üzerinde yapıldı.
                # Bu yüzden çizim yapılmış frame'i RGB'ye çevirip göndermek mantıklı.
                final_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_callback(final_rgb)

            if show_preview:
                cv2.imshow("Eye mouse (calibrated)", frame)
                cv2.setWindowProperty("Eye mouse (calibrated)", cv2.WND_PROP_TOPMOST, 1)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    cap.release()
    cv2.destroyAllWindows()
