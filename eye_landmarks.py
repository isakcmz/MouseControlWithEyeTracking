# src/eye_landmarks.py
import cv2, mediapipe as mp, numpy as np

# Göz ve iris noktaları
LEFT_EYE  = [33,160,158,133,153,144]
RIGHT_EYE = [263,387,385,362,380,373]
LEFT_IRIS  = [468,469,470,471,472]
RIGHT_IRIS = [473,474,475,476,477]

mp_face = mp.solutions.face_mesh

def get_pts(lmk, w, h, idxs):
    return np.array([[lmk[i].x*w, lmk[i].y*h] for i in idxs], dtype=np.float32)

# Kamera açılışı CAP_DSHOW ile
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True) as fm:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = fm.process(rgb)

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            for idxs in (LEFT_EYE, RIGHT_EYE, LEFT_IRIS, RIGHT_IRIS):
                for (x,y) in get_pts(lm, w, h, idxs):
                    cv2.circle(frame, (int(x),int(y)), 2, (0,255,0), -1)

        cv2.putText(frame, "q: cikis", (10,30), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,255), 2)
        cv2.imshow("Eye landmarks", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
