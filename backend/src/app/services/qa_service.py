from app.services.llm_service import get_chat_model
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage


def format_context(documents: list[Document]) -> str:
    context_parts = []

    for index, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "fonte desconhecida")
        page = doc.metadata.get("page_label") or doc.metadata.get("page")

        context_parts.append(
            f"[Documento {index} | Fonte: {source} | Página: {page}]\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)


def answer_question(question: str, documents: list[Document]) -> str:
    llm = get_chat_model()
    context = format_context(documents)

    prompt = f"""
Use exclusivamente o contexto abaixo para responder à pergunta.

Regras:
- Se a resposta não estiver no contexto, diga que não sabe com base nos documentos enviados.
- Não invente informações.
- Responda em português.
- Seja direto.
- Use no máximo 3 parágrafos.

Contexto:
{context}

Pergunta:
{question}

Resposta:
""".strip()

    response = llm.invoke([HumanMessage(content=prompt)])

    return str(response.content)
