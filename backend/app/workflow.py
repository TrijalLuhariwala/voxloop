from __future__ import annotations

import json
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_mistralai import ChatMistralAI
from langgraph.graph import END, START, StateGraph

from .config import settings
from .models import CritiqueResult


class WorkflowState(TypedDict, total=False):
    selected_topic: str
    transcript: str
    history_text: str
    original_response: str
    critique: dict[str, Any]
    improved_response: str


def _require_keys() -> None:
    if not settings.mistral_api_key_primary or not settings.mistral_api_key_critic:
        raise ValueError(
            "Missing Mistral API keys. Add them to backend/.env before running the workflow."
        )


def _primary_model() -> ChatMistralAI:
    return ChatMistralAI(
        api_key=settings.mistral_api_key_primary,
        model=settings.mistral_model_primary,
        temperature=0.3,
    )


def _critic_model() -> ChatMistralAI:
    return ChatMistralAI(
        api_key=settings.mistral_api_key_critic,
        model=settings.mistral_model_critic,
        temperature=0.2,
    )


def draft_response(state: WorkflowState) -> dict[str, str]:
    chain = _primary_model() | StrOutputParser()
    prompt = [
        SystemMessage(
            content=(
                f"You are a {state['selected_topic']} voice assist agent in an ongoing, multi-turn conversation. "
                "Respond to the user in a way that is accurate, clear, and policy-compliant. "
                "Use the prior conversation history to maintain context and continuity across turns."
            )
        ),
        HumanMessage(
            content=(
                "Prior conversation history:\n"
                f"{state['history_text']}\n\n"
                "Latest user utterance (STT):\n"
                f"{state['transcript']}\n\n"
                "Generate the direct response that the agent would speak."
            )
        ),
    ]
    return {"original_response": chain.invoke(prompt)}


def critique_response(state: WorkflowState) -> dict[str, Any]:
    parser = JsonOutputParser(pydantic_object=CritiqueResult)
    chain = _critic_model() | parser
    prompt = [
        SystemMessage(
            content=(
                "You are a critique agent reviewing a voice assistant response in an ongoing multi-turn conversation. "
                "Analyze the user sentiment and state, and verify if the response properly references and maintains continuity with prior turns. "
                "Score the response for accuracy, relevance, empathy, clarity, policy_compliance, and overall. "
                "Provide short actionable suggestions for improvement."
            )
        ),
        HumanMessage(
            content=(
                "Return valid JSON only.\n"
                f"Schema instructions:\n{parser.get_format_instructions()}\n\n"
                "Prior conversation history:\n"
                f"{state['history_text']}\n\n"
                "Latest user utterance:\n"
                f"{state['transcript']}\n\n"
                "Original agent response:\n"
                f"{state['original_response']}"
            )
        ),
    ]
    critique = chain.invoke(prompt)
    return {"critique": critique}


def improve_response(state: WorkflowState) -> dict[str, str]:
    chain = _primary_model() | StrOutputParser()
    critique = json.dumps(state["critique"], ensure_ascii=True, indent=2)
    prompt = [
        SystemMessage(
            content=(
                f"You are a {state['selected_topic']} voice assist agent improving your response in an ongoing conversation thread. "
                "Use the critique and prior conversation history to produce a stronger final response, but do not mention the critique explicitly."
            )
        ),
        HumanMessage(
            content=(
                "Prior conversation history:\n"
                f"{state['history_text']}\n\n"
                "Latest user utterance:\n"
                f"{state['transcript']}\n\n"
                "Original response:\n"
                f"{state['original_response']}\n\n"
                "Critique and suggestions:\n"
                f"{critique}\n\n"
                "Rewrite the response so it is more accurate, relevant, empathetic, clear, policy-compliant, and fully consistent with prior turns."
            )
        ),
    ]
    return {"improved_response": chain.invoke(prompt)}



def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("draft_response", draft_response)
    graph.add_node("critique_response", critique_response)
    graph.add_node("improve_response", improve_response)
    graph.add_edge(START, "draft_response")
    graph.add_edge("draft_response", "critique_response")
    graph.add_edge("critique_response", "improve_response")
    graph.add_edge("improve_response", END)
    return graph.compile()


def run_workflow(selected_topic: str, transcript: str, history_text: str) -> dict[str, Any]:
    _require_keys()
    app = build_workflow()
    return app.invoke(
        {
            "selected_topic": selected_topic,
            "transcript": transcript,
            "history_text": history_text or "No prior conversation memory.",
        }
    )
