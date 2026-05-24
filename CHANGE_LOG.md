
## Avanzamento 05 - Nota tecnica su sentence-transformers

Durante la preparazione del chunking semantico è stata valutata la libreria `sentence-transformers`.

Nel mio ambiente attuale l'installazione fallisce perché introduce `torch`, una dipendenza molto pesante e non compatibile con il mio setup Poetry/Python attuale.

Per mantenere il progetto stabile e consegnabile, scelgo una soluzione alternativa:
- continuo a usare gli embedding OpenAI già funzionanti;
- implemento il chunking semantico senza `sentence-transformers`;
- mantengo il codice più leggero e adatto al mio ambiente.

Questa è una scelta tecnica consapevole, non un errore del progetto.

## Avanzamento 07 - Nota tecnica su MarkItDown

Durante la preparazione del caricamento file con estensioni diverse è stata valutata la libreria `markitdown`.

Nel mio ambiente attuale l'installazione non è compatibile perché `markitdown` dipende da `magika`, che richiede `onnxruntime >=1.17.0`, mentre il progetto usa già una versione diversa di `onnxruntime`.

Per mantenere il progetto stabile, scelgo una soluzione progressiva:
- supporto subito file testuali e dati: `.txt`, `.csv`, `.json`, `.xml`, `.html`, `.zip`;
- rimando PDF, DOCX, PPTX e XLSX a uno step separato;
- evito di introdurre dipendenze pesanti senza controllo.

Questa è una scelta tecnica consapevole per proteggere la stabilità del progetto.
