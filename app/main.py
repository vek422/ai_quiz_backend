from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.api.routes import auth
from app.api.routes import test_assessment
import threading
from app.worker.queue import start_worker


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix='/auth', tags=["Auth"])
app.include_router(test_assessment.router, prefix='/test', tags=["Test"])

# Start the worker in a separate thread
worker_thread = threading.Thread(target=start_worker, daemon=True)
worker_thread.start()
