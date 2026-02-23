from flask import Flask, render_template, Response, request, jsonify
import cv2
import os
from ultralytics import YOLO
from datetime import datetime
from alerts.telegram_alert import send_telegram_alert

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = YOLO("models/yolo/best.pt")

video_path = None
sent_violations = set()
violation_log = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global video_path, sent_violations, violation_log

    sent_violations.clear()
    violation_log.clear()

    if "video" not in request.files:
        return jsonify({"status": "error"})

    file = request.files["video"]

    if file.filename == "":
        return jsonify({"status": "error"})

    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(video_path)

    return jsonify({"status": "success"})


@app.route("/violations")
def get_violations():
    return jsonify(violation_log)


def generate_frames():
    global video_path, sent_violations, violation_log

    if video_path is None:
        return

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        persons = 0
        helmets = 0
        gloves = 0
        vests = 0

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls].lower()

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)

                if label == "person":
                    persons += 1
                if label == "helmet":
                    helmets += 1
                if label == "gloves":
                    gloves += 1
                if label == "vest":
                    vests += 1

        # Worker condition
        if persons > 0 and vests > 0:

            if helmets == 0 and "Helmet Missing" not in sent_violations:
                send_violation("Helmet Missing")

            if gloves == 0 and "Gloves Missing" not in sent_violations:
                send_violation("Gloves Missing")

        _, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


def send_violation(name):
    global sent_violations, violation_log

    timestamp = datetime.now().strftime("%H:%M:%S")

    message = (
        f"🚨 PPE VIOLATION DETECTED 🚨\n\n"
        f"Violation: {name}\n"
        f"Zone: Red Zone\n"
        f"Location: Construction Site\n"
        f"Time: {timestamp}"
    )

    send_telegram_alert(message)

    sent_violations.add(name)
    violation_log.append(f"[{timestamp}] {name}")


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__== "__main__":
    app.run(debug=True)