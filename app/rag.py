"""Retrieval-augmented generation: answer questions from retrieved passages."""

from openai import OpenAI

from . import config

_client = OpenAI(base_url=config.AZURE_AI_ENDPOINT, api_key=config.AZURE_AI_KEY)

_SYSTEM = (
    "You are a knowledge-base assistant for ZESCO, a Zambian electricity "
    "utility. Answer the user's question using ONLY the provided context "
    "passages. If the answer is not contained in the context, say you do not "
    "have that information rather than guessing. Be concise and, where useful, "
    "cite the source file names you relied on."
)


def answer(question: str, passages: list[dict]) -> str:
    context = "\n\n".join(
        f"[{i + 1}] (source: {p['source']})\n{p['text']}"
        for i, p in enumerate(passages)
    )
    prompt = f"Context passages:\n{context}\n\nQuestion: {question}"
    response = _client.responses.create(
        model=config.AZURE_AI_DEPLOYMENT,
        instructions=_SYSTEM,
        input=prompt,
    )
    return response.output_text
