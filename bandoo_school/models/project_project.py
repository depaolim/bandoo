from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    enrolled_student_ids = fields.Many2many(
        'res.partner',
        'project_enrolled_student_rel',
        'project_id',
        'partner_id',
        string='Studenti iscritti',
        domain=[('is_company', '=', False)],
    )
