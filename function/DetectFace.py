import cv2
from threading import Thread

from function import PlaySound

cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

state = True

def detectFace(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    for x, y, w, h in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 106, 42), 2)

        position_circle = (x + w // 2, y + h // 2)
        position_start_line = (320, 240)
        cv2.line(frame, position_start_line, position_circle, (0, 0, 255), 1)
        cv2.circle(frame, position_circle, 3, (0, 255, 0), 2)
        total = position_circle[0] - position_start_line[0]

        text = "Detecting-Face"

        cv2.putText(
            frame,
            text,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (47, 173, 255),
            2,
        )

        if state:
            Thread(target=PlaySound.setSound, args=("sad"))
            thread = Thread(target=PlaySound.playSound)
            thread.start()
            print(thread)

def openCamera():
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        detectFace(frame)

        # display camera
        cv2.imshow("TOMI Detecting people", frame)

        # wait for pressed q letter
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\nEnding...")
            break

    cap.release()
    cv2.destroyAllWindows()
