from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            for line in order.order_line:
                if line.x_project_id and line.x_student_id:
                    # (4, id) è idempotente: ri-confermare non duplica l'iscrizione.
                    line.x_project_id.enrolled_student_ids = [
                        (4, line.x_student_id.id)
                    ]
        return res
