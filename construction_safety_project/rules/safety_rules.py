def check_violations(detections):
    violation = False
    message = ""
    color = "GREEN"

    detected_labels = [d['label'] for d in detections]

    if "person" in detected_labels and "helmet" not in detected_labels:
        violation = True
        message = "Helmet Missing"
        color = "RED"

    return violation, message, color
