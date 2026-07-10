from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            for line in order.order_line:
                if not line.product_id.x_is_course:
                    continue
                if not line.x_student_id:
                    raise UserError(_(
                        'Riga "%s": indicare lo studente da iscrivere.',
                        line.product_id.display_name))
                if not line.x_student_id.x_is_member:
                    raise UserError(_(
                        'Lo studente %s deve essere socio per iscriversi.',
                        line.x_student_id.display_name))
        return super().action_confirm()
