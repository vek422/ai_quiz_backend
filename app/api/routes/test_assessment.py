from langgraph.types import Command
import json
from app.langgraph.other.parse_resume import parse_resume
from typing import List
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.langgraph.models import userstate_initializer, JobDescription, Resume
from app.db.models import Test, CandidateAssessment,  Candidate, User
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime
import csv
from app.core.security import hash_password
from app.core.security import generate_password
from app.db.database import get_db
from app.worker.queue import enqueue_resume_task
from app.langgraph.other.parse_jd import parse_jd
from app.langgraph.graph.main import main_graph
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# Use async session for async endpoints
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


class CreateTestInput(BaseModel):
    title: str
    jd_text: str = None
    scheduled_start: datetime = None
    scheduled_end: datetime = None


@router.post("/create-test")
async def create_test(
    test_input: CreateTestInput,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):

    if not user.role == "recruiter":
        raise HTTPException(
            status_code=403, detail="Not authorized to create tests")

    # process the jd_text
    parsed_jd = parse_jd(test_input.jd_text)
    print(parsed_jd)
    if not parsed_jd:
        raise HTTPException(
            status_code=400, detail="JD text is not valid or empty")
    #
    # Step 2: Create Test entry
    test = Test(
        test_id=str(uuid.uuid4()),
        recruiter_uid=user.uid,
        title=test_input.title,
        jd_text=parsed_jd,
        scheduled_start=test_input.scheduled_start,
        scheduled_end=test_input.scheduled_end,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(test)
    await session.commit()

    return {
        "message": "Test created successfully",
        "test_id": test.test_id,
    }


@router.get('/recruiter/tests')
async def list_recruiter_tests(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != 'recruiter':
        raise HTTPException(
            status_code=403, detail="Only recruiters can view tests")
    tests = await db.execute(select(Test).filter_by(recruiter_uid=current_user.uid))
    tests = tests.scalars().all()
    result = []
    for t in tests:
        total_candidates = await db.execute(select(CandidateAssessment).filter_by(test_id=t.test_id))
        total_candidates = total_candidates.scalars().all()
        total_candidates = len(total_candidates)
        duration = None
        if t.scheduled_start and t.scheduled_end:
            # duration in minutes
            duration = (t.scheduled_end -
                        t.scheduled_start).total_seconds() // 60
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


@router.get('/candidate/tests')
async def list_candidate_tests(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != 'candidate':
        raise HTTPException(
            status_code=403, detail="Only candidates can view tests")

    assessments = await db.execute(select(CandidateAssessment).filter_by(candidate_uid=current_user.uid))
    assessments = assessments.scalars().all()
    result = []
    for assessment in assessments:
        test = await db.execute(select(Test).filter_by(test_id=assessment.test_id))
        test = test.scalar_one_or_none()
        if not test:
            continue

        result.append({
            "test_id": test.test_id,
            "title": test.title,
            "jd_text": test.jd_text,
            "created_at": test.created_at,
            "assessment_id": assessment.assessment_id,
            "status": assessment.status,
            "scheduled_end": test.scheduled_end,
            "scheduled_start": test.scheduled_start,

        })
    return result


@router.put('/recruiter/test/{test_id}')
async def update_test(test_id: str, update: TestUpdate, db: AsyncSession = Depends(get_db)):
    test = await db.execute(db.query(Test).filter_by(test_id=test_id)).first()
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
    await db.commit()
    return {"msg": "Test updated"}


@router.delete('/recruiter/test/{test_id}')
async def delete_test(test_id: str, db: AsyncSession = Depends(get_db)):
    test = await db.execute(db.query(Test).filter_by(test_id=test_id)).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    await db.delete(test)
    await db.commit()
    return {"msg": "Test deleted"}


class CandidateInput(BaseModel):
    email: str
    resume_link: str


@router.post('/{test_id}/add-candidates')
async def add_candidates(
    test_id: str,
    candidates: List[CandidateInput],
    session: AsyncSession = Depends(get_db),
):
    # Step 1: Check if Test exists
    test = await session.execute(select(Test).where(Test.test_id == test_id))
    test = test.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    created_or_updated_candidates = []

    for candidate_data in candidates:
        # Step 1: Check if User already exists
        query = await session.execute(select(User).where(User.email == candidate_data.email))
        existing_user = query.scalar_one_or_none()

        if existing_user:
            candidate_uid = existing_user.uid

            query_candidate = await session.execute(select(Candidate).where(Candidate.uid == candidate_uid))
            candidate_profile = query_candidate.scalar_one_or_none()

            if not candidate_profile:
                raise HTTPException(
                    status_code=400, detail=f"Candidate profile missing for {candidate_data.email}")

            # Use the async function version
            await enqueue_resume_task(candidate_uid=candidate_uid, resume_link=candidate_data.resume_link)

            candidate_info = {
                "email": candidate_data.email,
                "candidate_uid": candidate_uid,
                "is_new_user": False
            }

        else:
            # New candidate
            random_password = generate_password()
            user = User(
                uid=str(uuid.uuid4()),
                email=candidate_data.email,
                password_hash=hash_password(random_password),
                role="candidate",
                name=candidate_data.email.split(
                    '@')[0],  # Default name from email
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(user)
            await session.flush()

            candidate = Candidate(
                uid=user.uid,
                resume_text="Waiting for resume parsing",
                created_at=datetime.utcnow()
            )
            session.add(candidate)

            # Use the async function version
            await enqueue_resume_task(candidate_uid=user.uid, resume_link=candidate_data.resume_link)

            candidate_uid = user.uid

            candidate_info = {
                "email": candidate_data.email,
                "candidate_uid": candidate_uid,
                "is_new_user": True,
                "password": random_password  # Include password for new users for testing purposes
            }

        # Step 2: Create CandidateAssessment entry
        assessment = CandidateAssessment(
            assessment_id=str(uuid.uuid4()),
            candidate_uid=candidate_uid,
            test_id=test_id,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status="not_started"
        )
        session.add(assessment)

        candidate_info["assessment_id"] = assessment.assessment_id
        created_or_updated_candidates.append(candidate_info)

    await session.commit()

    return {
        "message": f"{len(created_or_updated_candidates)} candidates processed",
        "candidates": created_or_updated_candidates
    }


# candidate


@router.post('/candidate/test/{test_id}/start')
async def start_test(test_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    test = await db.execute(
        select(Test).where(Test.test_id == test_id)
    )
    test = test.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Check if the candidate has an assessment for this test
    assessment = await db.execute(
        select(CandidateAssessment).where(
            CandidateAssessment.test_id == test_id,
            CandidateAssessment.candidate_uid == current_user.uid
        )
    )
    assessment = assessment.scalar_one_or_none()
    # Check if the assessment is already in progress or completed
    if not assessment:
        raise HTTPException(
            status_code=404, detail="Candidate assessment not found")

    # check if the assessment started or not
    # if assessment.status == "in_progress":
    #     raise HTTPException(
    #         status_code=400, detail="Assessment already in progress")
    # if assessment.status == "completed":
    #     raise HTTPException(
    #         status_code=400, detail="Assessment already completed")

    candidate = await db.execute(select(Candidate).where(
        Candidate.uid == current_user.uid
    ))
    candidate = candidate.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=404, detail="Candidate profile not found")
    candidate_resume = candidate.resume_text
    parsed_jd = json.loads(test.jd_text)
    parsed_resume = json.loads(candidate_resume)

    config = {
        "thread_id": assessment.assessment_id,
    }
    userState = userstate_initializer()
    userState.user_id = current_user.uid
    userState.job_description = JobDescription(
        required_skills=parsed_jd.get("required_skills"),
        title=parsed_jd.get("title"),
        company=parsed_jd.get("company"),
        responsibilities=parsed_jd.get("responsibilities"),
        qualifications=parsed_jd.get("qualifications"),
        description=parsed_jd.get("description")
    )
    userState.resume = Resume(
        skills=parsed_resume.get("skills"),
        education=parsed_resume.get("education"),
        experience=parsed_resume.get("experience"),
        projects=parsed_resume.get("projects"),
        certifications=parsed_resume.get("certifications"),
        summary=parsed_resume.get("summary")
    )

    # get the questio
    # n for the test from langraph
    questions = main_graph.invoke(
        userState,
        config=config,
    )

    # Start the test
    # update the status of the assessment
    assessment.status = "in_progress"
    assessment.started_at = datetime.utcnow()
    await db.commit()
    return {"message": "Test started", "test_id": test_id, "questions": questions}


@router.post("/candidate/test/{test_id}/level/{level}/submit")
async def submit_level1_test(
    test_id: str,
    level: int,
    answers: List[dict[str, str]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if the candidate has an assessment for this test
    assessment = await db.execute(
        select(CandidateAssessment).where(
            CandidateAssessment.test_id == test_id,
            CandidateAssessment.candidate_uid == current_user.uid
        )
    )
    assessment = assessment.scalar_one_or_none()
    if not assessment:
        raise HTTPException(
            status_code=404, detail="Candidate assessment not found")

    # Check if the assessment is already completed
    if assessment.status == "completed":
        raise HTTPException(
            status_code=400, detail="Assessment already completed")

    # get the state from the checkpointer
    config = {
        "thread_id": assessment.assessment_id,
    }
    state = main_graph.get_state(config=config)
    if not state:
        raise HTTPException(
            status_code=404, detail="State not found for this assessment")

    #  check the current stage
    current_level = state.values.get("current_level")
    if (current_level != level):
        raise HTTPException(
            status_code=400, detail=f"Current level is {current_level}, not {level}")

    # invoke the graph with updated answers
    result = main_graph.invoke(
        Command(resume=answers, config=config)
    )
    print(result)
    return {"message": "Level 1 test submitted", "result": result}
    # Update the answers in the database
