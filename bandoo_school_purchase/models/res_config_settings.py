from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    teacher_hour_product_id = fields.Many2one(
        'product.product', string='Prodotto ore insegnante',
        domain=[('purchase_ok', '=', True)],
        config_parameter='bandoo_school_purchase.teacher_hour_product_id',
        help="Prodotto proposto di default dal wizard "
             "\"Consuntivo insegnante\". È un prodotto normale: il prezzo "
             "per insegnante si imposta nel suo listino fornitore.",
    )
