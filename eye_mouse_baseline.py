import cv2, mediapipe as mp, numpy as np, time
from pynput.mouse import Controller, Button
import pyautogui

# Göz noktaları
LEFT_EYE  = [33,160,158,133,153,144]
RIGHT_EYE = [263,387,385,362,380,373]

mp_face = mp.solutions.face_mesh
mouse = Controller()

# Eye Aspect Ratio (EAR) ile göz kırpma tespiti
def ear(pts):
    A = np.linalg.norm(pts[1]-pts[5])
    B = np.linalg.norm(pts[2]-pts[4])
    C = np.linalg.norm(pts[0]-pts[3]) + 1e-6
    return (A+B)/(2.0*C)

def get_pts(lmk, w, h, idxs):
    return np.array([[lmk[i].x*w, lmk[i].y*h] for i in idxs], dtype=np.float32)

def main(smoothing=0.15, ear_click_th=0.20, click_cooldown=0.25):
    pyautogui.FAILSAFE = True
    sw, sh = pyautogui.size()

    # Kamerayı DSHOW ile aç
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prev = None
    last_click = 0

    with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True) as fm:
        while True:
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

                # İmleç konumu: sol göz ortalaması
                gaze = L.mean(axis=0)
                if prev is None: prev = gaze
                smoothed = prev*(1-smoothing) + gaze*smoothing
                prev = smoothed

                mx = int(np.clip(smoothed[0] / w * sw, 0, sw-1))
                my = int(np.clip(smoothed[1] / h * sh, 0, sh-1))
                mouse.position = (mx, my)

                # Göz kırpma → sol tık
                ear_val = (ear(L) + ear(R)) / 2.0
                now = time.time()
                if ear_val < ear_click_th and (now - last_click) > click_cooldown:
                    mouse.click(Button.left, 1)
                    last_click = now

                # Görsel geri bildirim
                for (x,y) in np.vstack((L,R)):
                    cv2.circle(frame, (int(x),int(y)), 1, (0,255,0), -1)
                cv2.putText(frame, f"EAR:{ear_val:.2f}  q:cikis", (10,30),
                            cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,255), 2)

            cv2.imshow("Eye mouse (q: exit)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
