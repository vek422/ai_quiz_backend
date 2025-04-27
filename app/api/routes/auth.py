from fastapi import APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Candidate, LoginDetail
from app.core.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel
import uuid

router = APIRouter()


class UserRegister(BaseModel):
    name:str
    email:str
    password:str
    phone:str
class UserLogin(BaseModel):
    email:str
    password:str

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

@router.post('/signup')
def signup(user:UserRegister,db:Session = Depends(get_db)):
    uid = str(uuid.uuid4())
    if db.query(LoginDetail).filter_by(email=user.email).first():
        raise HTTPException(status_code=400,detail="Email Already registered")
    
    candidate = Candidate(uid=uid, name=user.name, email=user.email,  phone=user.phone)
    login = LoginDetail(uid=uid, password=hash_password(user.password), email=user.email)
    
    db.add(candidate)
    db.add(login)
    db.commit()
    return {"msg":"User created Successfully","uid":uid}

@router.post('/login')
def login(user:UserLogin,db:Session = Depends(get_db)):
    user_row = db.query(LoginDetail).filter_by(email=user.email).first()
    if not user or not verify_password(user.password,user_row.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(data={"sub": user_row.uid})
    return {"access_token": token, "token_type": "bearer"}



