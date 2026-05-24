import os
import shutil
import chainlit as cl

from config import Config
from database import Database
from document_processor import DocumentProcessor
from utils import LLMHelper


db = Database()
dp = DocumentProcessor()

added, updated, removed = dp.process_documents(db)

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
            name="clear_database",
            label="Svuota Database",
            payload={}
        ),
    ]


def is_supported_upload(file_name):
    extension = os.path.splitext(file_name)[1].lower()
    return extension in DocumentProcessor.SUPPORTED_EXTENSIONS


async def process_uploaded_file(file):
    file_name = os.path.basename(file.name)

    if not is_supported_upload(file_name):
        return f"File non supportato: {file_name}"

    os.makedirs(Config.DOCUMENTS_DIR, exist_ok=True)

    destination = os.path.join(Config.DOCUMENTS_DIR, file_name)

    shutil.copy2(file.path, destination)

    db.remove_document_by_source(file_name)

    documents, metadatas, ids = dp.process_single_document(destination)

    if not documents:
        return f"File salvato ma non indicizzato: {file_name}"

    db.add_documents(documents, metadatas, ids)

    return f"File caricato e indicizzato: {file_name} ({len(documents)} chunk)"


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
    added, updated, removed = dp.process_documents(db)
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


@cl.action_callback("clear_database")
async def on_clear_database(action):
    db.clear()

    await cl.Message(
        content="Database svuotato. Premi Reindex Database per ricostruirlo.",
        actions=build_actions(),
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    if message.elements:
        results = []

        for file in message.elements:
            result = await process_uploaded_file(file)
            results.append(result)

        await cl.Message(content="\n".join(results)).send()

        if not message.content.strip():
            return

    user_question = message.content

    results = db.query(user_question)

    if not results["documents"] or not results["documents"][0]:
        await cl.Message(
            content="Nessun curriculum trovato per questa richiesta.",
            actions=build_actions(),
        ).send()
        return

    filename = results["metadatas"][0][0]["source"]
    text_found = results["documents"][0][0]

    context_lines = DocumentProcessor.read_first_lines(
        os.path.join(Config.DOCUMENTS_DIR, filename),
        n_lines=200,
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
