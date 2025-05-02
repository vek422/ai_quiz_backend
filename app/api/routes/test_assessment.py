from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.security import get_current_user
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Test, CandidateAssessment, Recruiter, Candidate, User
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime
import csv
from app.core.security import hash_password
import secrets
from app.core.email_service import send_candidate_onboarding_email
from fastapi import BackgroundTasks
import requests
import tempfile
from pdf2image import convert_from_path
from PIL import Image
from app.langgraph.llm_config import llm

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Recruiter Test Management ---
class TestCreate(BaseModel):
    title: str
    jd_text: str
    scheduled_end: Optional[datetime] = None
    scheduled_start: Optional[datetime] = None

class TestUpdate(BaseModel):
    title: Optional[str]
    jd_text: Optional[str]
    scheduled_end: Optional[datetime] = None
    scheduled_start: Optional[datetime] = None

@router.post('/recruiter/test')
def create_test(test: TestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(current_user.role)
    print(current_user.email)
    if current_user.role != 'recruiter':
        raise HTTPException(status_code=403, detail="Only recruiters can create tests")
    recruiter_uid = current_user.uid
    if not db.query(Recruiter).filter_by(uid=recruiter_uid).first():
        raise HTTPException(status_code=404, detail="Recruiter not found")
    test_id = str(uuid.uuid4())
    now = datetime.utcnow()
    test_obj = Test(
        test_id=test_id,
        recruiter_uid=recruiter_uid,
        title=test.title,
        jd_text=test.jd_text,
        scheduled_end=test.scheduled_end,
        scheduled_start=test.scheduled_start,
        created_at=now,
        updated_at=now
    )
    db.add(test_obj)
    db.commit()
    return {"msg": "Test created", "test_id": test_id}

@router.get('/recruiter/tests')
def list_recruiter_tests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != 'recruiter':
        raise HTTPException(status_code=403, detail="Only recruiters can view tests")
    tests = db.query(Test).filter_by(recruiter_uid=current_user.uid).all()
    result = []
    for t in tests:
        total_candidates = db.query(CandidateAssessment).filter_by(test_id=t.test_id).count()
        duration = None
        if t.scheduled_start and t.scheduled_end:
            duration = (t.scheduled_end - t.scheduled_start).total_seconds() // 60  # duration in minutes
        result.append({
            "test_id": t.test_id,
            "title": t.title,
            "jd_text": t.jd_text,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "scheduled_end": t.scheduled_end,
            "scheduled_start": t.scheduled_start,
            "total_candidates": total_candidates,
            "duration_minutes": duration
        })
    return result

@router.put('/recruiter/test/{test_id}')
def update_test(test_id: str, update: TestUpdate, db: Session = Depends(get_db)):
    test = db.query(Test).filter_by(test_id=test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if update.title:
        test.title = update.title
    if update.jd_text:
        test.jd_text = update.jd_text
    if update.scheduled_end is not None:
        test.scheduled_end = update.scheduled_end
    if update.scheduled_start is not None:
        test.scheduled_start = update.scheduled_start
    test.updated_at = datetime.utcnow()
    db.commit()
    return {"msg": "Test updated"}

@router.delete('/recruiter/test/{test_id}')
def delete_test(test_id: str, db: Session = Depends(get_db)):
    test = db.query(Test).filter_by(test_id=test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    db.delete(test)
    db.commit()
    return {"msg": "Test deleted"}

from typing import List
from pydantic import BaseModel

class CandidateInput(BaseModel):
    name: str
    email: str
    phone: str
    resume_link: str

@router.post('/recruiter/test/{test_id}/add_candidates')
def add_candidates_json(test_id: str, candidates: List[CandidateInput], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    test = db.query(Test).filter_by(test_id=test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if current_user.role != 'recruiter' or test.recruiter_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to add candidates for this test")
    results = []
    for candidate_input in candidates:
        name = candidate_input.name
        email = candidate_input.email
        phone = candidate_input.phone
        resume_link = candidate_input.resume_link
        user = db.query(User).filter_by(email=email).first()
        password = None
        created = False
        if not user:
            uid = str(uuid.uuid4())
            password = secrets.token_urlsafe(8)
            test_link = 'test link'
            try:
                send_candidate_onboarding_email(name, email, password, test.title, resume_link, test_link)
            except Exception as e:
                results.append({"name": name, "email": email, "created": False, "password": password, "error": str(e)})
                continue  # Skip DB commit for this candidate
            user = User(uid=uid, email=email, password_hash=hash_password(password), role='candidate')
            candidate = Candidate(uid=uid, name=name, phone=phone, resume_link=resume_link)
            db.add(user)
            db.add(candidate)
            created = True
        else:
            candidate = db.query(Candidate).filter_by(uid=user.uid).first()
            if candidate:
                candidate.resume_link = resume_link
                candidate.phone = phone
            else:
                candidate = Candidate(uid=user.uid, name=name, phone=phone, resume_link=resume_link)
                db.add(candidate)
        assessment = db.query(CandidateAssessment).filter_by(candidate_uid=candidate.uid, test_id=test_id).first()
        if not assessment:
            assessment_id = str(uuid.uuid4())
            assessment = CandidateAssessment(assessment_id=assessment_id, candidate_uid=candidate.uid, test_id=test_id)
            db.add(assessment)
        results.append({
            "name": name,
            "email": email,
            "created": created,
            "password": password,
            "resume_link": resume_link
        })
    db.commit()
    return {"candidates": results}

# --- Candidate Assessment Management ---
@router.get('/candidate/tests')
def list_available_tests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    # Fetch tests for which the current user (candidate) has an assessment
    assessments = db.query(CandidateAssessment).filter_by(candidate_uid=current_user.uid).all()
    test_ids = [a.test_id for a in assessments]
    tests = db.query(Test).filter(Test.test_id.in_(test_ids)).all()
    return [{
        "test_id": t.test_id,
        "title": t.title,
        "jd_text": t.jd_text,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "scheduled_end": t.scheduled_end,
        "scheduled_start": t.scheduled_start
    } for t in tests]

def extract_text_from_pdf(pdf_url: str) -> str:
    # Download PDF
    response = requests.get(pdf_url)
    response.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
        tmp_pdf.write(response.content)
        tmp_pdf.flush()
        # Convert PDF to images
        images = convert_from_path(tmp_pdf.name)
    # OCR each image using LLM (simulate with LLM prompt)
    all_text = []
    for img in images:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
            img.save(tmp_img.name)
            # You could use an OCR library, but as per prompt, use LLM
            prompt = f"Extract all relevant resume details from this image. Return as plain text. (Assume image is base64-encoded)"
            with open(tmp_img.name, "rb") as f:
                img_bytes = f.read()
            # In practice, you would encode to base64 and send to LLM if it supports vision
            # Here, just simulate with a placeholder
            text = llm.invoke(prompt)  # Replace with actual vision LLM call if available
            all_text.append(text.content if hasattr(text, 'content') else str(text))
    return "\n".join(all_text)

def extract_jd_fields(jd_text: str) -> dict:
    prompt = f"""
    Extract the following fields from this job description text:\n\n{jd_text}\n\nFields: position, required_skills (list), experience_level. Return as JSON."
    """
    result = llm.invoke(prompt)
    import json
    try:
        return json.loads(result.content)
    except Exception:
        return {}

@router.post('/candidate/assessment/start')
def start_assessment(candidate_uid: str, test_id: str, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    # Fetch candidate and test
    candidate = db.query(Candidate).filter_by(uid=candidate_uid).first()
    test = db.query(Test).filter_by(test_id=test_id).first()
    if not candidate or not test:
        raise HTTPException(status_code=404, detail="Candidate or Test not found")
    # Download and parse resume
    resume_text = extract_text_from_pdf(candidate.resume_link)
    # Parse JD fields
    jd_fields = extract_jd_fields(test.jd_text)
    # Build initial state
    from app.langgraph.state import UserState
    initial_state = UserState(
        assessment_id=str(uuid.uuid4()),
        user_id=candidate_uid,
        current_level=1,
        progress={},
        resume_text=resume_text,
        jd_fields=jd_fields
    )
    # Save state in checkpointer (memory)
    from app.langgraph.graph import main_workflow
    main_workflow.checkpointer.put(initial_state.assessment_id, initial_state)
    return {"assessment_id": initial_state.assessment_id, "current_level": 1, "resume_text": resume_text, "jd_fields": jd_fields}

@router.get('/candidate/assessments')
def list_candidate_assessments(candidate_uid: str, db: Session = Depends(get_db)):
    assessments = db.query(CandidateAssessment).filter_by(candidate_uid=candidate_uid).all()
    return [{"assessment_id": a.assessment_id, "test_id": a.test_id, "started_at": a.started_at, "updated_at": a.updated_at} for a in assessments]
