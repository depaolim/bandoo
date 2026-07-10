from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_member = fields.Boolean(string='Socio', default=False)
