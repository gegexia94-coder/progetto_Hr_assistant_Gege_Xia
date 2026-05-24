import os
import uuid
import chainlit as cl
import chromadb
import ollama

from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv(".env")

openai_key = os.getenv("OPENAI_API_KEY")

if not openai_key:
    raise ValueError("OPENAI_API_KEY non trovata nel file .env")


def load_resumes(documents_dir="resumes"):
    documents = []
    metadatas = []
    ids = []

    for filename in os.listdir(documents_dir):
        if filename.endswith(".txt"):
            path = os.path.join(documents_dir, filename)

            with open(path, "r", encoding="utf-8") as file:
                chunks = file.read().replace("\n", ". ").split("### ")

            for chunk in chunks:
                if chunk.strip():
                    documents.append(chunk.strip())
                    metadatas.append({"source": filename})
                    ids.append(str(uuid.uuid4()))

    return documents, metadatas, ids


documents, metadatas, ids = load_resumes()

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_key,
    model_name="text-embedding-3-small"
)

chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(
    name="CVs",
    embedding_function=openai_ef
)

collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)


def leggi_prime_righe(file_path, limite=20):
    righe = []

    with open(file_path, "r", encoding="utf-8") as file:
        for i, riga in enumerate(file):
            if i < limite:
                righe.append(riga.strip())

    return righe


@cl.on_chat_start
def on_chat_start():
    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": "Sei un assistente HR. Rispondi in modo chiaro, professionale e concreto."
            }
        ],
    )


@cl.on_message
async def handle_message(message: cl.Message):
    user_question = message.content

    results = collection.query(
        query_texts=[user_question],
        n_results=1
    )

    filename = results["metadatas"][0][0]["source"]
    testo_trovato = results["documents"][0][0]

    context_nome = leggi_prime_righe(
        os.path.join("resumes", filename)
    )

    nome_response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": f"Trova solo nome e cognome del candidato in questo CV: {context_nome}"
            }
        ],
    )

    nome = nome_response["message"]["content"]

    context = f"""
CONTESTO:
file trovato: {filename}
nome candidato: {nome}
testo rilevante: {testo_trovato}
"""

    prompt = f"""
Domanda utente:
{user_question}

Usa questo contesto:
{context}

Rispondi come assistente HR.
Spiega perché questo profilo è adatto.
Non inventare informazioni non presenti nel contesto.
"""

    response_message = cl.Message(content="")
    await response_message.send()

    stream = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        await response_message.stream_token(
            chunk["message"]["content"]
        )

    await response_message.update()