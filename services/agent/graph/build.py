"""Wires the seven nodes into a LangGraph StateGraph."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from services.agent.graph import nodes
from services.agent.graph.state import AgentState


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("receive_input", nodes.receive_input)
    graph.add_node("gather_context", nodes.gather_context)
    graph.add_node("plan_action", nodes.plan_action)
    graph.add_node("build_proposal", nodes.build_proposal)
    graph.add_node("gateway_call", nodes.gateway_call)
    graph.add_node("handle_decision", nodes.handle_decision)
    graph.add_node("respond", nodes.respond)

    graph.set_entry_point("receive_input")
    graph.add_edge("receive_input", "gather_context")
    graph.add_edge("gather_context", "plan_action")
    graph.add_edge("plan_action", "build_proposal")
    graph.add_edge("build_proposal", "gateway_call")
    graph.add_edge("gateway_call", "handle_decision")
    graph.add_edge("handle_decision", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


AGENT_GRAPH = None


def get_agent_graph():
    global AGENT_GRAPH
    if AGENT_GRAPH is None:
        AGENT_GRAPH = build_agent_graph()
    return AGENT_GRAPH
