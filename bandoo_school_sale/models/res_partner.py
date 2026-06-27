from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_member = fields.Boolean(string='Socio', default=False)
    x_guardian_id = fields.Many2one(
        'res.partner', string='Genitore/Pagatore',
        help='Soggetto a cui è intestata la retta dello studente.',
    )
