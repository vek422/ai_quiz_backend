from app.langgraph.models import UserState
from langgraph.types import Send, Command, interrupt
from typing import TypedDict, Literal
from app.langgraph.prompts import lvl1_prompt_template
from app.langgraph.models import Question
from app.core.config import llm
import json
from uuid import uuid4
from app.langgraph.models import LevelProgress


class LLMInferenceState(TypedDict):
    skill: str
    llm_response: str


def lvl1_mcq_generator(userState: UserState):
    userState.current_level = 1
    userState.unlocked_levels.append(1)
    return userState


def assign_level1_workers(userState: UserState):
    # Assign workers for level 1
    skills = userState.job_description.required_skills
    return [Send('llm_lvl1_mcqs', {'skill': s}) for s in skills]


def llm_lvl1_mcqs(state: LLMInferenceState) -> LLMInferenceState:
    skill = state['skill']
    prompt = lvl1_prompt_template.format(skill=skill, num=5)
    response = llm.invoke(prompt)
    return Send('llm_inference_validator', {'skill': skill, 'llm_response': response.content})


def llm_inference_validator(state: LLMInferenceState) -> Command[Literal["lvl1_mcq_synthesizer", "llm_lvl1_mcqs"]]:
    try:
        lvl1_mcqs = json.loads(state["llm_response"])
        skill = state["skill"]

        # Validate lvl1_mcqs is a list
        if not isinstance(lvl1_mcqs, list):
            raise ValueError("Parsed MCQs should be a list")

        # Transform into List[Question]
        questions = []
        for item in lvl1_mcqs:
            question = Question(
                id=str(uuid4()),  # Generate unique id
                text=item.get("question", ""),
                options=item.get("options", []),
                correct_answer=item.get("answer", ""),
                level=1,
                metadata={
                    "skill": skill,
                    "max_time_required": item.get("max_time_required", 60)
                }
            )
            questions.append(question)

        return Command(
            update={
                "progress": {
                    1:  LevelProgress(
                        level=1,
                        questions=questions,
                        answers={},
                        score=None,
                        completed=False
                    )
                }
            },
            goto="lvl1_mcq_synthesizer"
        )

    except Exception as e:
        print(f"Invalid JSON or format error: {e}")
        return Command(
            update={
                "skill": state["skill"]  # keep the same skill to retry
            },
            goto="llm_lvl1_mcqs"
        )


def lvl1_mcq_synthesizer(userState: UserState) -> UserState:
    # Synthesize the MCQs for level 1
    return userState
