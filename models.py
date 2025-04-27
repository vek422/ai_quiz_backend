from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class Question(BaseModel):
    id: str
    text: str
    options: List[str]
    level: int
    metadata: Optional[dict] = None

class LevelProgress(BaseModel):
    level: int
    questions: List[Question]
    answers: Dict[str, Any]  # question_id -> answer
    score: Optional[float] = None
    completed: bool = False
    current_question: Optional[Question] = None  # for interactive/progressive levels

class Resume(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    education: List[str]
    experience: List[str]
    skills: List[str]
    certifications: Optional[List[str]] = None
    summary: Optional[str] = None
    # Add more fields as needed

class JobDescription(BaseModel):
    title: str
    company: str
    required_skills: List[str]
    responsibilities: List[str]
    qualifications: Optional[List[str]] = None
    description: Optional[str] = None
    # Add more fields as needed

class UserState(BaseModel):
    user_id: str
    job_description: JobDescription
    resume: Resume
    current_level: int
    unlocked_levels: List[int]
    progress: Dict[int, LevelProgress]  # level -> LevelProgress

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
