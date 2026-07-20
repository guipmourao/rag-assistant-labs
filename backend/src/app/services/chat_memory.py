from typing import TypedDict
from uuid import uuid4


class ChatMessage(TypedDict):
    role: str
    content: str


_chat_sessions: dict[str, list[ChatMessage]] = {}


def create_session_id() -> str:
    session_id = str(uuid4())
    _chat_sessions[session_id] = []
    return session_id


def get_history(session_id: str) -> list[ChatMessage]:
    return _chat_sessions.get(session_id, [])


def add_message(session_id: str, role: str, content: str) -> None:
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = []

    _chat_sessions[session_id].append(
        {
            "role": role,
            "content": content,
        }
    )


def clear_history(session_id: str) -> None:
    _chat_sessions[session_id] = []
