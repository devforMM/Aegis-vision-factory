FROM python:3.10-slim

# 1. Installer les dépendances système ET Redis pour Celery
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# 2. Définir le dossier racine
WORKDIR /app

# 3. Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copier tout le projet
COPY . .

# 5. Se placer dans le dossier back-end pour exécuter les commandes
WORKDIR /app/back-end

# 6. Donner les droits d'exécution au script Bash
RUN chmod +x start.sh

# 7. Exposer le port de Hugging Face
EXPOSE 7860

# 8. Lancer le script qui va démarrer Redis, Celery et FastAPI
CMD ["./start.sh"]