from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Enrollment(models.TransientModel):
    _name = 'bandoo.enrollment'
    _description = 'Iscrizione a corso'

    student_id = fields.Many2one(
        'res.partner', string='Studente', required=True,
        domain=[('x_is_student', '=', True), ('x_is_member', '=', True)],
    )
    guardian_id = fields.Many2one(
        'res.partner', string='Intestatario retta', required=True,
        help='Genitore/pagatore a cui viene intestato l’ordine.',
    )
    instrument_project_id = fields.Many2one(
        'project.project', string='Corso strumento', required=True,
        domain=[('x_is_course', '=', True), ('x_is_solfeggio', '=', False)],
    )
    instrument_price = fields.Float(string='Prezzo strumento')
    add_solfeggio = fields.Boolean(string='Aggiungi solfeggio', default=True)
    solfeggio_project_id = fields.Many2one(
        'project.project', string='Corso solfeggio',
        domain=[('x_is_course', '=', True), ('x_is_solfeggio', '=', True)],
        default=lambda self: self._default_solfeggio(),
    )
    solfeggio_price = fields.Float(string='Prezzo solfeggio')

    def _default_solfeggio(self):
        return self.env['project.project'].search([
            ('x_is_course', '=', True), ('x_is_solfeggio', '=', True),
        ], limit=1)

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id:
            self.guardian_id = self.student_id.parent_id or self.student_id

    @api.onchange('instrument_project_id')
    def _onchange_instrument(self):
        if self.instrument_project_id:
            self.instrument_price = self.instrument_project_id.x_list_price

    @api.onchange('add_solfeggio', 'solfeggio_project_id')
    def _onchange_solfeggio(self):
        if self.add_solfeggio and not self.solfeggio_project_id:
            self.solfeggio_project_id = self._default_solfeggio()
        if self.solfeggio_project_id:
            self.solfeggio_price = self.solfeggio_project_id.x_list_price

    def action_create_order(self):
        self.ensure_one()
        if not self.student_id.x_is_member:
            raise UserError(_('Lo studente deve essere socio per iscriversi.'))
        if self.add_solfeggio and not self.solfeggio_project_id:
            raise UserError(
                _('Seleziona il corso di solfeggio o disattiva il relativo toggle.'))
        if self.add_solfeggio \
                and self.solfeggio_project_id == self.instrument_project_id:
            raise UserError(_('Strumento e solfeggio devono essere corsi diversi.'))

        product = self.env.ref('bandoo_school_sale.product_enrollment')

        def _line(project, price):
            return (0, 0, {
                'product_id': product.id,
                'x_student_id': self.student_id.id,
                'x_project_id': project.id,
                'name': project.display_name,
                'price_unit': price,
                'product_uom_qty': 1.0,
            })

        lines = [_line(self.instrument_project_id, self.instrument_price)]
        if self.add_solfeggio:
            lines.append(_line(self.solfeggio_project_id, self.solfeggio_price))

        order = self.env['sale.order'].create({
            'partner_id': self.guardian_id.id,
            'order_line': lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Iscrizione'),
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }
