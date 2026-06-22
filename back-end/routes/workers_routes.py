import base64
import os
import shutil
from datetime import datetime
import cv2
import face_recognition
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Internal dependencies
from bd_initialization.DataBase_models import *
from bd_initialization.Bridge import get_session
from routes.utils import *
from server.server_utils import create_token, get_current_admin, hash_password, verify_password

templates = Jinja2Templates(directory="../front-end")
workers_routes = APIRouter()


# ==============================================================================
# WORKER REGISTRATION ENDPOINTS (GET/POST)
# ==============================================================================

@workers_routes.get("/register")
def login_template(request: Request):
    """
    Renders the worker registration form page.
    """
    return templates.TemplateResponse(
        request=request,
        name="RegisterWorker_template.html",
        context={}
    )


@workers_routes.post("/register")
def register_worker(
    request: Request,
    last_name: str = Form(...),
    first_name: str = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    role: str = Form(...),
    age: str = Form(...),
    gender: str = Form(...),
    face: UploadFile = File(...),
    database=Depends(get_session),
    admin=Depends(get_current_admin)
):
    """
    Handles a new worker registration. Uploads the worker's reference face image 
    to a dedicated administrator directory and records user profiles in the database.
    """
    if admin:
        try:
            # Build the storage path directory framework for the administrator
            complete_face_path = os.path.join(
                "admins_files",
                f"admin_{admin.id}",
                "workers_faces",
            )
            os.makedirs(complete_face_path, exist_ok=True)

            # Generate the specific unique file path for the worker's reference image
            image_path = os.path.join(complete_face_path, f"{last_name}_{first_name}.jpg")

            # Stream save uploaded image file stream to the local disk destination
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(face.file, buffer)

            # Create the structural database worker model entry instance
            worker = Worker(
                last_name=last_name,
                first_name=first_name,
                phone_number=phone_number,
                address=address,
                role=role,
                age=age,
                gender=gender,
                admin_id=admin.id,
                status="Absent",
                face_image_path=image_path
            )

            database.add(worker)
            database.commit()
            database.refresh(worker)

            return RedirectResponse(
                "/factory/workers/all",
                status_code=303
            )

        except Exception as e:
            # Revert mutations cleanly if file writing operations fail
            database.rollback()
            return templates.TemplateResponse(
                request=request,
                name="RegisterWorker_template.html",
                context={"message": f"❌ Error {e} occurred during worker creation"}
            )


# ==============================================================================
# WORKER LISTS AND DETAILED INFORMATION (GET)
# ==============================================================================

@workers_routes.get("/all", response_class=HTMLResponse)
def get_workers(request: Request, user=Depends(get_current_admin)):
    """
    Fetches and displays all the workers bound to the logged-in administrator.
    """
    workers_list = user.workers
    return templates.TemplateResponse(
        request=request,
        name="AllWorkers_template.html",
        context={"workers": workers_list}
    )


@workers_routes.get("/worker-details/{id_worker}", response_class=HTMLResponse)
def worker_informations(id_worker: int, request: Request, user=Depends(get_current_admin), database=Depends(get_session)):
    """
    Retrieves individual static profile specifications for a unique worker identifier.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Perform target entity validation database query lookup
        worker = database.query(Worker).filter(Worker.id == id_worker).first()

        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        # Map entity object properties to an explicit payload dictionary
        worker_infos = {
            "id": worker.id,
            "last_name": worker.last_name,
            "first_name": worker.first_name,
            "phone_number": worker.phone_number,
            "address": worker.address,
            "role": worker.role,
            "age": worker.age,
            "gender": worker.gender,
            "status": worker.status,
            "image_path": worker.face_image_path
        }

        return templates.TemplateResponse(
            request=request,
            name="WorkerDetails_template.html",
            context={"worker_infos": worker_infos}
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error while fetching worker details: {e}")



# ==============================================================================
# BIOMETRIC FACE RECOGNITION ATTENDANCE CHECK-IN (GET/POST)
# ==============================================================================

@workers_routes.post("/mark_attendance")
async def mark_attendance(
    request: Request,
    worker_id: int = Form(None),
    admin=Depends(get_current_admin),
    database=Depends(get_session)
):
    """
    Triggers automated face recognition attendance checking via the server camera.
    Compares real-time face embeddings with administrative reference files 
    and updates matching workers' attendance entries.
    """
    # Open camera stream frame target capturing
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return templates.TemplateResponse(
            request=request,
            name="Attendances_template.html",
            context={
                "message": "❌ Unable to connect to the server's camera feed",
                "image": None
            }
        )

    # Convert the raw captured frame from BGR matrix format to RGB for processing
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_positions = face_recognition.face_locations(rgb_image)
    detected_encodings = face_recognition.face_encodings(rgb_image, face_positions)

    # Safeguard validation check if no geometric face shapes exist in the view
    if not detected_encodings:
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return templates.TemplateResponse(
            request=request,
            name="Register_attendance.html",
            context={
                "message": "❌ No human face detected within the video stream frame",
                "image": image_base64
            }
        )

    status_message = "❌ Face structure unrecognized"
    worker_found = False

    # Execute geometric profile array indexing loops across registered users
    for single_worker in admin.workers:
        if worker_id is not None and single_worker.id != worker_id:
            continue

        # Load reference target disk arrays and process numerical vectors
        known_image = face_recognition.load_image_file(single_worker.face_image_path)
        known_encodings = face_recognition.face_encodings(known_image)

        if not known_encodings:
            continue

        known_encoding = known_encodings[0]

        # Scan active frames matrices matches across live facial vector spaces
        for (top, right, bottom, left), detected_encoding in zip(face_positions, detected_encodings):
            match_results = face_recognition.compare_faces([known_encoding], detected_encoding, tolerance=0.6)

            if match_results[0]:
                worker_found = True
                full_name = f"{single_worker.last_name} {single_worker.first_name}"

                # Draw bounding box identification boundaries on matrix overlays
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(
                    frame, full_name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                )

                # Mutate current session records data flags
                today_str = datetime.now().strftime("%d/%m/%Y")
                current_day_attendance = next((p for p in single_worker.attendances if p.date == today_str), None)

                if current_day_attendance:
                    current_day_attendance.status = "Present"
                    current_day_attendance.check_in_time = datetime.now().strftime("%H:%M")
                    database.commit()
                    status_message = f"✅ Verified: {full_name}"
                else:
                    status_message = f"⚠️ {full_name} identified, but no attendance logs session initialization exists for today"

                break

    # Re-encode spatial matrix changes back into standard base64 layout structures
    _, buffer = cv2.imencode('.jpg', frame)
    image_base64 = base64.b64encode(buffer).decode('utf-8')

    return templates.TemplateResponse(
        request=request,
        name="Register_attendance.html",
        context={
            "message": status_message,
            "image": image_base64
        }
    )


@workers_routes.get("/mark_attendance")
async def presence(request: Request, worker_id: int = None, admin=Depends(get_current_admin), database=Depends(get_session)):
    """
    Renders the manual/biometric presence logging interface for facial recognition.
    """
    worker_name = None
    if worker_id is not None:
        target_worker = database.query(Worker).filter(Worker.id == worker_id, Worker.admin_id == admin.id).first()
        if target_worker:
            worker_name = f"{target_worker.last_name} {target_worker.first_name}"

    return templates.TemplateResponse(
        request=request,
        name="Register_attendance.html",
        context={
            "worker_id": worker_id,
            "worker_name": worker_name
        }
    )