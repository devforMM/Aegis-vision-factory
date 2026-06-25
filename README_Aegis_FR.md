# 🏭 USINE — Système de Surveillance Industrielle par Intelligence Artificielle

> **Une plateforme de sécurité industrielle intelligente** combinant vision par ordinateur, détection d'incendies et reconnaissance de badges pour un monitoring en temps réel de l'environnement de travail.

---

## 📋 Table des Matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Technologies](#-technologies)
- [Endpoints API](#-endpoints-api)
- [Fonctionnalités](#-fonctionnalités)
- [Modèles de Deep Learning](#-modèles-de-deep-learning)
- [Exemples d'utilisation](#-exemples-dutilisation)

---

## 🎯 Vue d'ensemble

**USINE** est une plateforme de surveillance industrielle full-stack qui assure la sécurité du personnel et des installations selon **trois modalités principales** :

| Modalité | Description |
|----------|-------------|
| 🦺 **Détection des EPI** | Vérification du port des équipements de protection individuelle |
| 🔥 **Détection d'Incendie** | Alertes en temps réel sur détection de feu ou fumée |
| 🪪 **Reconnaissance de Badges** | Identification des travailleurs et suivi des présences |

> Construit avec un backend **FastAPI** et un frontend **HTML/JavaScript** personnalisé, propulsé par des modèles de vision par ordinateur à l'état de l'art.

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

| Composant | Technologie |
|-----------|-------------|
| Framework | FastAPI (Python 3.9+) |
| Serveur ASGI | Uvicorn |
| Modèle EPI | YOLO / CNN personnalisé |
| Modèle Incendie | Deep CNN / YOLO |
| Modèle Badge | Deep Learning — OCR / Reconnaissance faciale |
| Base de Données | PostgreSQL avec SQLAlchemy |
| Accélération | Inférence optimisée CUDA (GPU) |

### Frontend

| Composant | Technologie |
|-----------|-------------|
| Framework | HTML5 / JavaScript (Vanilla) |
| Gestion d'état | DOM natif |
| Client HTTP | Fetch API |
| Caméra | HTML5 Video |
| Rendu temps réel | WebSocket / Canvas |

---

## 🔌 Endpoints API

### 🦺 Surveillance & Détection

```http
POST /usine/surveillances/analyze
Content-Type: multipart/form-data
```

```json
// Corps de la requête
{ "frame": "<image ou frame vidéo>" }

// Réponse
{
  "ppe_detections": ["casque", "gilet"],
  "missing_ppe": ["gants", "lunettes"],
  "compliance": false,
  "confidence_scores": [0.96, 0.91]
}
```

---

### 🔥 Détection d'Incendie

```http
POST /usine/surveillances/fire
Content-Type: multipart/form-data
```

```json
// Corps de la requête
{ "frame": "<image ou frame vidéo>" }

// Réponse
{ "fire_detected": true, "location": "Zone B - Caméra 3", "confidence": 0.97 }
```

---

### 🪪 Reconnaissance de Badge

```http
POST /usine/workers/check-in
Content-Type: multipart/form-data
```

```json
// Corps de la requête
{ "badge_image": "<image du badge>" }

// Réponse
{ "worker_id": "EMP-042", "name": "Karim Mansouri", "timestamp": "2025-06-26T08:32:00Z" }
```

---

### 📹 Gestion des Caméras

```http
GET  /usine/surveillances/camera/stream   → Flux vidéo en direct
POST /usine/surveillances/camera/record   → Démarrer l'enregistrement
POST /usine/surveillances/camera/connect  → Connecter une caméra
```

---

### 🚨 Gestion des Incidents

```http
POST /usine/incidents/report              → Signaler un incident
GET  /usine/incidents/list                → Lister les incidents
GET  /usine/incidents/{id}/details        → Détails d'un incident
GET  /usine/incidents/analysis            → Analyse globale
```

---

### 👤 Gestion des Utilisateurs

```http
POST /usine/admin/login                   → Connexion administrateur
GET  /usine/admin/dashboard               → Tableau de bord
GET  /usine/workers                       → Liste des travailleurs
POST /usine/workers/register              → Enregistrer un travailleur
GET  /usine/workers/check-in              → Pointage entrée
GET  /usine/workers/check-out             → Pointage sortie
```

---

## ✨ Fonctionnalités

### 🦺 Détection des EPI

Vérification du port de **5 équipements de sécurité** :

| Équipement | Label | Criticité |
|------------|-------|-----------|
| Casque de sécurité | `hard_hat` | 🔴 Obligatoire |
| Gilet de sécurité | `safety_vest` | 🔴 Obligatoire |
| Lunettes de protection | `safety_glasses` | 🟠 Recommandé |
| Gants | `gloves` | 🟠 Recommandé |
| Chaussures de sécurité | `steel_boots` | 🔴 Obligatoire |

**Caractéristiques :**
- Détection multi-personnes en temps réel
- Calcul du taux de conformité global
- Alertes automatiques en cas de non-conformité
- Seuil de confiance élevé (faux-négatifs non acceptés)

---

### 🔥 Détection d'Incendie

- Détection feu et fumée en temps réel via caméras
- Seuil de confiance très élevé (faux-positifs non acceptés)
- Localisation précise par caméra et zone
- Déclenchement d'alertes automatiques
- Enregistrement vidéo de l'incident

---

### 🪪 Reconnaissance de Badges

- Identification des travailleurs à l'entrée/sortie
- Suivi des présences avec horodatage
- Détection des accès non autorisés
- Historique complet des pointages

---

### 📊 Tableau de Bord Administrateur

Indicateurs clés en temps réel :

| Métrique | Description |
|----------|-------------|
| Total travailleurs | Effectif total enregistré |
| Présents sur site | Travailleurs actuellement dans l'usine |
| Incidents du jour | Nombre d'incidents signalés |
| Conformité EPI | Pourcentage de conformité en temps réel |

---

### 🚨 Gestion des Incidents

Chaque incident est documenté avec :
- Formulaire de signalement détaillé
- Classification et niveau de sévérité
- Attribution à un responsable
- Timeline complète de l'incident
- Photos et vidéos associées
- Statut de résolution et commentaires

---

## 🧠 Modèles de Deep Learning

### Modèle PPE (Détection des EPI)

- **Type** : YOLO / CNN personnalisé
- **Entrée** : Image ou frame vidéo
- **Sortie** : Équipements détectés + équipements manquants

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

### Modèle Fire (Détection d'Incendie)

- **Type** : Deep CNN / YOLO
- **Entrée** : Flux vidéo continu
- **Sortie** : Alerte + localisation

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

### Modèle Badge (Reconnaissance)

- **Type** : Deep Learning — OCR ou reconnaissance faciale
- **Entrée** : Image du badge ou visage
- **Sortie** : ID travailleur + horodatage

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

### Chargement des Modèles au Démarrage

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

## 🚀 Exemples d'Utilisation

### 🦺 Flux de Vérification des EPI

```
1. La caméra capture en continu le flux vidéo de la zone de travail
2. Chaque frame est envoyée à /usine/surveillances/analyze
3. Le modèle PPE détecte les équipements portés et manquants
4. En cas de non-conformité, une alerte est déclenchée
5. L'incident est enregistré et assigné à un responsable
```

### 🔥 Flux de Détection d'Incendie

```
1. Les caméras surveillent les zones à risque en continu
2. Chaque frame est analysée par /usine/surveillances/fire
3. En cas de détection, une alerte immédiate est émise
4. La zone et la caméra concernées sont identifiées
5. L'enregistrement vidéo démarre automatiquement
```

### 🪪 Flux de Pointage

```
1. Le travailleur présente son badge à l'entrée
2. L'image est envoyée à /usine/workers/check-in
3. Le modèle Badge identifie le travailleur
4. Le pointage est enregistré avec horodatage
5. L'accès est accordé ou refusé selon les droits
```

---

## 🖥️ Fonctionnalités du Frontend

- 📊 **Tableau de bord** avec métriques de sécurité en temps réel
- 📹 **Flux caméras live** avec overlays de détection
- 🔔 **Alertes instantanées** en cas d'incident ou de non-conformité
- 👷 **Gestion des travailleurs** avec historique de présence
- 📋 **Suivi des incidents** avec timeline et pièces jointes
- 🔐 **Authentification administrateur** sécurisée

---

## 📄 Licence

**MIT License** — Voir le fichier `LICENSE` pour plus de détails.

---

<div align="center">

**Construit avec ❤️ grâce à FastAPI, HTML/JS et des modèles de vision industrielle de pointe**

</div>
