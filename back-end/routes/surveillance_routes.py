import asyncio
import base64
import os
import subprocess
from datetime import datetime
import cv2
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from bd_initialization.Bridge import get_session
from bd_initialization.DataBase_models import Incident
from routes.utils import format_video_time
from server.celery_script import predict
from server.server_utils import get_admin_from_ws, get_current_admin

templates = Jinja2Templates(directory="../front-end")
surveillances_router = APIRouter()



@surveillances_router.websocket("/live_surveillance")
async def live_detctions(
    websocket: WebSocket,
    database=Depends(get_session),
    admin=Depends(get_admin_from_ws)
):
    print(admin)
    """
    Establishes a WebSocket connection for real-time video surveillance streaming.
    """
    incident_count = len(admin.incidents) + 1
    report_folder_path = os.path.join(
        "admins_files", f"admin_{admin.id}", "incidents", f"report-{incident_count}"
    )
    os.makedirs(report_folder_path, exist_ok=True)

    original_tmp_path = os.path.join(report_folder_path, "original_tmp.avi")
    analysed_tmp_path = os.path.join(report_folder_path, "analysed_tmp.avi")
    original_video_path = os.path.join(report_folder_path, "original_video.mp4")
    analysed_video_path = os.path.join(report_folder_path, "output_video.mp4")

    video_format = cv2.VideoWriter_fourcc(*'XVID')
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        await websocket.accept()
        await websocket.send_json({"error": "Camera device not available or failed to open (device 0)"})
        await websocket.close()
        return
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 30
    
    original_video_writer = cv2.VideoWriter(
        original_tmp_path, video_format, fps, (width, height)
    )
    analysed_video_writer = cv2.VideoWriter(
        analysed_tmp_path, video_format, fps, (width, height)
    )

    if not original_video_writer.isOpened() or not analysed_video_writer.isOpened():
        await websocket.accept()
        await websocket.send_json({"error": "Failed to initialize video writers. Check codec and output directory."})
        await websocket.close()
        cap.release()
        if original_video_writer.isOpened():
            original_video_writer.release()
        if analysed_video_writer.isOpened():
            analysed_video_writer.release()
        return

    ppe_model = websocket.app.state.ppe_model
    fire_model = websocket.app.state.fire_model

    fire_detections = []
    ppe_detections = []

    await websocket.accept()

    FIRE_CONFIDENCE_THRESHOLD = 0.70
    frame_count = 0
    last_fire_alert_time = 0.0  # Pour l'alerte UI seulement
    last_ppe_alert_time = 0.0   # Pour l'alerte UI seulement
    UI_ALERT_COOLDOWN = 5  # Cooldown pour limiter les alertes à l'interface

    try:
        while websocket.client_state.name == "CONNECTED":
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            current_video_time = (frame_count - 1) / fps

            fire_results = fire_model(frame)[0]
            ppe_results = ppe_model(frame)[0]

            annotated = frame.copy()

            # FIRE
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

            # PPE
            ppe_summary = {}
            for box in ppe_results.boxes:
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                label = ppe_model.names[cls]

                if label.lower().startswith("no"):
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    cv2.putText(annotated, label, (x1, y1 - 10),
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

            analysed_video_writer.write(annotated)
            original_video_writer.write(frame)

            _, buffer = cv2.imencode(".jpg", annotated)
            image_text = base64.b64encode(buffer).decode("utf-8")

            # ====== ENREGISTREMENT DANS LA BASE DE DONNÉES ======
            # Enregistre TOUTES les détections (pas de cooldown)
            if fire_detection_batch:
                fire_detections.append({
                    "detections": fire_detection_batch,
                    "timestamp": format_video_time(current_video_time)
                })

            has_violation = any(item["class"].lower().startswith("no") for item in ppe_detection_batch)
            if has_violation:
                ppe_detections.append({
                    "detections": ppe_detection_batch,
                    "timestamp": format_video_time(current_video_time)
                })

            # ====== ENVOYER AU FRONTEND (TOUJOURS) ======
            # Le frontend a besoin des détections du frame actuel pour l'affichage
            
            # Déclencher l'alerte son seulement avec cooldown
            should_alert_fire = fire_detection_batch and (current_video_time - last_fire_alert_time > UI_ALERT_COOLDOWN)
            if should_alert_fire:
                last_fire_alert_time = current_video_time

            should_alert_ppe = has_violation and (current_video_time - last_ppe_alert_time > UI_ALERT_COOLDOWN)
            if should_alert_ppe:
                last_ppe_alert_time = current_video_time

            await websocket.send_json({
                "text_image": image_text,
                "timestamp": format_video_time(current_video_time),
                "fire_detection": fire_detection_batch,      # ← TOUJOURS les détections actuelles
                "ppe_detection": ppe_detection_batch,        # ← TOUJOURS les détections actuelles
                "fire_alert": should_alert_fire,             # ← Pour jouer le son
                "ppe_alert": should_alert_ppe                # ← Pour activer l'alerte
            })

            await asyncio.sleep(0.03)

    except WebSocketDisconnect:
        print("client disconnected")

    finally:
        cap.release()
        analysed_video_writer.release()
        original_video_writer.release()

        if os.path.exists(original_tmp_path):
            subprocess.run([
                "ffmpeg", "-y", "-i", original_tmp_path,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                original_video_path
            ], check=False)
            os.remove(original_tmp_path)
        else:
            print(f"original tmp file missing, skipping conversion: {original_tmp_path}")

        if os.path.exists(analysed_tmp_path):
            subprocess.run([
                "ffmpeg", "-y", "-i", analysed_tmp_path,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                analysed_video_path
            ], check=False)
            os.remove(analysed_tmp_path)
        else:
            print(f"analysed tmp file missing, skipping conversion: {analysed_video_path}")

        try:
            incident_entry = Incident(
                original_video_path=original_video_path,
                analyzed_video_path=analysed_video_path,
                admin_id=admin.id,
                date=datetime.now().strftime("%d/%m/%Y"),
                fire_detections=fire_detections,  # ← TOUTES les détections
                ppe_detections=ppe_detections      # ← TOUTES les détections
            )

            admin.incidents.append(incident_entry)
            database.commit()

        except Exception as database_error:
                print(f"[ERROR] Erreur base de données lors de l'enregistrement de l'incident : {database_error}")
                database.rollback()

@surveillances_router.post("/video_analysis")
async def saved_video_surveillance(
    video: UploadFile = File(),
    admin = Depends(get_current_admin),

):
    """
    Accepts static video uploads from administrative users for processing.
    """
    try:
        incident_count = len(admin.incidents) + 1

        report_folder_path = os.path.join(
            "admins_files", f"admin_{admin.id}", "incidents", f"report-{incident_count}"
        )
        os.makedirs(report_folder_path, exist_ok=True)

        original_video_path = os.path.join(report_folder_path, "original_video.mp4")
        analysed_video_path = os.path.join(report_folder_path, "output_video.mp4")

        video_payload = await video.read()
        with open(original_video_path, "wb") as output_file:
            output_file.write(video_payload)

        task = predict.delay(
            original_video_path,
            analysed_video_path,
            admin.id
        )
        
        while not task.ready():
            await asyncio.sleep(0.03)
            
        return {
            "message": "Analysis completed successfully"  # Translated response API string
        }
        
    except Exception as processing_error:
         raise HTTPException(detail=f"Error: {processing_error}", status_code=505)


@surveillances_router.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="MonitoringDashboard_template.html",
        context={}
    )