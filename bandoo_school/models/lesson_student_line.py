from odoo import fields, models


class LessonStudentLine(models.Model):
    _name = 'bandoo.lesson.student.line'
    _description = 'Presenza lezione'
    _order = 'partner_id'

    task_id = fields.Many2one('project.task', ondelete='cascade', required=True)
    project_id = fields.Many2one(
        related='task_id.project_id', store=True, precompute=True,
    )
    partner_id = fields.Many2one('res.partner', string='Studente', required=True)
    status = fields.Selection([
        ('present', 'Presente'),
        ('absent', 'Assente'),
        ('absent_justified', 'Assente giustificato'),
    ], string='Stato', default='present', required=True)
    note = fields.Char(string='Note')

    _sql_constraints = [
        ('unique_task_partner', 'UNIQUE(task_id, partner_id)',
         'Lo studente è già nella lista presenze di questa lezione.'),
    ]
