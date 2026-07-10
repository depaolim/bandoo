from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_enrollment_line_ids = fields.One2many(
        'sale.order.line', 'x_project_id', string='Righe di iscrizione')
    # Ridichiarato per dare al compute (in bandoo_school) le dipendenze
    # reali: senza, il valore resterebbe in cache anche dopo la conferma
    # o l'annullamento di un ordine nella stessa transazione.
    enrolled_student_ids = fields.Many2many(
        'res.partner', string='Studenti iscritti',
        compute='_compute_enrolled_student_ids',
        depends=['x_enrollment_line_ids.state',
                 'x_enrollment_line_ids.x_student_id'],
    )

    def _get_enrolled_students(self):
        """Iscritti = studenti delle righe d'ordine confermate del corso."""
        self.ensure_one()
        lines = self.x_enrollment_line_ids.filtered(
            lambda l: l.state == 'sale' and l.x_student_id)
        return super()._get_enrolled_students() | lines.x_student_id
