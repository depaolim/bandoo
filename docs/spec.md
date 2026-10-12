# Specifica — anagrafica, catalogo, iscrizioni, registro scuola, consuntivazione

> ⚠️ **Due funzionalità vanno accese prima di configurare il catalogo**, in
> `Vendite → Configurazione → Impostazioni`: **Varianti prodotto** e **Listini prezzi**.
> Senza, i record si creano lo stesso ma restano **invisibili** — niente menu Varianti,
> nessun campo listino — e un salvataggio delle impostazioni può **archiviare i listini**:
> da quel momento le iscrizioni prendono il prezzo di catalogo invece di quello dell'anno,
> senza alcun errore.

---

## S-00 · Glossario

L'**etichetta** è quella che l'utente vede: per gli oggetti standard il nome di Odoo in
italiano, che non si traduce; per le customizzazioni il termine del glossario. Dove bandoo
mostra un'etichetta diversa, è un difetto da correggere.

Annotazioni: *(da confermare)* = termine proposto, non ancora approvato; *(da definire)* =
soluzione ancora da progettare.

**Regole d'uso**

- **«Registro» mai da solo**: in Odoo italiano è il registro contabile (`account.journal`).
  Si dice sempre «registro scuola».
- **Un termine per gli utenti, uno contabile solo nel suo contesto**: *rata 3* per tutti, *saldo*
  solo in contabilità.
- **Un oggetto, un significato**: un lavoro (`project.task`) è sempre e solo una lezione.

### Anagrafiche e ruoli

| Termine | Etichetta | Oggetto Odoo | Descrizione | Sinonimi deprecati |
|---|---|---|---|---|
| Allievo | Contatto | `res.partner` | Persona che frequenta uno o più corsi. È sempre intestataria dell'iscrizione, anche se minorenne. | Alunno, Studente, Scolaro, Partecipante |
| Genitore | Contatto (tab «Contatti e indirizzi») | `res.partner`, figlio dell'allievo | Genitore, o chi ne fa le veci, di un allievo minorenne, registrato come contatto collegato all'allievo. | Referente, Tutore, Responsabile, Adulto responsabile |
| Insegnante *(da confermare)* | Contatto / Utente / Dipendente / Fornitore | `res.partner`, `res.users`, `hr.employee` | Persona che tiene le lezioni, registra le presenze, rendiconta le ore e vende alla scuola le ore insegnante. | Docente, Maestro |
| Segretario *(da confermare)* | Utente | `res.users` | Persona della scuola che gestisce le iscrizioni e assegna gli allievi ai corsi collettivi. | Segreteria |

### Calendario scolastico

| Termine | Etichetta | Oggetto Odoo | Descrizione | Sinonimi deprecati |
|---|---|---|---|---|
| Anno scolastico | — | — | Periodo didattico che inizia in autunno, nel quale la scuola raccoglie le iscrizioni e svolge i corsi. | Anno accademico |

### Registro scuola

Perimetro: corsi, lezioni, presenze e rendicontazioni. Corsi a catalogo, iscrizioni, rate,
consuntivazione e ordini ore insegnante stanno accanto al registro scuola e non ne fanno parte.

| Termine | Etichetta | Oggetto Odoo | Descrizione | Sinonimi deprecati |
|---|---|---|---|---|
| Registro scuola | — (insieme di funzionalità) | — | Meccanismo che gestisce corsi, lezioni, presenze e rendicontazioni. | Registro (da solo) |
| Corso | Progetto | `project.project` | Svolgimento di un corso a catalogo in un anno scolastico, con il suo calendario di lezioni. Può avere uno o più allievi. | Classe, Edizione, Calendario corso, Gruppo, Percorso, Ciclo di lezioni |
| Corso individuale | Progetto | `project.project` | Corso con un solo allievo, creato alla conferma dell'iscrizione a un corso a catalogo individuale. | Classe individuale, Registro |
| Corso collettivo | Progetto | `project.project` | Corso con più allievi, a cui il segretario assegna gli allievi (es. «Solfeggio A 2026/27»). | Classe collettiva, Gruppo |
| Modello di corso individuale | Progetto (usato come modello) | `project.project`, indicato in «Modello progetto» del corso a catalogo | Progetto da cui Odoo copia ogni nuovo corso individuale. Non contiene lezioni: serve solo per la configurazione (fasi, responsabile, fogli ore, fatturabilità). | Modello di classe individuale, Template |
| Lezione | Lavoro | `project.task` | Singolo incontro di un corso, con data prevista, aula e durata prevista. Comprende sia le lezioni ordinarie sia i saggi. | Incontro, Sessione, Task, Appuntamento |
| Lezione ordinaria *(da confermare)* | Lavoro | `project.task` | Lezione didattica, a cadenza tipicamente settimanale, calendarizzata a inizio anno scolastico. | Lezione vera e propria, Lezione normale |
| Saggio | Lavoro | `project.task` | Lezione in forma di esibizione degli allievi, con presenze. La data viene fissata mesi dopo l'inizio dell'anno scolastico. | — |
| Spostamento | Lavoro: Scadenza | `project.task`, data prevista | Modifica della data prevista di una lezione di un corso individuale dopo un'assenza giustificata con preavviso. La lezione resta da svolgere. | Rinvio |
| Recupero | Presenza | `bandoo.lesson.student.line` | Presenza di un allievo, su iniziativa dell'insegnante, a una lezione di un altro corso collettivo dello stesso corso a catalogo, dopo un'assenza giustificata. Conta come lezione erogata e si paga come le altre, fino alle lezioni previste. | Lezione di recupero |
| Aula | Aula | `bandoo.room` | Luogo in cui si tiene una lezione. | Sala, Stanza |
| Presenza | Presenza | `bandoo.lesson.student.line` | Esito della partecipazione di un allievo a una lezione. Vale per corsi individuali e collettivi. | Appello |
| Presente | Presente | — | L'allievo ha partecipato alla lezione. | — |
| Assente | Assente | — | L'allievo non ha partecipato senza giustificazione. La lezione è comunque fruita ai fini del prezzo. | Assente ingiustificato |
| Assente giustificato | Assente giustificato | — | L'allievo non ha partecipato con giustificazione: la lezione è non fruita e non si paga. In un corso individuale, con preavviso, la lezione si sposta (spostamento); in un corso collettivo l'insegnante può offrire un recupero. | Giustificato, Assenza giustificata |
| Registrare le presenze *(verbo)* | — | — | Azione con cui l'insegnante indica l'esito di ciascun allievo per una lezione. | Fare l'appello |
| Lezione non fruita | — (concetto derivato) | — | Lezione rendicontata con esito Assente giustificato, in corsi individuali o collettivi. Non si paga; un recupero si paga e la compensa (`S-09`). | Lezione a pagamento (concetto superato) |
| Rendicontazione | Foglio ore | `account.analytic.line` | Registrazione, fatta dall'insegnante, delle ore effettivamente svolte in una singola lezione. Indica sia l'atto (*rendicontare*) sia il record risultante. Non comprende le presenze. | Firma, Ore svolte, Svolgimento, Registrazione lezione |
| Lezione rendicontata | Rendicontata; filtri «Rendicontate» / «Da rendicontare» | `project.task` | Lezione con almeno una rendicontazione. È l'unico criterio per dire che una lezione è stata tenuta: conta la rendicontazione, non la data (`S-08`). | Svolta |

### Offerta, iscrizioni e rate (accanto al registro scuola)

| Termine | Etichetta | Oggetto Odoo | Descrizione | Sinonimi deprecati |
|---|---|---|---|---|
| Corso a catalogo | Prodotto | `product.template` | Offerta didattica annuale a catalogo, venduta nelle iscrizioni. | Corso (nel senso di prodotto), Tipo di corso, Offerta, Articolo, Prodotto-corso |
| Categoria di corso a catalogo | Categoria prodotto | `product.category` | Raggruppamento dei corsi a catalogo: Strumento bandistico, Strumento non bandistico, Solfeggio. | Categoria di corso |
| Corso a catalogo di strumento | Prodotto | `product.template` | Corso a catalogo la cui materia è uno strumento. Ha una variante per ogni strumento. | — |
| Corso a catalogo di solfeggio | Prodotto | `product.template` | Corso a catalogo la cui materia è il solfeggio. | — |
| Corso a catalogo individuale | Prodotto | `product.template` | Corso a catalogo la cui vendita genera un corso individuale. | — |
| Corso a catalogo collettivo | Prodotto | `product.template` | Corso a catalogo la cui vendita non genera un corso. Il segretario assegna l'allievo a un corso collettivo esistente. | — |
| Strumento | Valore (attributo «Strumento») | `product.attribute.value` | Strumento specifico insegnato (es. tuba, corno, sax, batteria, pianoforte, chitarra). | — |
| Variante di corso a catalogo | Variante prodotto | `product.product` | Corso a catalogo di strumento per uno strumento specifico. È ciò che si vende nella riga di iscrizione. | Variante di corso |
| Lezioni previste *(da confermare)* | Lezioni previste | — | Numero di lezioni, saggi compresi, incluse nel prezzo annuale di un corso a catalogo (tipicamente 28 lezioni ordinarie + 2 saggi). | Appuntamenti previsti |
| Listino | Listino prezzi | `product.pricelist` | Insieme di regole di prezzo, differenziabili per categoria di corso a catalogo. | — |
| Iscrizione | Ordine di vendita | `sale.order` | Atto con cui un allievo si iscrive a uno o più corsi a catalogo per un anno scolastico, a un prezzo fissato. | Contratto, Ordine cliente |
| Riga di iscrizione | Riga ordine di vendita | `sale.order.line` | Singolo corso a catalogo incluso in un'iscrizione. | — |
| Rata | *(da definire)* | *(da definire)* | Ciascuna delle tre quote in cui l'allievo paga il prezzo fissato nell'iscrizione: rata 1 e rata 2, di importo fisso, e rata 3. | — |
| Rata 3 | *(da definire)* | *(da definire)* | Ultima rata, il cui importo risulta dal consuntivo allievo: si riduce in base alle lezioni non fruite. In ambito contabile è il saldo. | Conguaglio, Terza rata; Saldo (ammesso solo come nome contabile interno) |

### Consuntivazione (ponte tra registro scuola, vendite e acquisti)

| Termine | Etichetta | Oggetto Odoo | Descrizione | Sinonimi deprecati |
|---|---|---|---|---|
| Consuntivazione | — (processo) | — | Processo periodico di calcolo che produce i consuntivi degli insegnanti e degli allievi (per la rata 3). | Rendicontazione (nel senso di calcolo periodico) |
| Consuntivo insegnante | Consuntivo insegnante | fogli ore → `purchase.order` | Risultato della consuntivazione per un insegnante: ore insegnante da fatturare alla scuola e relativo importo, formalizzati in un ordine ore insegnante. Comprende le lezioni con allievi assenti o assenti giustificati e le lezioni spostate o con recuperi. | Rendicontazione insegnanti, Compenso |
| Consuntivo allievo | Consuntivo allievo | presenze → `sale.order.line` | Risultato della consuntivazione per un allievo: lezioni fruite e non fruite, da cui deriva l'importo della rata 3. | Rendicontazione allievi, Conguaglio |

### Acquisti (accanto al registro scuola)

| Termine | Etichetta | Oggetto Odoo | Descrizione | Sinonimi deprecati |
|---|---|---|---|---|
| Ore insegnante | Prodotto | `product.template` | Servizio che la scuola acquista dagli insegnanti. | — |
| Ordine ore insegnante *(da confermare)* | Ordine di acquisto | `purchase.order` | Ordine con cui la scuola acquista ore insegnante da un insegnante, a seguito del consuntivo insegnante. | Ordine compenso |

---

## S-10 · Anagrafica

**Cognome e nome** sono due campi obbligatori, su contatti e dipendenti, e si mostrano come
«Cognome Nome». I contatti nuovi nascono **Persona**.

L'**allievo** è il contatto principale e l'intestatario delle sue iscrizioni; il
**genitore** è un contatto associato nella sua scheda, ripetuto per ogni allievo.

L'**insegnante** è un dipendente con utente, creato dalla scheda del dipendente: così ha un
**contatto di lavoro**, che è il fornitore dei suoi ordini ore insegnante (`S-11`).

L'**aula** è edificio e sala, e si mostra come «Edificio - Sala».

---

## S-01 · Catalogo

Si configura **una volta**, con un'eccezione annuale: il corso a catalogo collettivo, uno per
anno (`S-08`).

**Un corso a catalogo di strumento per combinazione di categoria e durata**, più i corsi a
catalogo collettivi. Oggi le categorie sono *bandistico* e *non bandistico* e le durate 30′,
45′ e 60′; il collettivo è il Solfeggio. Ogni corso a catalogo porta le **lezioni
previste**. Quelli di strumento portano anche la **durata in minuti**, hanno «Crea un ordine» =
Progetto e puntano al **modello di corso individuale**, uno per tutti. Il corso a catalogo
collettivo ha «Crea un ordine» = Nulla e non punta a nessun progetto: sono i suoi corsi
collettivi a indicarlo (`S-08`).

**Le varianti sono gli strumenti**: un attributo *Strumento*, di cui ogni corso a catalogo
porta solo i valori che gli competono — gli strumenti della banda (Flauto, Clarinetto,
Tromba… ) sui bandistici, gli altri (oggi il solo Pianoforte) sui non bandistici. Così non
nascono combinazioni impossibili, e aggiungere o togliere uno strumento è un valore
d'attributo: Odoo genera o ritira le varianti da sé. I collettivi non hanno varianti.

**Il prezzo non sta sul prodotto**: sta nel **listino dell'anno**, una regola per corso a
catalogo a livello di prodotto. È il listino a portare l'anno, e senza di lui il modello non
sta in piedi.

I listini per anno sono **due**: quello base e quello del **secondo familiare** (`S-07`).

Sulle iscrizioni nuove Odoo propone il primo listino attivo: il listino base dell'anno sta in
cima, il «Predefinito» e i listini degli anni passati si archiviano. Le iscrizioni confermate
non ne risentono.

---

## S-02 · Progetti, tre famiglie

| | Cosa | Quanti | Quando si creano |
|---|---|---|---|
| Modelli di corso individuale | stampi, non corsi; si **archiviano** dopo averli collegati | uno, comune a tutti i corsi a catalogo di strumento | una volta |
| Corsi collettivi | i corsi con più allievi | quanti ne servono, per corso a catalogo collettivo | **ogni anno**, alla pianificazione (`S-08`) |
| Corsi individuali | i corsi con un solo allievo | uno per riga di iscrizione individuale | alla conferma dell'iscrizione |

| Sul modello | Perché |
|---|---|
| Fogli ore e **Fatturabile** attivi | senza Fatturabile non compare in «Modello progetto» |
| **Nessuna lezione** dentro | la copia porta con sé anche i lavori |
| **Una sola fase**, «Lezione» | il corso individuale eredita le quattro di Odoo come colonne del kanban |
| **Tempo assegnato vuoto** | se valorizzato si copia tale e quale, e il calcolo di `S-06` salta |

L'ordine conta: prima la fase unica, **poi** l'archiviazione. Un modello archiviato non si
modifica senza disarchiviarlo, e ogni corso individuale generato da lì in avanti copia le fasi
che il modello ha in quel momento.

---

## S-03 · Iscrizione

Ordine di vendita intestato **all'allievo**, con il **listino dell'anno** in testata. Ogni
riga di iscrizione porta **prodotto + variante**, cioè corso a catalogo e strumento.

| Sulla riga di iscrizione | Individuale | Collettivo |
|---|---|---|
| Prezzo | dal listino in testata | dal listino in testata |
| Lezioni previste | dal corso a catalogo | dal corso a catalogo |
| Insegnante (fra i dipendenti) | facoltativo: diventa responsabile del corso individuale; vuoto → «In attesa di insegnante» | respinto: il responsabile sta sul corso collettivo |
| Corso | — | facoltativo; vuoto → da assegnare (`S-08`) |
| Alla conferma | nasce il corso individuale «\<strumento\> \<durata\> - \<allievo\>» | iscrive al corso collettivo, o a nessuno finché non è assegnato |

**Un corso individuale per iscrizione.** Chi ha bisogno di due strumenti apre una
**seconda iscrizione**. Una riga a quantità zero non fa doppione.

**Dopo la conferma** una riga di iscrizione aggiunta iscrive subito, e una riga portata a
**quantità zero** è annullata: non iscrive e non entra nel consuntivo allievo. Il prezzo
concordato è quello della riga: cambiare prodotto o quantità lo ricalcola dal listino.

**Iscrizione a metà anno**: prezzo e lezioni previste della riga si riducono a mano a quelli
residui; il consuntivo allievo conta su quel numero (`S-09`). Si riducono **prima** di
confermare: sul corso individuale le lezioni previste si copiano alla conferma, e una
riduzione successiva vale per il consuntivo allievo ma non per il corso né per il wizard
Genera lezioni.

---

## S-04 · Assegnazione e lezioni

Se il corso individuale è nato senza responsabile, la scuola glielo mette ora. Poi il wizard
**Genera lezioni** propone quell'insegnante, si sceglie l'**aula**, e le lezioni nascono tutte
con insegnante e aula.

L'aula si sceglie **solo qui**: non risiede né sul corso né sull'insegnante.

Il numero di lezioni proposto viene dalle **lezioni previste del corso**: sul corso
individuale sono quelle della riga di iscrizione, copiate alla conferma, quindi già ridotte per
un'iscrizione a metà anno; sul corso collettivo quelle del suo corso a catalogo.

---

## S-08 · Corsi collettivi

Un corso a catalogo collettivo vale **un anno** e ha **più corsi collettivi** in parallelo,
che possono differire per insegnante, orario e **durata della lezione**. L'allievo sta in un
solo corso collettivo dello stesso corso a catalogo. Prezzo e lezioni previste sono quelli del
corso a catalogo, uguali per tutti i suoi corsi collettivi.

Il corso a catalogo resta annuale perché il consuntivo allievo conta le lezioni su tutti i
suoi corsi collettivi: un corso a catalogo pluriennale sommerebbe gli anni.

| Quando | Cosa fa il segretario |
|---|---|
| **Inizio anno** | crea il corso a catalogo collettivo dell'anno («Crea un ordine» = Nulla, lezioni previste) e la sua regola nei listini. I corsi collettivi non ancora: nascono alla pianificazione |
| **Iscrizione** | aggiunge la riga collettiva all'iscrizione; il **Corso** si compila solo se già deciso. Confermata senza corso, la riga compare nel filtro **«Collettivi da assegnare»** |
| **Pianificazione** | crea i corsi collettivi: progetto con fogli ore e fatturabile, responsabile (l'insegnante), **durata**, **corso a catalogo** di appartenenza. Poi assegna le righe dal filtro — anche su iscrizioni già confermate — e genera le lezioni di ogni corso collettivo (`S-04`). La lista dei corsi collettivi mostra gli iscritti di ciascuno: la capienza è solo informativa |
| **Iscrizione tardiva** | come un'iscrizione, con prezzo e lezioni previste ridotti a mano sulla riga; il corso si può indicare subito |
| **Cambio di corso collettivo** | cambia il Corso sulla riga, e basta: prezzo e lezioni previste non cambiano |

Il corso di una riga di iscrizione è il **campo standard `project_id`** della riga:
sulle righe individuali è il corso individuale generato alla conferma e non si sceglie, sulle
collettive si sceglie fra i corsi collettivi del suo corso a catalogo.

**Le presenze si riallineano da sole.** Quando cambia chi è iscritto a un corso collettivo —
conferma o annullamento dell'iscrizione, riga a quantità zero, corso assegnato o cambiato — le
**lezioni non rendicontate** dei corsi coinvolti ricevono gli iscritti mancanti e perdono chi
non lo è più. Le lezioni rendicontate non si toccano: sono la storia, e il consuntivo allievo
si basa su quelle. Così l'iscritto tardivo entra solo nelle lezioni ancora da fare, e chi
cambia corso collettivo lascia le sue lezioni rendicontate nel primo e prosegue nel secondo.

**Conta la rendicontazione, non la data.** Una lezione tenuta ma ancora non rendicontata è,
per il riallineamento, una lezione da svolgere: un allievo spostato in quella finestra ne
viene tolto.

Il bottone **«Riallinea presenze»** sugli iscritti del corso collettivo fa la stessa cosa a
richiesta: serve da riparazione, non fa parte del flusso.

---

## S-05 · Lezioni previste: 28 lezioni ordinarie più 2 saggi

La quota annua copre **30 lezioni**: 28 lezioni ordinarie e **2 saggi**, uno a metà anno e
uno alla fine. È il numero in «Lezioni previste», ed è su quello che il consuntivo allievo
divide la quota.

**Il saggio è una lezione a tutti gli effetti**: sta nel corso dell'allievo, ha le sue
presenze e la sua rendicontazione, e l'insegnante è pagato per la **durata di quell'allievo**.
Chi porta al saggio due allievi da 30′ e tre da un'ora rendiconta 4 ore, non una.

**Si generano le 28 lezioni ordinarie, non 30.** La data dei saggi si sa solo poche settimane
prima, quindi il wizard ha un campo **«Saggi esclusi»** (2 di serie) e propone di generare
*lezioni previste − saggi*. I due saggi si aggiungono a mano al corso quando la data è nota;
la lezione creata a mano eredita già le presenze dagli iscritti.

⚠️ Generare tutte e 30 le lezioni previste e poi aggiungere i saggi darebbe **32** lezioni, e
il consuntivo allievo ne conterebbe 30 su 30: le lezioni mai erogate sparirebbero senza un
errore.


---

## S-06 · Tempo assegnato

Il corso a catalogo porta la **durata della lezione in minuti**. Alla conferma
dell'iscrizione scende sul corso individuale, e da lì su ogni lezione come **Tempo
assegnato**, in ore. Per i collettivi la durata sta invece sul **corso collettivo** (`S-08`),
e da lì sulle sue lezioni.

| Dove | Valore |
|---|---|
| Lezione | la durata |
| Corso individuale | durata × lezioni previste |

Vale anche per le lezioni aggiunte a mano, saggi compresi.

Odoo ne ricava avanzamento, ore rimanenti e **fuori tempo**: due ore rendicontate su una
lezione da un'ora risultano al 200%, con un'ora fuori tempo.

---

## S-09 · Presenze e consuntivo allievo

Ogni lezione ha una presenza per allievo iscritto, più gli eventuali recuperi, con tre esiti:
**presente**, **assente**, **assente giustificato**. Ai fini della retta i primi due pagano, il
terzo no. Una lezione non rendicontata non conta per nessuno: né per il consuntivo insegnante
né per il consuntivo allievo.

Un'assenza giustificata con preavviso in un corso individuale si gestisce con uno
**spostamento**: la data prevista della lezione cambia e la lezione resta da svolgere, senza
presenza da registrare per la data originale.

**Per riga di iscrizione** (confermata):

- prezzo lezione = prezzo della riga ÷ lezioni previste;
- lezioni erogate = rendicontate in cui l'allievo era in elenco, con qualunque esito, recuperi
  compresi;
- lezioni pagate = erogate − non fruite, al massimo le previste;
- detrazione = (previste − pagate) × prezzo lezione;
- rata 1 e rata 2 = `round(P/3)`, rata 3 = P − rata 1 − rata 2 − detrazione, anche negativa.

Finché le erogate non superano le previste, la detrazione è (non fruite + mai erogate) ×
prezzo lezione, con mai erogate = previste − erogate. Un recupero oltre le previste compensa
una non fruita invece di andare perso sotto il tetto. Un recupero conta solo se la lezione è
rendicontata con l'allievo in elenco: il riallineamento (`S-08`) toglie dalle lezioni non
rendicontate chi non è iscritto al corso.

**Per iscrizione** valgono le stesse rate sul totale, con la somma delle detrazioni; la rata
3 **non scende sotto zero**: un credito oltre l'iscrizione è perso. Sono queste le rate
dovute. Entrambi i consuntivi sono calcolati all'apertura, non memorizzati.

---

## S-07 · Sconto fratelli

Un secondo listino per lo stesso anno, **«Secondo familiare \<anno\>»**, con gli stessi corsi
a catalogo del listino base a prezzi già scontati e arrotondati.

I prezzi sono **fissi**, non una percentuale: si parte dallo sconto deciso per quell'anno e
si arrotonda, quindi la percentuale effettiva varia da un corso a catalogo all'altro. Per
esempio, con uno sconto del 20% arrotondato alla decina, 400 diventa 320 ma 260 diventa 210 —
il 19%.

Il segretario sceglie il listino in testata all'iscrizione del fratello, e vale su tutte le
sue righe. Il listino sull'iscrizione **è** la traccia dello sconto.

---

## S-11 · Consuntivo insegnante

L'insegnante che fattura è un **fornitore**. Il wizard **Consuntivo insegnante** raccoglie le
rendicontazioni **fatte da lui** sulle lezioni e non ancora in un ordine ore insegnante, anche
di un solo corso, e ne fa un **ordine ore insegnante** (ordine di acquisto) intestato al suo
contatto di lavoro: una riga per lezione, quantità = ore. Conta chi rendiconta, non il
responsabile del corso: il supplente ha il suo ordine.

Il prodotto **Ore insegnante** è un servizio normale, proposto dalle impostazioni Acquisti. La
tariffa sta nel **listino fornitore** del prodotto, una riga per insegnante; senza riga vale il
costo del prodotto. Le imposte le decide il regime dell'insegnante.

Le ore messe in ordine non si riprendono; annullando l'ordine tornano liquidabili.
