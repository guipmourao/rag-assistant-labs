from app.services.chat_memory import ChatMessage
from app.services.llm_service import get_chat_model
from app.services.qa_service import format_context
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage


def format_chat_history(history: list[ChatMessage]) -> str:
    if not history:
        return "Sem histórico anterior."

    lines = []

    for message in history:
        role = "Usuário" if message["role"] == "user" else "Assistente"
        lines.append(f"{role}: {message['content']}")

    return "\n".join(lines)


def answer_chat_question(
    question: str,
    documents: list[Document],
    history: list[ChatMessage],
) -> str:
    llm = get_chat_model()

    context = format_context(documents)
    chat_history = format_chat_history(history)

    prompt = f"""
Você é um assistente de perguntas e respostas sobre documentos.

Use o histórico da conversa apenas para entender referências como "isso", "ele", "essa parte" ou "o assunto anterior".

Use exclusivamente o contexto recuperado dos documentos para responder ao conteúdo factual.

Regras:
- Se a resposta não estiver no contexto, diga que não sabe com base nos documentos enviados.
- Não invente informações.
- Responda em português.
- Seja direto.
- Use no máximo 3 parágrafos.

Histórico da conversa:
{chat_history}

Contexto recuperado:
{context}

Pergunta atual:
{question}

Resposta:
""".strip()

    response = llm.invoke([HumanMessage(content=prompt)])

    return str(response.content)
