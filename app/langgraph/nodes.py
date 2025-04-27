from .state import State,LLMInferenceState
from  langgraph.types import Send,Command,interrupt
from typing_extensions import Literal
import json
from .llm_config import llm, memory
from .prompts.template import lvl1_prompt_template
# -- Level 1 mcq nodes -- 

def level1_mcq_generator(state:State):
    return {"unlocked_level":1}

def assign_level1_workers(state:State):
    lvl1_technical_skills= state["resume_jd_compiled"]["technical_skills"]

    return [Send("llm_lvl1_mcqs",{"skill":s}) for s in lvl1_technical_skills]


def llm_lvl1_mcqs(state:LLMInferenceState) -> LLMInferenceState:
  prompt = lvl1_prompt_template.format(skill=state["skill"],num=5)
  mcqs = llm.invoke(prompt)
  skill = state["skill"]
  # print(f"in llm_lvl1 for {skill} response {mcqs.content}")
  # print(mcqs.content)
  return Send("llm_inference_validator",{"skill":skill,"llm_response":mcqs.content})
def llm_inference_validator(state:LLMInferenceState)->Command[Literal["lvl1_mcq_synthesizer","llm_lvl1_mcqs"]]:
  print("inside validator\n")
  try:
    lvl1_mcqs = json.loads(state["llm_response"])
    skill = state["skill"]

    return Command(
        update={
            "lvl1_generated_mcqs":{
                state["skill"]:lvl1_mcqs
            }
        },
        goto="lvl1_mcq_synthesizer"
    )
  except:
    print("Invalid JSON")
    return Command(
        update={
            "skill":state["skill"]
        },
        goto="llm_lvl1_mcqs"
    )
  

def lvl1_mcq_synthesizer(state: dict) -> dict:
    updated_mcqs = {}
    for skill, questions in state["lvl1_generated_mcqs"].items():
        synthesized = []
        for idx, q in enumerate(questions, start=1):
            q_with_id = {
                "id": f"{skill.lower()}_{idx}",
                **q
            }
            synthesized.append(q_with_id)
        updated_mcqs[skill] = synthesized
    
    return {
        "lvl1_generated_mcqs": updated_mcqs,
        "current_stage": "lvl_1_waiting_response"
    }


def lvl1_await_respone(state:State):
   user_response = interrupt("waiting for level 1 mcq")
   return {
      "level1_answers":user_response
   }


def lvl1_evaluate(state: State) -> dict:
    generated_mcqs = state["lvl1_generated_mcqs"]
    user_response = state["lvl1_response"]

    skill_scores = {}
    pass_threshold = 0.7
    all_passed = True

    for skill, questions in generated_mcqs.items():
        total_questions = len(questions)
        correct_answers = 0

        for question in questions:
            question_id = question["id"]
            correct_answer = question["answer"]
            user_answer = user_response.get(skill, {}).get(question_id)

            if user_answer == correct_answer:
                correct_answers += 1

        accuracy = correct_answers / total_questions if total_questions > 0 else 0
        skill_scores[skill] = {
            "correct": correct_answers,
            "total": total_questions,
            "accuracy": round(accuracy, 2),
            "passed": accuracy >= pass_threshold
        }

        if accuracy < pass_threshold:
            all_passed = False

    next_stage = "lvl_2" if all_passed else "end"

    return {
        "current_stage": next_stage,
        "lvl1_score": skill_scores
    }
