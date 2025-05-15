from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from typing_extensions import Annotated
import operator


class Question(BaseModel):
    id: str
    text: str
    options: List[str]
    correct_answer: Optional[str]
    level: int
    metadata: Optional[dict] = None


class LevelProgress(BaseModel):
    level: int
    questions: Annotated[List[Question], operator.add]
    answers: Dict[str, Any]  # question_id -> answer
    score: Optional[float] = None
    completed: bool = False


class Resume(BaseModel):
    education: List[str]
    experience: List[str]
    skills: List[str]
    projects: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    summary: Optional[str] = None


def merge_progress_dicts(a: Dict[int, LevelProgress], b: Dict[int, LevelProgress]) -> Dict[int, LevelProgress]:
    result = a.copy()
    for level, progress_b in b.items():
        if level in result:
            progress_a = result[level]
            # Merge questions and answers
            progress_a.questions += progress_b.questions
            progress_a.answers.update(progress_b.answers)
            # Handle score and completed carefully (could customize this)
            if progress_b.score is not None:
                progress_a.score = progress_b.score
            if progress_b.completed:
                progress_a.completed = True
        else:
            result[level] = progress_b
    return result


class JobDescription(BaseModel):
    title: str
    company: str
    required_skills: List[str]
    responsibilities: List[str]
    qualifications: Optional[List[str]] = None
    description: Optional[str] = None


class UserState(BaseModel):
    user_id: str
    job_description: JobDescription
    resume: Resume
    current_level: int
    unlocked_levels: List[int]
    progress: Annotated[Dict[int, LevelProgress],
                        merge_progress_dicts]  # level -> LevelProgress


class GenerateResponse(BaseModel):
    questions: List[Question]


class SubmitRequest(BaseModel):
    answers: Dict[str, Any]  # question_id -> answer


class SubmitResponse(BaseModel):
    evaluation: Dict[str, Any]
    next_instructions: Optional[str] = None


class StateResponse(BaseModel):
    current_level: int
    unlocked_levels: List[int]
    progress: Dict[int, LevelProgress]


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def userstate_initializer(data: Optional[dict] = None) -> UserState:
    """Initialize UserState if none provided."""
    if data is None:
        # Create a default UserState
        return UserState(
            user_id="",
            job_description=JobDescription(
                title="",
                company="",
                required_skills=[],
                responsibilities=[],
                qualifications=[],
                description=""
            ),
            resume=Resume(
                education=[],
                experience=[],
                skills=[],
                projects=[],
                certifications=[],
                summary=""
            ),
            current_level=1,
            unlocked_levels=[1],
            progress={}
        )
    return UserState(**data)
