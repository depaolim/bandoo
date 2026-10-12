from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # Cambiano cosa paga l'ordine ore insegnante: ore, a chi, per quale lezione.
    _TEACHER_BILLED_FIELDS = {'unit_amount', 'employee_id', 'task_id', 'project_id'}

    x_teacher_bill_line_id = fields.Many2one(
        'purchase.order.line', string='Riga ordine ore insegnante',
        copy=False, ondelete='set null', index=True,
        help="Riga d'ordine d'acquisto che liquida queste ore. "
             "Vuoto = ore non ancora liquidate. Si azzera se l'ordine "
             "viene annullato o la riga eliminata.",
    )

    def _check_can_write(self, values):
        """Ore già in un ordine ore insegnante: non si cambiano (`S-11`).

        L'ordine copia le ore al momento della creazione e non le rilegge:
        cambiarle dopo lo lascerebbe a pagare ore che non ci sono più.
        """
        if (self._TEACHER_BILLED_FIELDS & values.keys()
                and self.filtered('x_teacher_bill_line_id')):
            raise UserError(_(
                "Queste ore sono già in un ordine ore insegnante: "
                "annulla l'ordine, o togline la riga, prima di modificarle."))
        return super()._check_can_write(values)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_teacher_billed(self):
        if self.filtered('x_teacher_bill_line_id'):
            raise UserError(_(
                "Queste ore sono già in un ordine ore insegnante: "
                "annulla l'ordine, o togline la riga, prima di eliminarle."))
