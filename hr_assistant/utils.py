import ollama

from config import Config


class LLMHelper:
    @staticmethod
    def chat(messages):
        return ollama.chat(
            model=Config.LLM_MODEL,
            messages=messages,
            stream=True,
        )

    @staticmethod
    async def get_candidate_name(context):
        response = ollama.chat(
            model=Config.LLM_MODEL_LOW,
            messages=[
                {
                    "role": "user",
                    "content": f"""
Dato questo curriculum, trova solo nome e cognome del candidato.
Non aggiungere spiegazioni.

CURRICULUM:
{context}
""",
                }
            ],
        )

        return response["message"]["content"].strip()

    @staticmethod
    def create_prompt(context, question, candidate_name):
        return f"""
Sei un assistente HR.

Domanda utente:
{question}

Contesto trovato nel database:
{context}

Candidato individuato:
{candidate_name}

Rispondi in modo professionale e concreto.
Spiega perché questo profilo è adatto alla richiesta.
Non inventare informazioni non presenti nel contesto.
Indica anche il file CV individuato.
"""
