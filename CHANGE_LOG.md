
## Avanzamento 05 - Nota tecnica su sentence-transformers

Durante la preparazione del chunking semantico è stata valutata la libreria `sentence-transformers`.

Nel mio ambiente attuale l'installazione fallisce perché introduce `torch`, una dipendenza molto pesante e non compatibile con il mio setup Poetry/Python attuale.

Per mantenere il progetto stabile e consegnabile, scelgo una soluzione alternativa:
- continuo a usare gli embedding OpenAI già funzionanti;
- implemento il chunking semantico senza `sentence-transformers`;
- mantengo il codice più leggero e adatto al mio ambiente.

Questa è una scelta tecnica consapevole, non un errore del progetto.
