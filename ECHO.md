Executive Summary: Echo (gestione dei "concetti")

Obiettivo
Echo è un sistema di automazione focalizzato non soltanto sulla creazione di tweet, ma anche sull'identificazione e la gestione di "concetti" estratti da newsletter. In questo modo si evita la duplicazione di informazioni e si garantisce la coerenza nel lungo periodo, a prescindere da quante volte lo stesso tema venga trattato in newsletter diverse.

1. Acquisizione e delle Newsletter
	Raccolta Email: Le email provenienti dalle varie newsletter vengono lette e memorizzate in un database relazionale SQLite.

2. Identificazione dei "Concetti"
	Generazione Concetti
	-	Per ogni email, l'LLM cerca di ricavare uno o più "concetti" centrali (es. "OpenAI rilascia un nuovo modello GPT", "Nuova feature di Twitter su spazi audio", ecc.).
	- andiamo a salvare il testo del concetto su un database vettoriale (chroma) se non esiste già un concetto simile con un threshold a 0.85
	- Ciascun concetto ha un testo descrittivo sintetico, un set di keywords e un set di links e un id del vettore su Chroma.
	- andiamo a salvare questi dati nel db relazionale (sqlite)

3. Generazione dei Tweet
	Creazione Contenuti
	- Il sistema offre due modalità di generazione: tweet singoli o thread, sia da concetti locali che da fonti esterne
	- Per i concetti locali:
		- Recupera i concetti non utilizzati degli ultimi 5 giorni
		- Utilizza il database vettoriale per trovare concetti simili come contesto aggiuntivo
		- Genera tweet tecnici mirati a un pubblico di tech, data science e AI
	- Per le fonti esterne:
		- Estrae il contenuto da URL forniti
		- Analizza il testo e i link correlati
		- Genera contenuti mantenendo lo stesso stile tecnico
	- Caratteristiche dei contenuti:
		- Tweet limitati a 280 caratteri
		- Thread strutturati con tweet iniziale accattivante
		- Inclusione automatica dei link rilevanti
		- Possibilità di aggiungere istruzioni extra per personalizzare il tono o il contenuto
