from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_lesson_target = fields.Integer(string='Lezioni previste', default=28)
    enrolled_student_ids = fields.Many2many(
        'res.partner', string='Studenti iscritti',
        compute='_compute_enrolled_student_ids',
    )

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

    def action_align_future_attendance(self):
        """Aggiunge gli iscritti mancanti alle presenze delle lezioni
        non ancora svolte (senza ore registrate). Idempotente."""
        for project in self:
            students = project._get_enrolled_students()
            for task in project.task_ids.filtered(lambda t: not t.timesheet_ids):
                missing = students - task.attendance_line_ids.partner_id
                if missing:
                    task.attendance_line_ids = [
                        (0, 0, {'partner_id': student.id, 'status': 'present'})
                        for student in missing
                    ]
