from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Router imports
from routes.admin_routes import admin_router
from routes.incidents_routes import incidents_router
from routes.surveillance_routes import surveillances_router
from routes.workers_routes import workers_routes

# Deep learning models loader
from deep_learning.functions import get_models

app = FastAPI()



# ==============================================================================
# ROUTER REGISTRATION
# ==============================================================================
app.include_router(admin_router, prefix="/factory/admin")
app.include_router(surveillances_router, prefix="/factory/surveillance")
app.include_router(workers_routes, prefix="/factory/workers")
app.include_router(incidents_router, prefix="/factory/incidents")


# Mount static asset directories
app.mount("/", StaticFiles(directory="."), name="static")


# ==============================================================================
# STARTUP EVENT LIFECYCLE
# ==============================================================================

@app.on_event("startup")
def load_models():
    """
    FastAPI startup hook executing asynchronous initialization loops.
    Loads deep learning weights securely into core application state memory spaces.
    """
    try:
        models = get_models()
        app.state.ppe_model = models["ppe_model"]
        app.state.fire_model = models["fire_model"]
        print("✅ All AI models have been loaded successfully")
        
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        raise RuntimeError(f"Critical error occurred while loading deep learning models: {e}")
    


@app.get("/hello")
def hello():
    return {
        "message":"hello"
    }