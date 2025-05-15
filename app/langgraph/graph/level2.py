from langgraph.graph import StateGraph
from app.langgraph.models import UserState
from app.langgraph.nodes.level2 import (
    lvl2_mcq_generator,
    assign_lvl2_skill_workers,
    llm_lvl2_mcqs,
    llm_inference_validator,
    lvl2_mcq_synthesizer,
)
from langgraph.constants import START, END

level2_workflow_builder = StateGraph(UserState)

# Add Level 2 nodes to the workflow
level2_workflow_builder.add_node("lvl2_mcq_generator", lvl2_mcq_generator)
level2_workflow_builder.add_node(
    "assign_lvl2_skill_workers", assign_lvl2_skill_workers)
level2_workflow_builder.add_node("llm_lvl2_mcqs", llm_lvl2_mcqs)
level2_workflow_builder.add_node(
    "llm_inference_validator", llm_inference_validator)
level2_workflow_builder.add_node("lvl2_mcq_synthesizer", lvl2_mcq_synthesizer)
# Add edges and transitions between nodes
level2_workflow_builder.add_edge(START, "lvl2_mcq_generator")
level2_workflow_builder.add_conditional_edges(
    "lvl2_mcq_generator", assign_lvl2_skill_workers, ["llm_lvl2_mcqs"]
)

# level2_workflow_builder.add_conditional_edges(
#     "llm_lvl2_mcqs", llm_inference_validator, ["lvl2_mcq_synthesizer"]
# )

# level2_workflow_builder.add_edge("lvl2_mcq_synthesizer", "lvl2_await_response")
# level2_workflow_builder.add_edge("lvl2_await_response", "lvl2_evaluation")
level2_workflow_builder.add_edge("lvl2_mcq_synthesizer", END)

# Compile the graph
level2_graph = level2_workflow_builder.compile()
