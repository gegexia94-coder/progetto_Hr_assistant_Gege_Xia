import os
import chainlit as cl

from config import Config
from database import Database
from document_processor import DocumentProcessor
from utils import LLMHelper


db = Database()

added, updated, removed = DocumentProcessor.process_documents(db)

print(
    f"Document sync complete: "
    f"{added} added, {updated} updated, {removed} removed"
)


def build_actions():
    return [
        cl.Action(
            name="database_stats",
            label="Statistiche Database",
            payload={}
        ),
        cl.Action(
            name="reindex_database",
            label="Reindex Database",
            payload={}
        ),
        cl.Action(
            name="hello_world",
            label="Ciao Mondo",
            payload={}
        ),
    ]


@cl.on_chat_start
async def start():
    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": (
                    "Sei un assistente HR. "
                    "Rispondi in modo professionale, sintetico e concreto. "
                    "Usa solo il contesto dei CV trovati."
                ),
            }
        ],
    )

    stats = db.stats()

    await cl.Message(
        content=(
            "HR Assistant pronto.\n\n"
            f"CV tracciati: {stats['files']}\n"
            f"Chunk nel database: {stats['chunks']}"
        ),
        actions=build_actions(),
    ).send()


@cl.action_callback("database_stats")
async def on_database_stats(action):
    stats = db.stats()

    sources = "\n".join(f"- {source}" for source in stats["sources"])

    await cl.Message(
        content=(
            "Statistiche database:\n\n"
            f"File tracciati: {stats['files']}\n"
            f"Chunk salvati: {stats['chunks']}\n\n"
            f"File:\n{sources}"
        ),
        actions=build_actions(),
    ).send()


@cl.action_callback("reindex_database")
async def on_reindex_database(action):
    db.clear()
    added, updated, removed = DocumentProcessor.process_documents(db)
    stats = db.stats()

    await cl.Message(
        content=(
            "Database reindicizzato.\n\n"
            f"Aggiunti: {added}\n"
            f"Aggiornati: {updated}\n"
            f"Rimossi: {removed}\n"
            f"File tracciati: {stats['files']}\n"
            f"Chunk salvati: {stats['chunks']}"
        ),
        actions=build_actions(),
    ).send()


@cl.action_callback("hello_world")
async def on_hello_world(action):
    await cl.Message(
        content="Ciao Mondo. I pulsanti Chainlit funzionano.",
        actions=build_actions(),
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    user_question = message.content
    results = db.query(user_question)

    filename = results["metadatas"][0][0]["source"]
    text_found = results["documents"][0][0]

    context_lines = DocumentProcessor.read_first_lines(
        os.path.join(Config.DOCUMENTS_DIR, filename),
        limit=200,
    )

    candidate_name = await LLMHelper.get_candidate_name(context_lines)

    context = (
        f"File individuato: {filename}\n"
        f"Testo più rilevante:\n{text_found}"
    )

    prompt = LLMHelper.create_prompt(
        context=context,
        question=user_question,
        candidate_name=candidate_name,
    )

    messages = cl.user_session.get("messages", [])
    messages.append({"role": "user", "content": prompt})

    response_message = cl.Message(content="")
    await response_message.send()

    try:
        stream = LLMHelper.chat(messages)

        for chunk in stream:
            token = chunk["message"]["content"]
            await response_message.stream_token(token)

        messages.append(
            {
                "role": "assistant",
                "content": response_message.content,
            }
        )

        await response_message.update()

    except Exception as error:
        await cl.Message(
            content=f"Errore durante la risposta: {error}",
            actions=build_actions(),
        ).send()

    cl.user_session.set("messages", messages)
