from app.langgraph.models import Question, UserState, LevelProgress
from typing import TypedDict, Literal
from langgraph.types import Send, Command, interrupt
from app.langgraph.prompts import lvl2_prompt_template
from app.core.config import llm
import json
from uuid import uuid4


class LLMInferenceState(TypedDict):
    skill: str
    llm_response: str
    projects: list[str]
    experience: list[str]


class SkillWorkerState(TypedDict):
    skills: list[str]
    projects: list[str]
    experience: list[str]


def lvl2_mcq_generator(userState: UserState):
    userState.current_level = 2
    userState.unlocked_levels.append(2)
    return userState


def assign_lvl2_skill_workers(userState: UserState):
    # Assign workers for level 2
    skills = userState.job_description.required_skills
    projects = userState.resume.projects or []
    experience = userState.resume.experience or []
    return [Send("llm_lvl2_mcqs", {
        "skill": s,
        "projects": projects,
        "experience": experience
    }) for s in skills]


def llm_lvl2_mcqs(state: SkillWorkerState) -> SkillWorkerState:
    skill = state["skill"]
    projects = state["projects"]
    experience = state["experience"]
    prompt = lvl2_prompt_template.format(
        skill=skill, projects=projects, experience=experience, num=5)

    response = llm.invoke(prompt)
    return Send("llm_inference_validator", {
        "skill": skill,
        "llm_response": response.content,
        "projects": projects,
        "experience": experience
    })


def llm_inference_validator(state: LLMInferenceState) -> Command[Literal["lvl2_mcq_synthesizer", "llm_lvl2_mcqs"]]:
    try:
        lvl2_mcqs = json.loads(state["llm_response"])
        skill = state["skill"]
        projects = state["projects"]
        experience = state["experience"]

        # Validate lvl2_mcqs is a list
        if not isinstance(lvl2_mcqs, list):
            raise ValueError("Parsed MCQs should be a list")

        # Transform into List[Question]
        questions = []
        for item in lvl2_mcqs:
            question = Question(
                id=str(uuid4()),  # Generate unique id
                text=item.get("question", ""),
                options=item.get("options", []),
                level=2,
                metadata={
                    "skill": skill,
                    "max_time_required": item.get("max_time_required", 60),
                    "projects": projects,
                    "experience": experience
                }
            )
            questions.append(question)

        return Command(
            goto="lvl2_mcq_synthesizer",
            update={
                "progress": {
                    2: LevelProgress(
                        level=2,
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
        return Command(
            update={
                "skill": state["skill"]  # keep the same skill to retry
            },
            goto="llm_lvl1_mcqs"
        )


def lvl2_mcq_synthesizer(userState: UserState) -> UserState:
    return userState
