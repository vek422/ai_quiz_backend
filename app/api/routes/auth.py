from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User, Candidate, Recruiter
from app.core.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel
import uuid

router = APIRouter()

class CandidateRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    resume_link: str 

class RecruiterRegister(BaseModel):
    name: str
    email: str
    password: str
    company: str
    phone: str

class UserLogin(BaseModel):
    email: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/candidate/signup')
def candidate_signup(user: CandidateRegister, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = str(uuid.uuid4())
    user_obj = User(uid=uid, email=user.email, password_hash=hash_password(user.password), role='candidate')
    candidate = Candidate(uid=uid, name=user.name, phone=user.phone,resume_link=user.resume_link)
    db.add(user_obj)
    db.add(candidate)
    db.commit()
    return {"msg": "Candidate created successfully", "uid": uid}

@router.post('/recruiter/signup')
def recruiter_signup(user: RecruiterRegister, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = str(uuid.uuid4())
    user_obj = User(uid=uid, email=user.email, password_hash=hash_password(user.password), role='recruiter')
    recruiter = Recruiter(uid=uid, name=user.name, company=user.company, phone=user.phone)
    db.add(user_obj)
    db.add(recruiter)
    db.commit()
    return {"msg": "Recruiter created successfully", "uid": uid}

@router.post('/login')
def login(user: UserLogin, db: Session = Depends(get_db)):
    user_row = db.query(User).filter_by(email=user.email).first()
    if not user_row or not verify_password(user.password, user_row.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(data={"sub": user_row.uid, "role": user_row.role})
    return {
        "token": token, 
        "token_type": "bearer", 
        "user": {
            "uid": user_row.uid, 
            "role": user_row.role, 
            "email": user_row.email,
            "name": user_row.candidate.name if user_row.role == 'candidate' else user_row.recruiter.name,
            "company": user_row.recruiter.company if user_row.role == 'recruiter' else None,
        }
    }

# CRUD endpoints for candidate and recruiter profiles
from fastapi import status
from typing import Optional

class CandidateProfileUpdate(BaseModel):
    name: Optional[str]
    phone: Optional[str]

class RecruiterProfileUpdate(BaseModel):
    name: Optional[str]
    company: Optional[str]
    phone: Optional[str]

@router.get('/candidate/profile')
def get_candidate_profile(uid: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter_by(uid=uid).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"uid": candidate.uid, "name": candidate.name, "phone": candidate.phone}

@router.put('/candidate/profile')
def update_candidate_profile(uid: str, update: CandidateProfileUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter_by(uid=uid).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if update.name:
        candidate.name = update.name
    if update.phone:
        candidate.phone = update.phone
    db.commit()
    return {"msg": "Candidate profile updated"}


@router.get('/recruiter/profile')
def get_recruiter_profile(uid: str, db: Session = Depends(get_db)):
    recruiter = db.query(Recruiter).filter_by(uid=uid).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return {"uid": recruiter.uid, "name": recruiter.name, "company": recruiter.company, "phone": recruiter.phone}

@router.put('/recruiter/profile')
def update_recruiter_profile(uid: str, update: RecruiterProfileUpdate, db: Session = Depends(get_db)):
    recruiter = db.query(Recruiter).filter_by(uid=uid).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    if update.name:
        recruiter.name = update.name
    if update.company:
        recruiter.company = update.company
    if update.phone:
        recruiter.phone = update.phone
    db.commit()
    return {"msg": "Recruiter profile updated"}

@router.delete('/recruiter/profile')
def delete_recruiter_profile(uid: str, db: Session = Depends(get_db)):
    recruiter = db.query(Recruiter).filter_by(uid=uid).first()
    user = db.query(User).filter_by(uid=uid).first()
    if not recruiter or not user:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    db.delete(recruiter)
    db.delete(user)
    db.commit()
    return {"msg": "Recruiter deleted"}



