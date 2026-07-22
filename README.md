# Addon Bandoo

Addon Odoo 18 per Bandoo — una scuola di musica costruita sulle app Progetto,
Foglio ore e Vendite. Tre moduli stratificati per dipendenza.

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
template di progetto, collettivo con progetto condiviso) e la `sale.order.line`
porta il corso e le lezioni previste. Espone due viste SQL di conguaglio:
`bandoo.enrollment.settlement` (per iscrizione: prezzo annuo, lezioni svolte,
assenze giustificate, detrazione, rate) e `bandoo.order.settlement` (per ordine).

Dipende da: `bandoo_school`, `sale_management`, `sale_project`.

## bandoo_branding

Branding della pagina di login e meta-modulo il cui elenco `depends` è il manifest
d'installazione dell'istanza Bandoo (stack HR, presenze, fogli ore, portale, …,
inclusi gli altri due moduli).
