from odoo import fields, models, tools


class LessonAttendance(models.Model):
    _name = 'bandoo.lesson.attendance'
    _description = 'Consuntivo presenze lezioni'
    _auto = False
    _rec_name = 'partner_id'

    task_id = fields.Many2one('project.task', string='Lezione', readonly=True)
    project_id = fields.Many2one('project.project', string='Corso', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Studente', readonly=True)
    status = fields.Selection([
        ('present', 'Presente'),
        ('absent', 'Assente'),
    ], string='Stato', readonly=True)
    date = fields.Date(string='Data lezione', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW bandoo_lesson_attendance AS
            SELECT
                row_number() OVER () AS id,
                sl.task_id,
                sl.project_id,
                sl.partner_id,
                sl.status,
                MIN(al.date) AS date
            FROM bandoo_lesson_student_line sl
            JOIN account_analytic_line al ON al.task_id = sl.task_id
            GROUP BY sl.task_id, sl.project_id, sl.partner_id, sl.status
        """)
