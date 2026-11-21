"""Scenario-scoped conversational assistant."""

from __future__ import annotations

from src.db.repositories import ChatRepository, ScenarioRepository
from src.prompts.chat import build_chat_system_prompt
from src.services.explanation_renderer import summary_for_chat
from src.services.groq_client import chat_completion


def ask_about_scenario(
    conn,
    *,
    session_id: str,
    scenario_id: str,
    user_message: str,
) -> str:
    scenario_repo = ScenarioRepository(conn)
    chat_repo = ChatRepository(conn)
    bundle = scenario_repo.get_bundle(scenario_id)
    if not bundle:
        raise ValueError(f"Scenario not found: {scenario_id}")

    system = build_chat_system_prompt(
        technology=bundle.scenario.technology,
        title=bundle.scenario.title,
        stem=bundle.scenario.stem,
        explanation_summary=summary_for_chat(bundle.explanation),
    )
    history = chat_repo.list_messages(session_id, scenario_id)
    messages = [{"role": "system", "content": system}]
    for msg in history[-12:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    chat_repo.add_message(session_id, scenario_id, "user", user_message)
    answer = chat_completion(messages, temperature=0.4)
    chat_repo.add_message(session_id, scenario_id, "assistant", answer)
    return answer
