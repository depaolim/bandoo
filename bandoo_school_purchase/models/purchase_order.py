from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_cancel(self):
        # Annullare l'ordine libera le ore: tornano liquidabili da un nuovo
        # ordine. La cancellazione della singola riga è già coperta da
        # ondelete='set null' sul link del timesheet.
        res = super().button_cancel()
        self.env['account.analytic.line'].search([
            ('x_teacher_bill_line_id', 'in', self.order_line.ids),
        ]).write({'x_teacher_bill_line_id': False})
        return res
