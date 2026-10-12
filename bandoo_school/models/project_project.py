from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Durata della singola lezione, in minuti. La portano le lezioni come
    # "Tempo assegnato" (allocated_hours, in ore): e' l'unico termine di
    # confronto delle ore che l'insegnante registra, e su cui si fonda il
    # compenso.
    x_lesson_duration = fields.Integer(
        string='Durata lezione (minuti)',
        help='Durata di una lezione di questo corso. Ogni lezione nuova nasce '
             'con il Tempo assegnato corrispondente.')
    # Lezioni previste: le lezioni ordinarie più i saggi, che sono lezioni a
    # tutti gli effetti (fogli ore, presenze, ore insegnante) e rientrano nel
    # prezzo annuale. È il numero su cui il consuntivo allievo divide il
    # prezzo. Nessun default: un numero che nessuno ha scelto non va proposto.
    x_lesson_target = fields.Integer(
        string='Lezioni previste',
        help='Lezioni coperte dalla quota annua: le lezioni ordinarie '
             'piu\' i saggi. Il wizard ne propone di meno da generare, '
             'perche\' la data dei saggi si sa solo dopo.')
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
