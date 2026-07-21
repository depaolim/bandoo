# Addon Bandoo

Addon Odoo 18 per il progetto Bandoo — una scuola di musica costruita sopra
le app Progetto, Foglio ore e Vendite di Odoo.

Tre moduli, stratificati per dipendenza:

## bandoo_school

Dominio principale: corsi, lezioni, presenze.

- I corsi sono record `project.project`; le lezioni sono record `project.task`
  (con aula, insegnante e un flag "svolta").
- `bandoo.room` — le aule fisiche.
- `bandoo.lesson.student.line` — presenza del singolo studente su ogni lezione,
  con uno stato (presente / giustificato / ingiustificato) e uno stato di
  fatturazione calcolato.
- `bandoo.lesson.attendance` — vista SQL in sola lettura che aggrega le presenze
  per la reportistica.
- Procedura guidata `bandoo.lesson.generate` — genera in blocco le lezioni
  ricorrenti di un corso (data di inizio, orario, numero, intervallo settimanale).

Dipende da: `project`, `hr_timesheet`, `contacts`.

## bandoo_school_sale

Strato vendite sopra `bandoo_school`: iscrizioni, rette e conguaglio.

- Un `product.template` può essere marcato come corso e collegato a un progetto
  corso; una `sale.order.line` porta allora lo studente iscritto e il numero di
  lezioni previste.
- `bandoo.enrollment.settlement` — conguaglio per iscrizione: prezzo annuo,
  lezioni svolte, assenze giustificate, prezzo per lezione, detrazione e le tre
  rate.
- `bandoo.order.settlement` — conguaglio per ordine, aggrega le righe.
- `res.partner` acquisisce il flag `Socio`.

Dipende da: `bandoo_school`, `sale_management`, `sale_project`.

## bandoo_branding

Branding della pagina di login e meta-modulo che fissa l'elenco completo dei
moduli da installare per un'istanza Bandoo.

- Logo personalizzato e template di login.
- Il suo elenco `depends` è di fatto il manifest d'installazione del deployment
  (HR, presenze, fogli ore, portale, dashboard spreadsheet, TOTP, …), inclusi
  `bandoo_school` e `bandoo_school_sale`.
