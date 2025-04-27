from typing_extensions import TypedDict
from pydantic import BaseModel,Field
from typing import TypedDict, List, Dict, Literal,Annotated

from pydantic import BaseModel, Field
import uuid
def merge_dicts(a: dict[str, list], b: dict[str, list]) -> dict[str, list]:
    result = a.copy()
    for key, value in b.items():
        if key in result:
            result[key] += value
        else:
            result[key] = value
    return result


# -----------------------
# Reusable Models
# -----------------------

class Project(BaseModel):
    name: str
    description: List[str]

class Experience(BaseModel):
    role: str
    company: str
    duration: str
    technologies: List[str]

class TechnicalDetail(BaseModel):
    projects: List[str] = []
    subtopics: List[str] = []
    jd_mentions: List[str] = []

class JobDescription(BaseModel):
    position: str = ""
    required_skills: List[str] = []
    experience_level: str = ""

class ResumeJDState(BaseModel):
    personal_info: Dict[str, str] = Field(default_factory=lambda: {"email": "", "name": ""})
    projects: List[Project] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    job_description: JobDescription = Field(default_factory=JobDescription)
    technical_details:Dict[str,TechnicalDetail]
    technical_skills:List[str] # list of skills with descending priority

# MCQ structure for questions
class MCQ(TypedDict):
    question_id: str
    question: str
    options: List[str]
    answer: str

# -----------------------
# Global Assessment State
# -----------------------

class State(TypedDict):
    # --- Session / endpoint metadata ---
    assessment_id: str             # uuid4 per candidate session
    user_id: str                   # from JWT sub
    unlocked_level: Literal[1, 2, 3]
    
    # --- Compiled Resume + JD context ---
    resume_jd_compiled: ResumeJDState

    
    jd_prioritized_skills: List[str] # fixed length (e.g., top 5)
    technical_details: Dict[str, TechnicalDetail] # one key per skill in jd_prioritized_skills

    # --- Per-level MCQs, answers & pass flags ---
    level1_generated_mcqs:Annotated[Dict[str, List[MCQ]],merge_dicts]
    level1_answers: Dict[str, str]                  
    level1_score:Dict[str,list]
    level1_passed: bool

    level2_generated_mcqs: Annotated[Dict[str, List[MCQ]],merge_dicts]
    level2_answers: Dict[str, str]
    level2_score:Dict[str,list]
    level2_passed: bool

    level3_generated_mcqs: Annotated[Dict[str, List[MCQ]],merge_dicts]
    level3_answers: Dict[str, str]
    level3_score:Dict[str,list]
    level3_passed: bool

# -----------------------
# Helper to initialize a fresh state
# -----------------------

def create_initial_state(user_id: str, resume_jd: ResumeJDState) -> State:
    """
    - user_id: from JWT
    - resume_jd: output of your compile Resume+JD chain
    """
    aid = str(uuid.uuid4())
    # prepare empty TechnicalDetail for each skill
    
    return State(
        assessment_id=aid,
        user_id=user_id,
        unlocked_level=1,
        current_stage="level1_questions",
        resume_jd_compiled=resume_jd,
        technical_details={},
        level1_generated_mcqs={},
        level1_answers={},
        level1_passed=False,
        level2_generated_mcqs={},
        level2_answers={},
        level2_passed=False,
        level3_generated_mcqs={},
        level3_answers={},
        level3_passed=False,
    )


class LLMInferenceState(TypedDict):
  skill:str
  llm_response:str

