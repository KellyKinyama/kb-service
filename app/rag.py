"""Retrieval-augmented generation: answer questions from retrieved passages."""

from openai import OpenAI

from . import config

_client = OpenAI(base_url=config.AZURE_AI_ENDPOINT, api_key=config.AZURE_AI_KEY)

_SYSTEM = (
    "You assist ZESCO call-centre agents while they are on a call with a "
    "customer, for a Zambian electricity utility. The agent consults you when a "
    "caller asks a difficult question. Answer using ONLY the provided context "
    "passages. Give a clear, concise answer the agent can relay directly to the "
    "caller, in plain customer-friendly language. If the answer is not contained "
    "in the context, say you do not have that information and suggest the agent "
    "escalate or check the relevant department, rather than guessing. Where "
    "useful, cite the source file names you relied on."
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
