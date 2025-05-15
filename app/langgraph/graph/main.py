# main.py
from app.core.config import memory
from langgraph.graph import StateGraph
from app.langgraph.models import UserState
from app.langgraph.nodes.main.initialize_assessment import initialize_assessment
from .level1 import level1_graph
from .level2 import level2_graph
from app.langgraph.nodes.main.evaluation import level1_evaluation
from langgraph.constants import START, END

# Build the main graph
main_graph_builder = StateGraph(UserState)

# Add Nodes
main_graph_builder.add_node("initialize_assessment", initialize_assessment)
main_graph_builder.add_node("level1_graph", level1_graph)
main_graph_builder.add_node("level1_evaluation", level1_evaluation)
main_graph_builder.add_node("level2_graph", level2_graph)

# Add Edges
main_graph_builder.add_edge(START, "initialize_assessment")
main_graph_builder.add_edge("initialize_assessment", "level1_graph")
main_graph_builder.add_edge("level1_graph", "level1_evaluation")
main_graph_builder.add_edge("level1_evaluation", "level2_graph")
main_graph_builder.add_edge("level2_graph", END)

# Compile
main_graph = main_graph_builder.compile(checkpointer=memory)
