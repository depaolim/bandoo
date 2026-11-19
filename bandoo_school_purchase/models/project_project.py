from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Lo stesso insegnante è pagato per tipo di lezione (`S-11`): il tipo è un
    # prodotto ore di acquisto, e il corso dice quale. Gli individuali lo
    # ricevono dal modello di progetto, copiato alla conferma da sale_project:
    # niente copy=False. I collettivi lo ricevono a mano alla pianificazione.
    x_teacher_hour_product_id = fields.Many2one(
        'product.product', string='Prodotto ore insegnante',
        domain=[('purchase_ok', '=', True)],
        help="Prodotto di acquisto con cui si pagano all'insegnante le ore "
             "delle lezioni di questo corso (es. «Ore strumento», "
             "«Ore solfeggio»): la tariffa è il suo costo. Per i corsi "
             "individuali si imposta sul modello di progetto, che lo passa ai "
             "corsi creati da lì; per i collettivi si imposta sul corso. "
             "Senza, il consuntivo insegnante si ferma.",
    )
