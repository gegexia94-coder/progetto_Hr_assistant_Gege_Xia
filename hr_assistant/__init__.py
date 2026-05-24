import os
import uuid
import chainlit as cl

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
sources = set(item["source"] for item in metadatas) 
    
@cl.on_message
async def main(message: cl.Message):
        await cl.Message(
        content=f"Ho caricato {len(documents)} blocchi CV da {len(sources)} file."
        ).send()       