from datetime import datetime
from fastapi import APIRouter, Depends, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bd_initialization.DataBase_models import Attendance,Worker,Admin
from bd_initialization.Bridge import get_session
from server.server_utils import create_token, verify_password, get_current_admin, hash_password

templates = Jinja2Templates(directory="../front-end")
admin_router = APIRouter()


# ==============================================================================
# AUTHENTICATION PAGES (GET REQUESTS)
# ==============================================================================

@admin_router.get("/register", response_class=HTMLResponse)
async def admin_register_page(request: Request):
    """
    Renders the administrator registration form page.
    """
    return templates.TemplateResponse(
        request=request,
        name="AdminRegister_template.html",
        context={}
    )


@admin_router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """
    Renders the administrator login page.
    """
    return templates.TemplateResponse(
        request=request,
        name="AdminLogin_template.html",
        context={}
    )


# ==============================================================================
# AUTHENTICATION ACTIONS (POST REQUESTS)
# ==============================================================================

@admin_router.post("/register")
def create_admin(
    last_name: str = Form(...),
    first_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    age: int = Form(...),
    password: str = Form(...),
    db=Depends(get_session)
):
    """
    Processes the registration form submitted by a new administrator.
    """
    hashed_pwd = hash_password(password)

    new_admin = Admin(
        last_name=last_name,
        first_name=first_name,
        email=email,
        phone_number=phone_number,
        address=address,
        age=age,
        password=hashed_pwd
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return RedirectResponse(url="/factory/admin/login", status_code=303)


@admin_router.post("/login", response_class=HTMLResponse)
def login_admin(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    database=Depends(get_session)
):
    """
    Authenticates administrator credentials.
    """
    user = database.query(Admin).filter(Admin.email == email).first()

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="AdminLogin_template.html",
            context={"error": "❌ Email not found"}
        )

    if not verify_password(password, user.password):
        return templates.TemplateResponse(
            request=request,
            name="AdminLogin_template.html",
            context={"error": "❌ Incorrect password"}
        )

    payload = {"id": user.id}
    token = create_token(payload)

    response = RedirectResponse(
        "/factory/admin/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True
    )

    return response

@admin_router.get("/logout")
def logout_admin():
    """
    Logs out the administrator by removing the access token cookie.
    """
    response = RedirectResponse(
        url="/factory/admin/login",
        status_code=303
    )
    response.delete_cookie("access_token")
    return response

# ==============================================================================
# DASHBOARD & MANAGEMENT (GET/POST REQUESTS)
# ==============================================================================

@admin_router.get("/dashboard", response_class=HTMLResponse)
def dashboard_template(request: Request, admin=Depends(get_current_admin)):
    print(admin)
    """
    Compiles and displays real-time metrics and daily incident logs.
    """
    current_date_str = datetime.now().strftime("%d/%m/%Y")

    incidents = [
        incident for incident in admin.incidents
        if incident.date == current_date_str
    ]

    fire_count = sum(len(i.fire_detections or []) for i in admin.incidents)
    ppe_count = sum(len(i.ppe_detections or []) for i in admin.incidents)

    workers_count = len(admin.workers)
    incidents_count = len(admin.incidents)

    return templates.TemplateResponse(
        request=request,
        name="AdminDashboard_template.html",
        context={
            "admin": admin,
            "incidents": incidents,
            "fire_count": fire_count,
            "ppe_count": ppe_count,
            "workers_count": workers_count,
            "incidents_count": incidents_count
        }
    )


@admin_router.get("/attendance/log", response_class=HTMLResponse)
def view_attendance_log(request: Request, database=Depends(get_session)):
    """
    Fetches the daily attendance ledger list.
    """
    current_date_str = datetime.now().strftime("%d/%m/%Y")
    status_msg = request.query_params.get("msg")

    attendances = database.query(Attendance).filter(Attendance.date == current_date_str).all()

    attendance_register = []

    for record in attendances:
        worker = database.query(Worker).filter(Worker.id == record.worker_id).first()

        attendance_register.append({
            "attendance_id": record.id,
            "worker_id": worker.id,
            "worker_informations": f"{worker.last_name} {worker.first_name}",
            "role": worker.role,
            "etat": record.status,
            "date": record.date,
            "heure": record.check_in_time
        })

    return templates.TemplateResponse(
        request=request,
        name="Attendances_template.html",
        context={
            "registre_presences": attendance_register,
            "msg": status_msg
        }
    )


@admin_router.get("/attendance/mark/{attendance_id}")
def mark_attendance_record(attendance_id: int, admin=Depends(get_current_admin), database=Depends(get_session)):
    current_date_str = datetime.now().strftime("%d/%m/%Y")
    attendance = database.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    worker = database.query(Worker).filter(Worker.id == attendance.worker_id, Worker.admin_id == admin.id).first()
    if not worker:
        raise HTTPException(status_code=403, detail="Unauthorized")

    attendance.status = "Present"
    attendance.check_in_time = datetime.now().strftime("%H:%M")
    database.commit()

    return RedirectResponse("/factory/admin/attendance/log?msg=marked", status_code=303)


@admin_router.post("/attendance/new_register")
def create_attendance_register(
    admin=Depends(get_current_admin),
    database=Depends(get_session),
):
    """
    Initializes a new blank attendance registry sheet for the current day.
    """
    current_date_str = datetime.now().strftime("%d/%m/%Y")

    if database.query(Attendance).filter(Attendance.date == current_date_str).first():
        return RedirectResponse(
            "/factory/admin/attendance/log?msg=exist",
            status_code=303
        )

    for single_worker in admin.workers:
        new_attendance = Attendance(
            status="Absent",
            date=current_date_str,
            worker_id=single_worker.id
        )
        single_worker.attendances.append(new_attendance)
        database.add(new_attendance)

    database.commit()

    return RedirectResponse(
        "/factory/admin/attendance/log?msg=created",
        status_code=303
    )