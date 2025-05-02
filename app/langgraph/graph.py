from .state import UserState, LevelProgress
from .llm_config import memory
from . import nodes
from langgraph.graph import StateGraph, END, START

# Main assessment workflow with all 3 levels, updated for new state schema

def build_main_workflow():
    graph = StateGraph(UserState)
    # --- Level 1 nodes ---
    graph.add_node("level1_mcq_generator", nodes.level1_mcq_generator)
    graph.add_node("assign_level1_workers", nodes.assign_level1_workers)
    graph.add_node("llm_lvl1_mcqs", nodes.llm_lvl1_mcqs)
    graph.add_node("llm_inference_validator", nodes.llm_inference_validator)
    graph.add_node("lvl1_mcq_synthesizer", nodes.lvl1_mcq_synthesizer)
    graph.add_node("lvl1_await_respone", nodes.lvl1_await_respone)
    graph.add_node("lvl1_evaluate", nodes.lvl1_evaluate)
    # --- Level 2 nodes ---
    graph.add_node("lvl2_msq_generator", nodes.lvl2_msq_generator)
    graph.add_node("assign_lvl2_skill_workers", nodes.assign_lvl2_skill_workers)
    graph.add_node("llm_lvl2_msqs", nodes.llm_lvl2_msqs)
    graph.add_node("llm_inference_validator2", nodes.llm_inference_validator2)
    graph.add_node("lvl2_synthesizer", nodes.lvl2_msq_synthesizer)
    graph.add_node("lvl2_await_response", nodes.lvl2_await_response)
    graph.add_node("lvl2_evaluation", nodes.lvl2_evaluation)
    # --- Level 3 nodes ---
    graph.add_node("lvl3_msq_generator", nodes.lvl3_msq_generator)
    graph.add_node("assign_lvl3_skill_workers", nodes.assign_lvl3_skill_workers)
    graph.add_node("llm_lvl3_msqs", nodes.llm_lvl3_msqs)
    graph.add_node("llm_inference_validator3", nodes.llm_inference_validator3)
    graph.add_node("lvl3_synthesizer", nodes.lvl3_synthesizer)
    graph.add_node("lvl3_await_response", nodes.lvl3_await_response)
    graph.add_node("lvl3_evaluation", nodes.lvl3_evaluation)

    # --- Edges for Level 1 ---
    graph.add_edge(START, "level1_mcq_generator")
    graph.add_edge("level1_mcq_generator", "assign_level1_workers")
    graph.add_conditional_edges("assign_level1_workers", nodes.assign_level1_workers, ["llm_lvl1_mcqs"])
    graph.add_edge("llm_lvl1_mcqs", "llm_inference_validator")
    graph.add_conditional_edges("llm_inference_validator", nodes.llm_inference_validator, ["lvl1_mcq_synthesizer", "llm_lvl1_mcqs"])
    graph.add_edge("lvl1_mcq_synthesizer", "lvl1_await_respone")
    graph.add_edge("lvl1_await_respone", "lvl1_evaluate")
    graph.add_conditional_edges("lvl1_evaluate", nodes.lvl1_evaluate, ["lvl2_msq_generator", END])

    # --- Edges for Level 2 ---
    graph.add_edge("lvl2_msq_generator", "assign_lvl2_skill_workers")
    graph.add_conditional_edges("assign_lvl2_skill_workers", nodes.assign_lvl2_skill_workers, ["llm_lvl2_msqs"])
    graph.add_edge("llm_lvl2_msqs", "llm_inference_validator2")
    graph.add_conditional_edges("llm_inference_validator2", nodes.llm_inference_validator2, ["lvl2_synthesizer", "llm_lvl2_msqs"])
    graph.add_edge("lvl2_synthesizer", "lvl2_await_response")
    graph.add_edge("lvl2_await_response", "lvl2_evaluation")
    graph.add_conditional_edges("lvl2_evaluation", nodes.lvl2_evaluation, ["lvl3_msq_generator", END])

    # --- Edges for Level 3 ---
    graph.add_edge("lvl3_msq_generator", "assign_lvl3_skill_workers")
    graph.add_conditional_edges("assign_lvl3_skill_workers", nodes.assign_lvl3_skill_workers, ["llm_lvl3_msqs"])
    graph.add_edge("llm_lvl3_msqs", "llm_inference_validator3")
    graph.add_conditional_edges("llm_inference_validator3", nodes.llm_inference_validator3, ["lvl3_synthesizer", "llm_lvl3_msqs"])
    graph.add_edge("lvl3_synthesizer", "lvl3_await_response")
    graph.add_edge("lvl3_await_response", "lvl3_evaluation")
    graph.add_edge("lvl3_evaluation", END)

    return graph.compile(checkpointer=memory)

main_workflow = build_main_workflow()

def run_assessment_step(state: dict, user_response: dict):
    # Update state with user response for the current level
    state = dict(state)
    current_level = state.get('current_level', 1)
    if 'progress' not in state:
        state['progress'] = {}
    if current_level not in state['progress']:
        state['progress'][current_level] = LevelProgress(level=current_level, questions=[], answers={})
    state['progress'][current_level].answers = user_response
    result = main_workflow.invoke(state)
    return result
