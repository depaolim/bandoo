from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """Alla conferma gli allievi entrano nelle lezioni dei loro corsi.

        Serve ai corsi collettivi già indicati sulla riga prima della
        conferma: le loro lezioni non rendicontate ricevono il nuovo
        iscritto (`S-08`). I corsi individuali nascono qui, senza lezioni.
        """
        res = super()._action_confirm()
        # Manutenzione del registro scuola, non un'azione dell'utente: come
        # `sale_project` per la generazione dei corsi, chi conferma o annulla
        # può non avere accesso a Progetti.
        self.order_line.project_id.sudo().action_align_attendance()
        return res

    def _action_cancel(self):
        """All'annullamento gli allievi escono dalle lezioni non rendicontate
        dei loro corsi; quelle rendicontate restano, sono la storia (`S-08`).
        """
        res = super()._action_cancel()
        # Manutenzione del registro scuola, non un'azione dell'utente: come
        # `sale_project` per la generazione dei corsi, chi conferma o annulla
        # può non avere accesso a Progetti.
        self.order_line.project_id.sudo().action_align_attendance()
        return res
