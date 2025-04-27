from fastapi import FastAPI

from app.db.database import Base,engine
from app.api.routes import auth

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router,prefix='/auth',tags=["Auth"])