from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Durata della lezione del gruppo, in minuti: vale per i corsi con più
    # allievi, che la decidono alla pianificazione (`S-08`). La portano le
    # lezioni come "Tempo assegnato" (allocated_hours, in ore): e' l'unico
    # termine di confronto delle ore che l'insegnante registra, e su cui si
    # fonda il compenso.
    x_lesson_duration = fields.Integer(
        string='Durata lezione (minuti)',
        help='Durata di una lezione di questo corso. Ogni lezione nuova nasce '
             'con il Tempo assegnato corrispondente.')
    enrolled_student_ids = fields.Many2many(
        'res.partner', string='Allievi iscritti',
        compute='_compute_enrolled_student_ids',
    )
    x_enrolled_count = fields.Integer(
        string='Iscritti', compute='_compute_x_enrolled_count')

    @api.depends('enrolled_student_ids')
    def _compute_x_enrolled_count(self):
        for project in self:
            project.x_enrolled_count = len(project.enrolled_student_ids)

    def _get_enrolled_students(self):
        """Elenco iscritti al corso.

        Base: nessuna fonte. I moduli a valle estendono derivando
        dalla loro fonte di verità (es. righe d'ordine confermate).
        """
        self.ensure_one()
        return self.env['res.partner']

    def _get_lesson_duration(self):
        """Durata di una lezione del corso, in minuti.

        Base: quella scritta sul corso. I moduli a valle la ricavano da dove
        sta davvero, per esempio dal corso a catalogo della riga d'ordine.
        """
        self.ensure_one()
        return self.x_lesson_duration

    def _get_lesson_target(self):
        """Lezioni previste del corso, saggi compresi: 0 se non si sanno.

        Base: nessuna fonte. Le ricava chi conosce la vendita.
        """
        self.ensure_one()
        return 0

    def _get_recital_count(self):
        """Saggi da escludere dalle lezioni da generare. Base: nessuno."""
        self.ensure_one()
        return 0

    def _compute_enrolled_student_ids(self):
        for project in self:
            project.enrolled_student_ids = project._get_enrolled_students()

    def action_align_attendance(self):
        """Allinea le presenze delle lezioni non rendicontate agli iscritti
        del corso, nei due sensi: aggiunge chi manca, toglie chi non è più
        iscritto (`S-08`). Idempotente.

        Conta la rendicontazione, non la data: una lezione tenuta ma senza
        foglio ore è ancora da allineare. Le lezioni rendicontate non si
        toccano: sono la storia, e il consuntivo allievo si basa su quelle.

        Togliere un iscritto cancella anche l'esito già segnato su una
        lezione non rendicontata.
        """
        for project in self:
            students = project._get_enrolled_students()
            for task in project.task_ids.filtered(lambda t: not t.timesheet_ids):
                lines = task.attendance_line_ids
                missing = students - lines.partner_id
                lines.filtered(lambda l: l.partner_id not in students).unlink()
                if missing:
                    task.attendance_line_ids = [
                        (0, 0, {'partner_id': s.id, 'status': 'present'})
                        for s in missing]
