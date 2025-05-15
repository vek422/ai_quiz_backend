from typing import Optional
from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db.models import User, Candidate, Recruiter
from app.core.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel
import uuid

router = APIRouter()

# Dependency for async DB session


def get_async_db():
    async def _get_db():
        async with AsyncSessionLocal() as session:
            yield session
    return _get_db


class CandidateRegister(BaseModel):
    email: str
    password: str
    resume_text: Optional[str] = None
    name: str
    phone: str


class RecruiterRegister(BaseModel):
    name: str
    email: str
    password: str
    company: str
    phone: str


class UserLogin(BaseModel):
    email: str
    password: str


@router.post('/candidate/signup')
async def candidate_signup(
        user: CandidateRegister,
        session: AsyncSession = Depends(get_async_db())
):
    result = await session.execute(select(User).filter_by(email=user.email))

    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    uid = str(uuid.uuid4())

    user_obj = User(uid=uid, email=user.email, password_hash=hash_password(
        user.password), role='candidate', name=user.name)

    candidate = Candidate(uid=uid, resume_text=user.resume_text)

    session.add(user_obj)

    session.add(candidate)

    await session.commit()
    return {"msg": "Candidate created successfully", "uid": uid}


@router.post('/recruiter/signup')
async def recruiter_signup(user: RecruiterRegister, session: AsyncSession = Depends(get_async_db())):
    result = await session.execute(select(User).filter_by(email=user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = str(uuid.uuid4())
    user_obj = User(uid=uid, email=user.email, password_hash=hash_password(
        user.password), role='recruiter', name=user.name)
    recruiter = Recruiter(uid=uid,
                          company=user.company, phone=user.phone)
    session.add(user_obj)
    session.add(recruiter)
    await session.commit()
    return {"msg": "Recruiter created successfully", "uid": uid}


@router.post('/login')
async def login(user: UserLogin, session: AsyncSession = Depends(get_async_db())):
    result = await session.execute(select(User).filter_by(email=user.email))
    user_row = result.scalars().first()
    if not user_row or not verify_password(user.password, user_row.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(
        data={"sub": user_row.uid, "role": user_row.role})
    name = user_row.name
    company = None
    resume_text = None
    if user_row.role == 'recruiter':
        rec_result = await session.execute(select(Recruiter).filter_by(uid=user_row.uid))
        recruiter = rec_result.scalars().first()
        company = recruiter.company if recruiter else None
    elif user_row.role == 'candidate':
        can_result = await session.execute(select(Candidate).filter_by(uid=user_row.uid))
        candidate = can_result.scalars().first()
        if candidate:
            print(f"Resume text: {candidate.resume_text}")
        else:
            print("Candidate not found")
        resume_text = candidate.resume_text if candidate else None
    return {
        "token": token,
        "token_type": "bearer",
        "user": {
            "uid": user_row.uid,
            "role": user_row.role,
            "email": user_row.email,
            "name": name,
            "company": company,
            "resume_text": resume_text
        }
    }

# CRUD endpoints for candidate and recruiter profiles


class CandidateProfileUpdate(BaseModel):
    resume_text: Optional[str] = None


class RecruiterProfileUpdate(BaseModel):
    name: Optional[str]
    company: Optional[str]
    phone: Optional[str]


@router.get('/candidate/profile')
async def get_candidate_profile(uid: str, session: AsyncSession = Depends(get_async_db())):
    result = await session.execute(select(Candidate).filter_by(uid=uid))
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    user_result = await session.execute(select(User).filter_by(uid=uid))
    user = user_result.scalars().first()

    return {
        "uid": candidate.uid,
        "email": user.email if user else None,
        "resume_text": candidate.resume_text
    }


@router.put('/candidate/profile')
async def update_candidate_profile(uid: str, update: CandidateProfileUpdate, session: AsyncSession = Depends(get_async_db())):
    result = await session.execute(select(Candidate).filter_by(uid=uid))
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if update.resume_text is not None:
        candidate.resume_text = update.resume_text
    await session.commit()
    return {"msg": "Candidate profile updated"}


@router.get('/recruiter/profile')
async def get_recruiter_profile(uid: str, session: AsyncSession = Depends(get_async_db())):
    result = await session.execute(select(Recruiter).filter_by(uid=uid))
    recruiter = result.scalars().first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return {"uid": recruiter.uid, "name": recruiter.name, "company": recruiter.company, "phone": recruiter.phone}


@router.put('/recruiter/profile')
async def update_recruiter_profile(uid: str, update: RecruiterProfileUpdate, session: AsyncSession = Depends(get_async_db())):
    result = await session.execute(select(Recruiter).filter_by(uid=uid))
    recruiter = result.scalars().first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    if update.name:
        recruiter.name = update.name
    if update.company:
        recruiter.company = update.company
    if update.phone:
        recruiter.phone = update.phone
    await session.commit()
    return {"msg": "Recruiter profile updated"}


@router.delete('/recruiter/profile')
async def delete_recruiter_profile(uid: str, session: AsyncSession = Depends(get_async_db())):
    rec_result = await session.execute(select(Recruiter).filter_by(uid=uid))
    recruiter = rec_result.scalars().first()
    user_result = await session.execute(select(User).filter_by(uid=uid))
    user = user_result.scalars().first()
    if not recruiter or not user:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    await session.delete(recruiter)
    await session.delete(user)
    await session.commit()
    return {"msg": "Recruiter deleted"}
