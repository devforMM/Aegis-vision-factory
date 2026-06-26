# 🏭 USINE — AI-Powered Industrial Safety Monitoring System

> **An intelligent industrial safety platform** combining computer vision, fire detection, and badge recognition for real-time monitoring of the work environment.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Technologies](#-technologies)
- [API Endpoints](#-api-endpoints)
- [Features](#-features)
- [Deep Learning Models](#-deep-learning-models)
- [Usage Examples](#-usage-examples)

---

## 🎯 Overview

**USINE** is a full-stack industrial surveillance platform that ensures the safety of personnel and facilities through **three main modalities**:

| Modality | Description |
|----------|-------------|
| 🦺 **PPE Detection** | Verification of personal protective equipment compliance |
| 🔥 **Fire Detection** | Real-time alerts on fire or smoke detection |
| 🪪 **Badge Recognition** | Worker identification and attendance tracking |

> Built with a **FastAPI** backend and a custom **HTML/JavaScript** frontend, powered by state-of-the-art computer vision models.

---

## 🏗️ Architecture

### Backend

```
back-end
├── bd_initialization
│   ├── Bridge.py
│   └── DataBase_models.py
├── deep_learning
├── images
├── models
│   └── models.py
├── routes
│   ├── admin_routes.py
│   ├── incidents_routes.py
│   ├── surveillance_routes.py
│   ├── utils.py
│   └── workers_routes.py
├── server
│   ├── celery_script.py
│   ├── server_utils.py
│   └── server.py
├── static
│   └── styles.css
```

### Frontend

```
├── AdminDashboard_template.html
│   ├── AdminLogin_template.html
│   ├── AdminRegister_template.html
│   ├── AllIncidents_template.html
│   ├── AllWorkers_template.html
│   ├── Attendances_template.html
│   ├── IncidentDetails_template.html
│   ├── MonitoringDashboard_template.html
│   ├── Register_attendance.html
│   ├── RegisterWorker_template.html
│   └── WorkerDetails_template.html
```

---

## 🛠️ Technologies

### Backend

| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.9+) |
| ASGI Server | Uvicorn |
| PPE Model | YOLO / Custom CNN |
| Fire Model | Deep CNN / YOLO |
| Badge Model | Deep Learning — OCR / Face Recognition |
| Database | PostgreSQL with SQLAlchemy |
| Acceleration | CUDA-optimized GPU inference |

### Frontend

| Component | Technology |
|-----------|------------|
| Framework | HTML5 / JavaScript (Vanilla) |
| State Management | Native DOM |
| HTTP Client | Fetch API |
| Camera | HTML5 Video |
| Real-time Rendering | WebSocket / Canvas |

---

## 🔌 API Endpoints

### 🦺 Surveillance & Detection

```http
POST /usine/surveillances/analyze
Content-Type: multipart/form-data
```

```json
// Request body
{ "frame": "<image or video frame>" }

// Response
{
  "ppe_detections": ["hard_hat", "safety_vest"],
  "missing_ppe": ["gloves", "safety_glasses"],
  "compliance": false,
  "confidence_scores": [0.96, 0.91]
}
```

---

### 🔥 Fire Detection

```http
POST /usine/surveillances/fire
Content-Type: multipart/form-data
```

```json
// Request body
{ "frame": "<image or video frame>" }

// Response
{ "fire_detected": true, "location": "Zone B - Camera 3", "confidence": 0.97 }
```

---

### 🪪 Badge Recognition

```http
POST /usine/workers/check-in
Content-Type: multipart/form-data
```

```json
// Request body
{ "badge_image": "<badge image>" }

// Response
{ "worker_id": "EMP-042", "name": "Karim Mansouri", "timestamp": "2025-06-26T08:32:00Z" }
```

---

### 📹 Camera Management

```http
GET  /usine/surveillances/camera/stream   → Live video feed
POST /usine/surveillances/camera/record   → Start recording
POST /usine/surveillances/camera/connect  → Connect a camera
```

---

### 🚨 Incident Management

```http
POST /usine/incidents/report              → Report an incident
GET  /usine/incidents/list                → List all incidents
GET  /usine/incidents/{id}/details        → Incident details
GET  /usine/incidents/analysis            → Global analysis
```

---

### 👤 User Management

```http
POST /usine/admin/login                   → Admin login
GET  /usine/admin/dashboard               → Admin dashboard
GET  /usine/workers                       → Worker list
POST /usine/workers/register              → Register a worker
GET  /usine/workers/check-in              → Clock in
GET  /usine/workers/check-out             → Clock out
```

---

## ✨ Features

### 🦺 PPE Detection

Verification of **5 safety equipment items**:

| Equipment | Label | Criticality |
|-----------|-------|-------------|
| Hard hat | `hard_hat` | 🔴 Mandatory |
| Safety vest | `safety_vest` | 🔴 Mandatory |
| Safety glasses | `safety_glasses` | 🟠 Recommended |
| Gloves | `gloves` | 🟠 Recommended |
| Steel-toe boots | `steel_boots` | 🔴 Mandatory |

**Key capabilities:**
- Real-time multi-person detection
- Global compliance rate calculation
- Automatic alerts on non-compliance
- High confidence threshold (false negatives not tolerated)

---

### 🔥 Fire Detection

- Real-time fire and smoke detection via camera feeds
- Very high confidence threshold (false positives not tolerated)
- Precise localization by camera and zone
- Automatic alert triggering
- Automatic video recording of the incident

---

### 🪪 Badge Recognition

- Worker identification at entry and exit
- Attendance tracking with timestamps
- Unauthorized access detection
- Complete check-in/out history

---

### 📊 Admin Dashboard

Real-time key safety metrics:

| Metric | Description |
|--------|-------------|
| Total workers | Total registered workforce |
| On-site now | Workers currently in the facility |
| Incidents today | Number of reported incidents |
| PPE compliance | Real-time compliance percentage |

---

### 🚨 Incident Management

Each incident is documented with:
- Detailed incident report form
- Classification and severity level
- Assignment to a responsible person
- Full incident timeline
- Associated photos and videos
- Resolution status and comments thread

---

## 🧠 Deep Learning Models

### PPE Detection Model

- **Type**: YOLO / Custom CNN
- **Input**: Image or video frame
- **Output**: Detected equipment + missing items

```python
from ultralytics import YOLO

def load_ppe_detection_model():
    return YOLO("ppe_model.pt")

def detect_ppe(model, frame, confidence_threshold=0.6):
    results = model(frame)[0]
    mask = results.boxes.conf >= confidence_threshold
    filtered = results[mask]
    class_names = model.names
    detected = [class_names[int(c)] for c in filtered.boxes.cls]
    required = ["hard_hat", "safety_vest", "steel_boots"]
    missing = [item for item in required if item not in detected]
    return detected, missing
```

---

### Fire Detection Model

- **Type**: Deep CNN / YOLO
- **Input**: Continuous video feed
- **Output**: Alert + localization

```python
def load_fire_detection_model():
    return YOLO("fire_model.pt")

def detect_fire(model, frame, confidence_threshold=0.85):
    results = model(frame)[0]
    mask = results.boxes.conf >= confidence_threshold
    fire_detected = len(results[mask]) > 0
    return {
        "fire_detected": fire_detected,
        "confidence": float(results.boxes.conf.max()) if fire_detected else 0.0
    }
```

---

### Badge Recognition Model

- **Type**: Deep Learning — OCR or face recognition
- **Input**: Badge image or face
- **Output**: Worker ID + timestamp

```python
def load_badge_recognition_model():
    return YOLO("badge_model.pt")

def recognize_badge(model, image):
    results = model(image)[0]
    worker_id = extract_worker_id(results)
    return {
        "worker_id": worker_id,
        "timestamp": datetime.now().isoformat()
    }
```

---

### Model Loading at Startup

```python
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
def load_models():
    app.state.models = {
        "ppe_model":   load_ppe_detection_model(),
        "fire_model":  load_fire_detection_model(),
        "badge_model": load_badge_recognition_model()
    }
```

---

## 🚀 Usage Examples

### 🦺 PPE Compliance Check Flow

```
1. Camera continuously captures the video feed of the work zone
2. Each frame is sent to /usine/surveillances/analyze
3. The PPE model detects worn and missing equipment
4. In case of non-compliance, an alert is triggered
5. The incident is logged and assigned to a supervisor
```

### 🔥 Fire Detection Flow

```
1. Cameras monitor high-risk zones continuously
2. Each frame is analyzed by /usine/surveillances/fire
3. On detection, an immediate alert is issued
4. The affected zone and camera are identified
5. Video recording starts automatically
```

### 🪪 Badge Check-in Flow

```
1. Worker presents their badge at the entrance
2. The image is sent to /usine/workers/check-in
3. The Badge model identifies the worker
4. The check-in is logged with a timestamp
5. Access is granted or denied based on permissions
```

---

## 🖥️ Frontend Features

- 📊 **Dashboard** with real-time safety metrics
- 📹 **Live camera feeds** with detection overlays
- 🔔 **Instant alerts** on incidents or non-compliance
- 👷 **Worker management** with attendance history
- 📋 **Incident tracking** with timeline and attachments
- 🔐 **Secure admin authentication**

---

## 📄 License

**MIT License** — See the `LICENSE` file for details.

---

<div align="center">

**Built with ❤️ using FastAPI, HTML/JS, and state-of-the-art industrial vision models**

</div>
