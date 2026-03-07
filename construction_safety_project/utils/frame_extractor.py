import cv2
import time
import sys
import os
from datetime import datetime
# PDF Library Imports
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from alerts.telegram_alert import send_telegram_alert
except ImportError:
    def send_telegram_alert(msg): print(f"DEBUG: {msg}")

# Safety Risk Data
EFFECTS_MAP = {
    "Helmet Missing": "High risk of traumatic brain injury from falling objects.",
    "Vest Missing": "Reduced visibility to machinery operators, leading to collisions.",
    "Boots Missing": "Increased risk of puncture wounds or crushed feet.",
    "Gloves Missing": "Vulnerability to chemical burns, abrasions, and hand injuries."
}

ZONE_COLOR_MAP = {
    "Helmet Missing": "RED",
    "Vest Missing": "ORANGE",
    "Boots Missing": "BLUE",
    "Gloves Missing": "YELLOW"
}

global_status = "SAFE"

def get_global_status():
    return global_status

def generate_pdf_report(video_name, violation_data):
    """Generates a professional PDF audit report."""
    try:
        report_dir = os.path.join(project_root, "static", "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report_path = os.path.join(report_dir, filename)
        
        c = canvas.Canvas(report_path, pagesize=letter)
        width, height = letter

        # Title and Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "PPE SAFETY AUDIT REPORT")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Video Source: {video_name}")
        c.drawString(50, height - 85, f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        c.setStrokeColor(colors.black)
        c.line(50, height - 95, 550, height - 95)

        # Table Headers
        y = height - 120
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Time")
        c.drawString(100, y, "Violation")
        c.drawString(200, y, "Zone")
        c.drawString(280, y, "Safety Risk (Consequences)")

        # Table Content
        c.setFont("Helvetica", 9)
        y -= 20
        for v in violation_data:
            if y < 50: # New Page if space is low
                c.showPage()
                y = height - 50
            
            c.drawString(50, y, v['time'])
            c.drawString(100, y, v['type'])
            c.drawString(200, y, v['zone'])
            # Wrap text for the risk description
            risk_text = v['effect']
            c.drawString(280, y, risk_text[:60]) # Simple truncation for PDF layout
            y -= 15

        c.save()
        print(f"PDF REPORT GENERATED: {report_path}")
        return filename
    except Exception as e:
        print(f"ERROR SAVING PDF: {e}")
        return None

def generate_frames(model_main, model_gloves, video_path):
    global global_status
    cap = cv2.VideoCapture(video_path)
    video_name = os.path.basename(video_path)
    
    violation_list = []
    last_alert = {k: 0 for k in EFFECTS_MAP.keys()}
    timers = {k: 0 for k in EFFECTS_MAP.keys()}

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success: break

            res_m = model_main.predict(frame, imgsz=640, conf=0.20, verbose=False)
            res_g = model_gloves.predict(frame, imgsz=640, conf=0.20, verbose=False)
            
            seen = [model_main.names[int(c)].lower() for r in res_m for c in r.boxes.cls] + \
                   [model_gloves.names[int(c)].lower() for r in res_g for c in r.boxes.cls]

            current = []
            if any(x in seen for x in ["person", "vest", "helmet", "hardhat"]):
                if not any(h in seen for h in ["helmet", "hardhat", "head"]): current.append("Helmet Missing")
                if not any(v in seen for v in ["vest", "jacket"]): current.append("Vest Missing")
                if not any(b in seen for b in ["boots", "boot", "shoes"]): current.append("Boots Missing")
                if not any(g in seen for g in ["gloves", "glove", "hand"]): current.append("Gloves Missing")

            confirmed = []
            for v in ZONE_COLOR_MAP.keys():
                if v in current:
                    if timers[v] == 0: timers[v] = time.time()
                    if time.time() - timers[v] > 1.5: confirmed.append(v)
                else: timers[v] = 0

            if confirmed:
                global_status = "DANGER: " + ", ".join(confirmed)
                ts = datetime.now().strftime("%H:%M:%S")
                for v in confirmed:
                    if time.time() - last_alert[v] > 60:
                        zone = ZONE_COLOR_MAP[v]
                        risk = EFFECTS_MAP[v]
                        
                        violation_list.append({'time': ts, 'type': v, 'zone': zone, 'effect': risk})
                        
                        # --- UPDATED TELEGRAM FORMAT ---
                        alert_msg = (
                            f"🚨 PPE ALERT 🚨\n"
                            f"Violation: {v}\n"
                            f"Zone: {zone}\n"
                            f"Time: {ts}\n"
                            f"Risk: {risk}"
                        )
                        send_telegram_alert(alert_msg)
                        last_alert[v] = time.time()
            else:
                global_status = "SAFE"

            # Visualization
            for r in res_m: frame = r.plot()
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    except GeneratorExit:
        pass
    finally:
        cap.release()
        if violation_list:
            generate_pdf_report(video_name, violation_list)