from typing import TypedDict, List
from app.langgraph.models import UserState, LevelProgress, Question
from app.langgraph.prompts import lvl3_prompt_template
from app.core.config import llm
from uuid import uuid4
import json
from langgraph.types import Send, Command, interrupt
from typing import Literal
# Define the LLMInferenceState3 typed dict


class LLMInferenceState3(TypedDict):
    skill: str
    title: str
    company: str
    responsibilities: List[str]
    qualifications: List[str]
    llm_response: str

# Define the SkillWorkerInput3 typed dict


class SkillWorkerInput3(TypedDict):
    skills: List[str]
    title: str
    company: str
    responsibilities: List[str]
    qualifications: List[str]

# lvl3_mcq_generator function


def lvl3_mcq_generator(state: UserState):
    skills = state.job_description.required_skills
    jd = state.job_description
    return {
        "skills": skills,
        "title": jd.title,
        "company": jd.company,
        "responsibilities": jd.responsibilities,
        "qualifications": jd.qualifications,
    }

# llm_lvl3_mcqs function


def llm_lvl3_mcqs(state: LLMInferenceState3) -> Send:
    skill = state["skill"]
    title = state["title"]
    company = state["company"]
    responsibilities = state["responsibilities"]
    qualifications = state["qualifications"]
    prompt = lvl3_prompt_template.format(
        skill=skill,
        title=title,
        company=company,
        responsibilities="\n".join(responsibilities),
        qualifications="\n".join(qualifications),
        num=10
    )
    response = llm.invoke(prompt)

    # Convert the AI message response to a string explicitly
    response_content = str(response.content)

    print(f"LLM Response: {response_content}")
    print(f"Response type: {type(response_content)}")

    return Send(
        "llm_inference_validator3",
        {
            "llm_response": response_content,
            "skill": skill,
            "title": title,
            "company": company,
            "responsibilities": responsibilities,
            "qualifications": qualifications
        }
    )

# assign_lvl3_skill_workers function


def assign_lvl3_skill_workers(state: SkillWorkerInput3):
    return [
        Send("llm_lvl3_mcqs", {
            "skill": s,
            "title": state["title"],
            "company": state["company"],
            "responsibilities": state["responsibilities"],
            "qualifications": state["qualifications"]
        }) for s in state["skills"]
    ]

# lvl3_await_response function


def lvl3_await_response(state: UserState):
    user_response = interrupt("Waiting for the lvl3 msq response")
    return {"lvl3_response": user_response}

# lvl3_mcq_synthesizer function


def lvl3_mcq_synthesizer(state: UserState):
    level_progress = state.progress.get(3)
    mcqs = level_progress.questions
    return {
        "lvl3_generated_mcqs": mcqs,
        "current_stage": "lvl_3_waiting_response"
    }

# llm_inference_validator3 function


def llm_inference_validator3(state: LLMInferenceState3) -> Command[Literal["lvl3_mcq_synthesizer", "llm_lvl3_mcqs"]]:
    try:

        print(f"{state.keys()}")
        llm_response = state["llm_response"]

        lvl3_mcqs = json.loads(llm_response)
        skill = state["skill"]
        title = state["title"]
        company = state["company"]
        responsibilities = state["responsibilities"]
        qualifications = state["qualifications"]

        # Validate lvl3_mcqs is a list
        if not isinstance(lvl3_mcqs, list):
            raise ValueError("Parsed MCQs should be a list")

        # Transform into List[Question]
        questions = []
        for item in lvl3_mcqs:
            question = Question(
                id=str(uuid4()),  # Generate unique id
                text=item.get("question", ""),
                options=item.get("options", []),
                level=3,
                metadata={
                    "skill": skill,
                    "title": title,
                    "company": company,
                    "responsibilities": responsibilities,
                    "qualifications": qualifications,
                    "max_time_required": item.get("max_time_required", 60)
                }
            )
            questions.append(question)

        return Command(
            goto="lvl3_mcq_synthesizer",
            update={
                "progress": {
                    3: LevelProgress(
                        level=3,
                        questions=questions,
                        answers={},
                        score=None,
                        completed=False
                    )
                }
            }
        )

    except Exception as e:
        print(f"Invalid JSON or format error: {e}")
        skill = state["skill"]
        title = state["title"]
        company = state["company"]
        responsibilities = state["responsibilities"]
        qualifications = state["qualifications"]
        return Command(
            update={
                "skill": skill,
                "title": title,
                "company": company,
                "responsibilities": responsibilities,
                "qualifications": qualifications
            },
            goto="llm_lvl3_mcqs"
        )
