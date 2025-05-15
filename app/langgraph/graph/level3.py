from langgraph.graph import StateGraph
from app.langgraph.models import UserState
from app.langgraph.nodes.level3 import (
    lvl3_mcq_generator,
    assign_lvl3_skill_workers,
    llm_lvl3_mcqs,
    llm_inference_validator3,
    lvl3_mcq_synthesizer,
)
from langgraph.constants import START, END

level3_workflow_builder = StateGraph(UserState)

level3_workflow_builder.add_node("lvl3_mcq_generator", lvl3_mcq_generator)
level3_workflow_builder.add_node(
    "assign_lvl3_skill_workers", assign_lvl3_skill_workers)
level3_workflow_builder.add_node("llm_lvl3_mcqs", llm_lvl3_mcqs)
level3_workflow_builder.add_node(
    "llm_inference_validator3", llm_inference_validator3)
level3_workflow_builder.add_node("lvl3_mcq_synthesizer", lvl3_mcq_synthesizer)

level3_workflow_builder.add_edge(START, "lvl3_mcq_generator")
level3_workflow_builder.add_conditional_edges(
    "lvl3_mcq_generator", assign_lvl3_skill_workers, ["llm_lvl3_mcqs"]
)
# level3_workflow_builder.add_conditional_edges(
#     "llm_lvl3_mcqs", llm_inference_validator3, ["lvl3_mcq_synthesizer"]
# )
level3_workflow_builder.add_edge("lvl3_mcq_synthesizer", END)

level3_graph = level3_workflow_builder.compile()
