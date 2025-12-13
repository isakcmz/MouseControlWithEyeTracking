import cv2, mediapipe as mp, numpy as np, time, pandas as pd, os

# Göz landmark indexleri
LEFT_EYE  = [33,160,158,133,153,144]
RIGHT_EYE = [263,387,385,362,380,373]

mp_face = mp.solutions.face_mesh

def get_pts(lmk, w, h, idxs):
    return np.array([[lmk[i].x*w, lmk[i].y*h] for i in idxs], dtype=np.float32)

# Kalibrasyon noktaları (ekran koordinatları)
def get_targets(sw, sh):
    return [
        (int(sw*0.1), int(sh*0.1)),   # sol-üst
        (int(sw*0.9), int(sh*0.1)),   # sağ-üst
        (int(sw*0.1), int(sh*0.9)),   # sol-alt
        (int(sw*0.9), int(sh*0.9)),   # sağ-alt
        (int(sw*0.5), int(sh*0.5))    # orta
    ]

def main(samples_per_point=30, delay=2.0):
    sw, sh = 1920, 1080  # varsayılan ekran çözünürlüğü (pyautogui.size() ile de alınabilir)

    save_path = "../data/raw/calibration.csv"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    data = []
    with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True) as fm:
        for tx, ty in get_targets(sw, sh):
            print(f"👉 Bu noktaya bak: ({tx}, {ty})")
            time.sleep(delay)

            count = 0
            while count < samples_per_point:
                ok, frame = cap.read()
                if not ok: break
                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = fm.process(rgb)

                if res.multi_face_landmarks:
                    lm = res.multi_face_landmarks[0].landmark
                    L = get_pts(lm, w, h, LEFT_EYE)
                    R = get_pts(lm, w, h, RIGHT_EYE)
                    gaze = np.vstack((L,R)).mean(axis=0)

                    data.append([gaze[0], gaze[1], tx, ty])
                    count += 1

                cv2.circle(frame, (tx//4, ty//4), 15, (0,0,255), -1)  # hedefi küçültülmüş olarak göster
                cv2.imshow("Calibration", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    cap.release(); cv2.destroyAllWindows(); return

    cap.release()
    cv2.destroyAllWindows()

    df = pd.DataFrame(data, columns=["eye_x","eye_y","screen_x","screen_y"])
    df.to_csv(save_path, index=False)
    print(f"✅ Kalibrasyon verisi kaydedildi: {save_path}")

if __name__ == "__main__":
    main()
