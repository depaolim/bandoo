from odoo import fields, models


class BandooRoom(models.Model):
    _name = 'bandoo.room'
    _description = 'Aula'
    _order = 'name'

    name = fields.Char(string='Aula', required=True)
