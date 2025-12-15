import cv2, mediapipe as mp, numpy as np, time, pandas as pd, os

# Göz landmark indexleri
LEFT_EYE  = [33,160,158,133,153,144]
RIGHT_EYE = [263,387,385,362,380,373]

mp_face = mp.solutions.face_mesh

def get_pts(lmk, w, h, idxs):
    return np.array([[lmk[i].x*w, lmk[i].y*h] for i in idxs], dtype=np.float32)

# --- 3x3 Kalibrasyon hedefleri ---
def get_targets(sw, sh):
    xs = [0.15, 0.5, 0.85]
    ys = [0.15, 0.5, 0.85]
    targets = []
    for y in ys:
        for x in xs:
            targets.append((int(sw * x), int(sh * y)))
    return targets

def main(samples_per_point=40, delay=2.0):
    sw, sh = 1920, 1080  # ekran çözünürlüğü

    save_path = "../data/raw/calibration.csv"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    data = []

    # --- Fullscreen pencere ---
    cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Calibration",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True) as fm:
        for tx, ty in get_targets(sw, sh):
            print(f"👉 Bu noktaya bak: ({tx}, {ty})")
            time.sleep(delay)

            count = 0
            while count < samples_per_point:
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
                    gaze = np.vstack((L, R)).mean(axis=0)

                    data.append([gaze[0], gaze[1], tx, ty])
                    count += 1

                # --- Kırmızı hedef nokta (tam ekran oranlı) ---
                draw_x = int(tx / sw * w)
                draw_y = int(ty / sh * h)
                cv2.circle(frame, (draw_x, draw_y), 15, (0, 0, 255), -1)

                cv2.imshow("Calibration", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    cap.release()
                    cv2.destroyAllWindows()
                    return

    cap.release()
    cv2.destroyAllWindows()

    df = pd.DataFrame(
        data,
        columns=["eye_x", "eye_y", "screen_x", "screen_y"]
    )
    df.to_csv(save_path, index=False)
    print(f"✅ Kalibrasyon verisi kaydedildi: {save_path}")

if __name__ == "__main__":
    main()
