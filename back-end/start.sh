#!/bin/bash

# 1. Démarrer Redis en arrière-plan (le broker pour Celery)
redis-server --daemonize yes

# 2. Démarrer le worker Celery en arrière-plan (le & à la fin est super important)
python -m celery -A server.celery_script worker --pool=solo --loglevel=info &

# 3. Démarrer FastAPI en premier plan sur le port imposé par Hugging Face (7860)
uvicorn server.server:app --host 0.0.0.0 --port 7860