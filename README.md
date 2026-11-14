# Addon Bandoo

Addon Odoo 18 per Bandoo — una scuola di musica costruita sulle app Progetto,
Foglio ore e Vendite. Quattro moduli stratificati per dipendenza.

## bandoo_school

Dominio: corsi, lezioni, presenze. I corsi sono `project.project`, le lezioni
`project.task` (aula, insegnante, flag "svolta"). Aggiunge `bandoo.room` (aule),
`bandoo.lesson.student.line` (presenza del singolo studente, con stato e stato di
fatturazione calcolato), la vista SQL `bandoo.lesson.attendance` per la
reportistica e la procedura `bandoo.lesson.generate` per generare in blocco le
lezioni ricorrenti.

Dipende da: `project`, `hr_timesheet`, `contacts`.

## bandoo_school_sale

Iscrizioni, rette e conguaglio sopra `bandoo_school`. L'iscrizione è un
`sale.order` standard **intestato allo studente** (che è anche l'iscritto); un
`product.template` è marcato come corso tramite il tracciamento (individuale con
template di progetto, collettivo con progetto condiviso) e si vende in
un'unità di misura annua della categoria Orario lavorativo, con la quota in
minuti per allievo: le lezioni previste della `sale.order.line` si ricavano
dalla quantità, e il monte ore del corso individuale è lezioni previste per
quota. Espone due viste SQL di conguaglio:
`bandoo.enrollment.settlement` (per iscrizione: prezzo annuo, lezioni svolte,
assenze giustificate, detrazione, rate) e `bandoo.order.settlement` (per ordine).

Dipende da: `bandoo_school`, `sale_management`, `sale_project`, `sale_timesheet`.

## bandoo_school_purchase

Consuntivo insegnante sopra `bandoo_school`. L'insegnante è un fornitore: la procedura
`bandoo.teacher.hours.bill` raccoglie le sue rendicontazioni non ancora liquidate e ne fa un
ordine di acquisto intestato al suo contatto di lavoro, una riga per lezione con le ore
rendicontate. Il prodotto di ogni riga è il **prodotto ore** del corso della lezione
(`x_teacher_hour_product_id` su `project.project`, ereditato dal modello di progetto): un
prodotto per tipo di lezione, col costo come tariffa; il prezzo lo calcola purchase. Le ore in
ordine sono bloccate; annullare l'ordine le libera.

Dipende da: `bandoo_school`, `purchase`.

## bandoo_branding

Branding della pagina di login e meta-modulo il cui elenco `depends` è il manifest
d'installazione dell'istanza Bandoo (stack HR, presenze, fogli ore, portale, …,
inclusi gli altri due moduli).
