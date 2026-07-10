from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_student_id = fields.Many2one(
        'res.partner', string='Studente',
        domain=[('is_company', '=', False)],
    )
    x_project_id = fields.Many2one(
        'project.project', string='Corso',
        compute='_compute_x_project_id', store=True,
    )

    @api.depends('project_id', 'product_id')
    def _compute_x_project_id(self):
        """Progetto del corso: per gli individuali è quello generato alla
        conferma (project_id standard), per i collettivi quello condiviso
        indicato sul prodotto."""
        for line in self:
            line.x_project_id = (
                line.project_id or line.product_id.x_course_project_id
            )
