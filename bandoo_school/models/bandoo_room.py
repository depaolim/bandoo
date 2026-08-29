from odoo import api, fields, models


class BandooRoom(models.Model):
    _name = 'bandoo.room'
    _description = 'Aula'
    # Edificio prima: l'elenco raggruppa da sé le sale della stessa sede.
    _order = 'building, name'

    name = fields.Char(string='Sala', required=True)
    # Volutamente non obbligatorio (`D-26`).
    building = fields.Char(
        string='Edificio', help='Sede in cui si trova la sala.')

    @api.depends('building', 'name')
    def _compute_display_name(self):
        """L'etichetta unita si compone qui e basta: lezione, calendario e
        wizard mostrano l'aula per riferimento e passano tutti da qui."""
        for room in self:
            room.display_name = ' - '.join(
                part for part in (room.building, room.name) if part)
