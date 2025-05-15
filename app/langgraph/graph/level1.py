from langgraph.graph import StateGraph
from app.langgraph.models import UserState
from app.langgraph.nodes.level1 import (
    lvl1_mcq_generator,
    assign_level1_workers,
    llm_lvl1_mcqs,
    llm_inference_validator,
    lvl1_mcq_synthesizer,
)
from langgraph.constants import START, END

level1_workflow_builer = StateGraph(UserState)

level1_workflow_builer.add_node("lvl1_mcq_generator", lvl1_mcq_generator)
level1_workflow_builer.add_node("assign_level1_workers", assign_level1_workers)
level1_workflow_builer.add_node("llm_lvl1_mcqs", llm_lvl1_mcqs)
level1_workflow_builer.add_node(
    "llm_inference_validator", llm_inference_validator)
level1_workflow_builer.add_node(
    "lvl1_mcq_synthesizer", lvl1_mcq_synthesizer)


level1_workflow_builer.add_edge(START, "lvl1_mcq_generator")
level1_workflow_builer.add_conditional_edges(
    "lvl1_mcq_generator", assign_level1_workers, ["llm_lvl1_mcqs"])

level1_workflow_builer.add_edge("lvl1_mcq_synthesizer", END)


level1_graph = level1_workflow_builer.compile()
