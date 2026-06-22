import datetime
import time
import cv2
from celery import Celery
import subprocess

# Internal dependencies
from bd_initialization.DataBase_models import *
from deep_learning.functions import get_models
from routes.utils import format_video_time

# ==============================================================================
# MODELS CORE INITIALIZATION
# ==============================================================================
models = get_models()
ppe_model = models["ppe_model"]
fire_model = models["fire_model"]


# ==============================================================================
# CELERY WORKER CONFIGURATION
# ==============================================================================
celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)


# ==============================================================================
# ASYNCHRONOUS BACKEND PROCESSING TASK
# ==============================================================================
@celery_app.task
def predict(original_video_path, analysed_video_path, admin_id):
    database = session_local()
    cap = cv2.VideoCapture(original_video_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if not fps or fps != fps:
        fps = 20

    temp_video_path = analysed_video_path.replace(".mp4", "_temp.mp4")
    video_format = cv2.VideoWriter_fourcc(*'mp4v')
    analysed_video_writer = cv2.VideoWriter(
        temp_video_path,
        video_format,
        fps,
        (width, height)
    )

    fire_detections = []
    ppe_detections = []

    FIRE_CONFIDENCE_THRESHOLD = 0.70
    COOLDOWN = 5
    last_fire_time = 0.0
    last_ppe_time = 0.0
    frame_count = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            current_video_time = frame_count / fps

            fire_results = fire_model(frame)[0]
            ppe_results = ppe_model(frame)[0]

            annotated = frame.copy()

            fire_detection_batch = []
            for box in fire_results.boxes:
                conf = float(box.conf[0])
                if conf < FIRE_CONFIDENCE_THRESHOLD:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                label = fire_model.names[cls]

                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(annotated, f"{label} {conf:.0%}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                fire_detection_batch.append({
                    "class": label,
                    "confidence": f"{conf * 100:.2f} %"
                })

            if fire_detection_batch and (current_video_time - last_fire_time > COOLDOWN):
                fire_detections.append({
                    "detections": fire_detection_batch,
                    "timestamp": format_video_time(current_video_time)
                })
                last_fire_time = current_video_time

            ppe_summary = {}
            for box in ppe_results.boxes:
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                label = ppe_model.names[cls]

                if label.lower().startswith("no"):
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    cv2.putText(annotated, f"{label} {conf:.0%}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                if label in ppe_summary:
                    ppe_summary[label]["quantity"] += 1
                    if conf > ppe_summary[label]["max_confidence"]:
                        ppe_summary[label]["max_confidence"] = conf
                else:
                    ppe_summary[label] = {
                        "quantity": 1,
                        "max_confidence": conf
                    }

            ppe_detection_batch = []
            for label, data in ppe_summary.items():
                ppe_detection_batch.append({
                    "class": label,
                    "quantity": data["quantity"],
                    "confidence": f"{data['max_confidence'] * 100:.2f} %"
                })

            has_violation = any(item["class"].lower().startswith("no") for item in ppe_detection_batch)

            if has_violation and (current_video_time - last_ppe_time > COOLDOWN):
                ppe_detections.append({
                    "detections": ppe_detection_batch,
                    "timestamp": format_video_time(current_video_time)
                })
                last_ppe_time = current_video_time

            analysed_video_writer.write(annotated)

        # Re-encode avec ffmpeg en H.264 lisible partout
        cap.release()
        analysed_video_writer.release()

        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_video_path,
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-pix_fmt", "yuv420p",
            analysed_video_path
        ], check=True)

        os.remove(temp_video_path)

        admin = database.query(Admin).filter(Admin.id == admin_id).first()

        incident_report = Incident(
            original_video_path=original_video_path,
            analyzed_video_path=analysed_video_path,
            admin_id=admin.id,
            date=datetime.datetime.now().strftime("%d/%m/%Y"),
            fire_detections=fire_detections,
            ppe_detections=ppe_detections
        )

        admin.incidents.append(incident_report)
        database.commit()

        return {"status": "analysis completed successfully"}

    except Exception as runtime_error:
        return {"status": "error", "message": str(runtime_error)}

    finally:
        if cap.isOpened():
            cap.release()
        analysed_video_writer.release()
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        database.close()