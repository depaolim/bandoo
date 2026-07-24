from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    x_teacher_bill_line_id = fields.Many2one(
        'purchase.order.line', string='Riga ordine compenso',
        copy=False, ondelete='set null', index=True,
        help="Riga d'ordine d'acquisto che liquida queste ore. "
             "Vuoto = ore non ancora liquidate. Si azzera se l'ordine "
             "viene annullato o la riga eliminata.",
    )
