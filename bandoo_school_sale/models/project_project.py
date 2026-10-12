from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_course_product_id = fields.Many2one(
        'product.template', string='Corso a catalogo',
        domain=[('x_lesson_target', '>', 0), ('service_tracking', '=', 'no')])
    x_enrollment_line_ids = fields.One2many(
        'sale.order.line', 'project_id', string='Righe di iscrizione')
    x_lesson_target = fields.Integer(
        compute='_compute_x_lesson_target', store=True, readonly=False)
    # Ridichiarato per dare al compute (in bandoo_school) le dipendenze
    # reali: senza, il valore resterebbe in cache anche dopo la conferma
    # o l'annullamento di un ordine nella stessa transazione.
    enrolled_student_ids = fields.Many2many(
        'res.partner', string='Allievi iscritti',
        compute='_compute_enrolled_student_ids',
        depends=['x_enrollment_line_ids.state',
                 'x_enrollment_line_ids.order_id.partner_id',
                 'x_enrollment_line_ids.product_uom_qty'],
    )

    @api.depends('x_course_product_id')
    def _compute_x_lesson_target(self):
        for project in self:
            if project.x_course_product_id:
                project.x_lesson_target = project.x_course_product_id.x_lesson_target
            else:
                project.x_lesson_target = project.x_lesson_target

    def _get_enrolled_students(self):
        """Iscritti = allievi delle righe di iscrizione confermate del corso.

        Quantità 0 = riga annullata (convenzione Odoo sugli ordini
        confermati): non iscrive.
        """
        self.ensure_one()
        lines = self.x_enrollment_line_ids.filtered(
            lambda l: l.state == 'sale' and l.product_uom_qty > 0)
        return super()._get_enrolled_students() | lines.order_id.partner_id
