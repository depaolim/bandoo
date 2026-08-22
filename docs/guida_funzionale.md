# Scuola di musica — guida funzionale e operativa

**Documento del 01/08/2026** · riferito a **bandoo 18.0.1.0.0**

---

<a id="g-01"></a>
## G-01 · Il modello

La scuola vende **corsi** e paga **insegnanti**. Sono due cicli distinti che si incontrano in
un punto solo: **le ore delle lezioni**.

- **Ciclo attivo** — lo studente si iscrive, riceve le lezioni, paga la retta in tre rate. Le
  lezioni non erogate e le assenze giustificate producono una **detrazione** sull'ultima rata.
- **Ciclo passivo** — l'insegnante registra le ore delle lezioni che ha tenuto; quelle ore
  diventano il suo **compenso**, liquidato come acquisto di servizi. Il compenso è un
  **costo**, non una riduzione dei ricavi.

Le ore sono il perno: la stessa registrazione dimostra allo studente che la lezione è stata
erogata e all'insegnante che gli spetta il compenso.

<a id="g-02"></a>
### G-02 · Corsi individuali e collettivi

| | Individuale (es. pianoforte) | Collettivo (es. solfeggio) |
|---|---|---|
| Registro delle lezioni | **uno per studente**, creato all'iscrizione | **uno solo**, condiviso da tutti |
| Presenze | il solo studente | tutti gli iscritti |
| Recupero di una lezione | riguarda quello studente | riguarda l'intera classe |

A catalogo ogni corso è un **servizio** con il suo prezzo annuo. La differenza fra i due tipi
si dichiara sul prodotto: l'individuale indica il **modello di registro** da copiare a ogni
iscrizione, il collettivo indica il **progetto condiviso** già esistente.

<a id="g-03"></a>
### G-03 · Chi è chi

- **Studente**: è l'intestatario dell'iscrizione e il destinatario della retta, anche se
  minore. Va inserito come **persona**, non come azienda: le tendine di selezione filtrano
  sulle persone fisiche, e un contatto-azienda non comparirà mai.
- **Genitore**: è un recapito **dentro la scheda dello studente**, non un contatto separato.
  Per più fratelli il genitore si ripete su ciascuno; in cambio ogni scheda è autoconsistente.
- **Insegnante**: è sia un dipendente (per registrare le ore) sia un fornitore (per ricevere
  il compenso). Le due cose puntano allo stesso contatto.

---

<a id="g-04"></a>
## G-04 · Ciclo attivo

<a id="g-05"></a>
### G-05 · Aule

`Progetto → Configurazione → Aule` → **Nuovo** per ciascuno spazio (es. "Sala Pianoforte",
"Sala Solfeggio").

<a id="g-06"></a>
### G-06 · Insegnante

1. `Dipendenti → Nuovo` → nome e ruolo.
2. Nella stessa scheda, tab **Impostazioni → Utente correlato** → creare lì l'utente con la
   sua email. Creandolo da qui il sistema compila da sé il **Contatto lavoro**, che è
   l'anagrafica su cui verrà intestato il compenso.
3. L'utente nasce **senza password**: va impostata da `Impostazioni → Utenti`, oppure
   l'insegnante la sceglie ricevendo l'invito.

✅ Controllare che **Contatto lavoro** risulti valorizzato: senza, il compenso non parte.

<a id="g-07"></a>
### G-07 · Registri dei corsi

`Progetto → Nuovo`, con **Fogli ore** attivi, **Lezioni previste** = quante nell'anno, e
**Responsabile** = l'insegnante.

- **Corso collettivo**: il registro vero e proprio, es. "Solfeggio 2026/27".
- **Corso individuale**: un **modello**, es. "Template Pianoforte", che va creato anche con
  **Fatturabile** attivo — senza, non comparirà fra i modelli selezionabili sul prodotto — e
  **senza nessuna lezione dentro**: viene copiato a ogni iscrizione, lezioni comprese.

Dopo aver collegato il modello al prodotto (2.4), **archiviarlo**: non deve comparire fra i
corsi operativi. Il collegamento resta valido.

<a id="g-08"></a>
### G-08 · Corsi a catalogo

`Vendite → Prodotti → Nuovo`, **Tipo = Servizio**, prezzo di vendita = il prezzo annuo.

**Svuotare le imposte di vendita**: le rette sono fuori campo IVA, e il valore predefinito
applicherebbe il 22%.

Nella pagina **Informazioni generali**, tendina **"Crea un ordine"**:

| Tipo di corso | Selezione | Campo che compare sotto |
|---|---|---|
| Individuale | **Progetto** | **Modello di progetto** → il modello creato in 2.3 |
| Collettivo | **Progetto condiviso** | **Progetto condiviso** → il registro creato in 2.3 |

È la selezione a fare di un prodotto un corso: non esiste una casella "questo è un corso".

✅ Un collettivo senza progetto condiviso, o un individuale senza modello, deve essere
**rifiutato al salvataggio**.

<a id="g-09"></a>
### G-09 · Studenti

`Contatti → Nuovo`, tipo **Persona**.

Per un minore, nella sua scheda: tab **Contatti e indirizzi → Aggiungi** → il genitore, tipo
*Contatto*, coi suoi recapiti.

<a id="g-10"></a>
### G-10 · Iscrizione

`Vendite → Ordini → Nuovo`, **Cliente = lo studente**. Una riga per corso; un ordine per
studente anche se frequenta più corsi.

Su ogni riga: il **prezzo concordato** (proposto dal catalogo, modificabile) e le **lezioni
previste**.

⚠️ **Iscrizione a metà anno**: le lezioni previste arrivano col valore annuale. Vanno
**ridotte alle lezioni residue**, insieme al prezzo, **prima di confermare**: è il numero su
cui si calcolerà il conguaglio.

Poi **Conferma**. Alla conferma:

- per i corsi individuali nasce il registro dello studente, copiato dal modello, e la colonna
  **Corso** della riga lo mostra (in bozza era vuota: il registro non esisteva ancora);
- per i collettivi lo studente entra fra gli **Studenti iscritti** del registro condiviso.

Una riga aggiunta a un ordine **già confermato** iscrive comunque, senza riconfermare.

<a id="g-11"></a>
### G-11 · Programmare le lezioni

`Progetto → Genera lezioni`, una volta per registro:

- **Corso** = il registro; insegnante e numero di lezioni si compilano da soli;
- **Aula**, **Prima lezione** (data), **Ora inizio**, **Cadenza** → **Genera**.

Rigenerare sulle stesse date non produce duplicati.

<a id="g-12"></a>
### G-12 · Svolgere le lezioni

**L'insegnante entra con la propria utenza** e va in `Progetti → Lavori → I miei lavori`.

Sulla lezione, tab **Ore** → nuova riga con data e tempo speso. **Non esiste una casella
"lezione svolta"**: è la registrazione delle ore a renderla svolta.

Nel tab **Presenze** si indica lo stato di ciascuno studente:

| Stato | Ai fini della retta |
|---|---|
| Presente | paga |
| Assente | paga — la lezione è stata erogata |
| Assente giustificato | **non paga** |

La colonna **Ai fini retta** si compila da sola.

Spostare data o aula è un **rimando**: resta la stessa lezione e non incide sui conteggi. Una
lezione prevista e mai tenuta è invece **non erogata** e verrà detratta; per **recuperarla**
basta registrarne le ore, eventualmente dopo averla spostata.

<a id="g-13"></a>
### G-13 · Iscritti arrivati a corso iniziato

Le presenze di una lezione sono **fotografate quando la lezione viene creata**: chi si iscrive
dopo non compare nelle lezioni già svolte, ed è corretto — sono storia.

Per le lezioni future: `Progetto → <registro> → Studenti iscritti` → **Allinea presenze
lezioni future**, che aggiunge il nuovo iscritto alle sole lezioni non ancora svolte.

<a id="g-14"></a>
### G-14 · Consuntivi e conguagli

- `Progetto → Rendicontazione → Analisi lavori` — ore per progetto, insegnante e mese.
- `Progetto → Rendicontazione → Presenze studenti` — raggruppate per **Ai fini retta**:
  mostra solo le lezioni con ore registrate.
- `Vendite → Ordini → Conguagli per iscrizione` — il dettaglio per singolo corso.
- `Vendite → Ordini → Conguagli per ordine` — **queste sono le rate dovute**.

```
prezzo lezione = prezzo concordato ÷ lezioni previste
detrazione     = (assenze giustificate + lezioni non erogate) × prezzo lezione

rata 1 = rata 2 = totale ordine ÷ 3
rata 3 = totale − rata 1 − rata 2 − detrazioni        (mai negativa)
```

**Il credito che eccede l'ordine è perso**: se le detrazioni superano il residuo, la terza
rata è zero e non si genera un rimborso. Da sapere prima di concordare sconti importanti.

Casi particolari:

- **borsa di studio o scambio**: riga a prezzo zero, conguaglio zero;
- **annullare una singola iscrizione** su ordine confermato: la riga non si può eliminare, si
  porta la **quantità a zero**. Non iscrive e non entra nei conguagli;
- **annullare l'intero ordine** non elimina il registro già creato: va archiviato a parte.

---

<a id="g-15"></a>
## G-15 · Ciclo passivo

<a id="g-16"></a>
### G-16 · Prodotto ore

`Acquisti → Prodotti → Prodotti → Nuovo` → **"Ora di insegnamento"**:

- **Tipo Servizio**, **Può essere acquistato** attivo, **Unità di misura = Ore** — così la
  quantità di riga è direttamente il monte ore;
- **Costo**: la tariffa di riserva, usata solo per insegnanti senza listino;
- **Imposte acquisti**: dipendono dal **regime fiscale dell'insegnante** — ordinario con
  imposta, forfettario o prestazione occasionale senza. Va verificato, non è una preferenza.

<a id="g-17"></a>
### G-17 · Tariffa per insegnante

Sul prodotto, tab **Acquisti → Fornitori → Aggiungi riga**: **Fornitore** = il contatto
dell'insegnante, **Prezzo** = la sua tariffa oraria. Una riga per insegnante.

⚠️ Dev'essere **esattamente il Contatto lavoro** della scheda dipendente. Se si sbaglia
contatto — o se ne crea uno nuovo omonimo dalla tendina — il sistema non protesta: usa la
tariffa di riserva e produce un compenso sbagliato in silenzio.

<a id="g-18"></a>
### G-18 · Prodotto predefinito

`Acquisti → Configurazione → Impostazioni` → sezione **Ordini** → **Prodotto ore insegnante**
= "Ora di insegnamento" → **Salva**. Serve solo a proporlo già compilato.

<a id="g-19"></a>
### G-19 · Liquidare il compenso

`Acquisti → Compenso ore insegnante`:

- **Insegnante** (obbligatorio);
- **Corso**: filtro facoltativo — vuoto significa **tutti i corsi**;
- **Prodotto ore**: già proposto, modificabile;
- **Crea ordine**.

Nasce un **ordine d'acquisto in bozza** intestato all'insegnante, con una riga per lezione
svolta, quantità pari alle ore e prezzo pari alla sua tariffa.

- le lezioni **senza ore** non entrano;
- conta **chi ha registrato** le ore, non chi è responsabile del corso: un supplente riceve un
  ordine proprio, per le sole lezioni che ha tenuto;
- le ore già liquidate **non vengono riprese**: rilanciando si ottiene *"Nessuna ora da
  liquidare"*;
- **annullando** l'ordine le ore tornano liquidabili.

<a id="g-20"></a>
### G-20 · Fattura fornitore

Sull'ordine: **Conferma ordine** → **Crea fattura**. Nasce la fattura fornitore in bozza, con
il totale delle ore per la tariffa. È il documento contro cui l'insegnante emette la propria.

---

<a id="g-21"></a>
## G-21 · Ciclo di validazione

Da eseguire su un ambiente vuoto quando se ne prepara uno nuovo: tre studenti, due corsi, un
insegnante e un supplente.

<a id="g-22"></a>
### G-22 · Simulazione

1. due aule, un insegnante con la sua utenza;
2. un registro collettivo e un modello individuale, entrambi con 4 lezioni previste;
3. i due corsi a catalogo, senza IVA, collegati come da [G-08](#g-08);
4. due studenti, uno minorenne col genitore come recapito e uno adulto;
5. iscrizione del primo a entrambi i corsi, del secondo al solo individuale;
6. generazione delle lezioni sui tre registri;
7. l'insegnante svolge le prime tre lezioni di ciascun individuale e la prima del collettivo,
   un'ora per lezione; su una lezione registra un'**assenza giustificata**;
8. **terzo studente a metà anno**: si iscrive quando il collettivo è già cominciato, con
   lezioni previste e prezzo ridotti al residuo, e parte da zero sull'individuale;
9. si completano le lezioni rimaste, **recuperando** anche quelle inizialmente non tenute;
10. si crea il prodotto ore con due tariffe, si liquida l'insegnante e poi il supplente.

<a id="g-23"></a>
### G-23 · Verifiche — ciclo attivo

- l'iscrizione è intestata **allo studente**, e le righe aggiunte a un ordine confermato
  iscrivono comunque;
- i registri individuali nascono dal modello **senza lezioni ereditate**;
- gli iscritti sono **derivati dagli ordini** e non modificabili a mano;
- lo studente arrivato a metà anno **non compare** nelle lezioni già svolte, e l'allineamento
  lo aggiunge **solo** a quelle future;
- il consuntivo presenze separa correttamente chi paga da chi non paga;
- le detrazioni corrispondono alla formula, e **il recupero di una lezione le riduce**;
- le ore totali corrispondono al numero di lezioni svolte.

<a id="g-24"></a>
### G-24 · Verifiche — ciclo passivo

- l'ordine è intestato all'insegnante, una riga per lezione svolta, con la **sua tariffa** e
  non quella di riserva;
- le lezioni senza ore non compaiono;
- il **supplente** riceve un ordine distinto, con le sole ore registrate da lui;
- rilanciando la liquidazione: **nessuna ora da liquidare**;
- annullando l'ordine le ore tornano liquidabili e una nuova liquidazione le ripropone;
- la fattura fornitore riporta il totale delle ore per la tariffa.

---

<a id="g-25"></a>
## G-25 · Cose da sapere

- **Le stampe in PDF non sono disponibili** in questa versione: i pulsanti di stampa
  falliscono. Consultazione a schermo e consuntivi funzionano normalmente.
- **Cambiare prodotto o quantità su una riga d'ordine ricalcola il prezzo dal catalogo** e
  sovrascrive quello concordato. È il modo più facile di perdere uno sconto accordato mesi
  prima.
- **Una sola registrazione di ore per lezione**: due registrazioni parziali sulla stessa
  lezione falsano la data nei consuntivi.
- **Le fasi colorate delle lezioni sono solo organizzazione visiva**: nessun calcolo le legge.
  Lo stato reale si legge dai filtri "svolte" e "da svolgere".
- **I conguagli sono calcolati all'apertura**: dopo aver registrato ore o presenze, riaprire
  la voce di menu per vedere i valori aggiornati.
