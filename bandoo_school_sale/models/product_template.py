from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # In minuti, che e' l'unita' in cui la scuola parla: 30, 45, 60 per lo
    # strumento, 15 per allievo nel solfeggio. Le ore decimali servono solo
    # ai fogli ore, e la divisione sta li'.
    x_lesson_duration = fields.Integer(
        string='Quota (minuti per allievo)',
        help="Minuti di insegnante per allievo per lezione: la durata della "
             "lezione nei corsi individuali, la parte di ciascun allievo nei "
             "collettivi. Le lezioni previste sono le ore dell'unità di "
             "misura divise per la quota.",
    )
    x_lesson_target = fields.Integer(
        string='Lezioni previste', compute='_compute_x_lesson_target',
        help="Lezioni incluse nel prezzo annuale, saggi compresi: le ore "
             "dell'unità di misura divise per la quota.",
    )
    # Un prodotto è un corso a catalogo quando ha una quota
    x_is_course = fields.Boolean(compute='_compute_x_is_course')

    @api.depends('x_lesson_duration')
    def _compute_x_is_course(self):
        for product in self:
            product.x_is_course = product.x_lesson_duration > 0

    @api.depends('x_lesson_duration', 'uom_id')
    def _compute_x_lesson_target(self):
        for product in self:
            product.x_lesson_target = product._x_lessons_in(1.0, product.uom_id)

    def _x_lessons_in(self, qty, uom):
        """Lezioni contenute in `qty` unità `uom` del corso a catalogo.

        Arrotondate all'intero e non troncate: una quantità a due decimali
        (17 lezioni su 30 = 0,57) porta un errore fino a 0,15 lezioni, che
        l'arrotondamento recupera e il troncamento no. La stessa formula sta
        nella view SQL del consuntivo allievo.
        """
        self.ensure_one()
        hour = self.env.ref('uom.product_uom_hour')
        if not self.x_lesson_duration or not uom or uom.category_id != hour.category_id:
            return 0
        hours = qty / uom.factor * hour.factor
        return int(float_round(hours * 60 / self.x_lesson_duration,
                               precision_digits=0))

    @api.constrains('x_lesson_duration', 'uom_id',
                    'project_template_id', 'service_tracking', 'type')
    def _check_course_configuration(self):
        hour = self.env.ref('uom.product_uom_hour')
        for product in self:
            if not product.x_is_course:
                if product.service_tracking == 'project_only':
                    raise ValidationError(_(
                        'Un corso a catalogo individuale richiede la quota.'))
                continue
            if product.type != 'service':
                raise ValidationError(_(
                    'Un corso a catalogo deve essere un servizio.'))
            if product.service_tracking not in ('project_only', 'no'):
                raise ValidationError(_('Un corso a catalogo deve essere individuale o collettivo.'))
            # Fuori da Orario lavorativo `sale_timesheet` non calcola il monte
            # ore, e le lezioni previste non si possono ricavare.
            if product.uom_id.category_id != hour.category_id:
                raise ValidationError(_(
                    "Un corso a catalogo si vende in un'unità di misura "
                    "annua (es. «Anno 45′»), non in «%s».",
                    product.uom_id.name))
            if product.service_tracking == 'project_only':
                if not product.project_template_id:
                    raise ValidationError(_(
                        'Un corso a catalogo individuale richiede il modello di progetto.'))

    def write(self, vals):
        """Quota e unità di misura bloccate quando il corso a catalogo ha
        iscrizioni confermate.

        Le lezioni previste di ogni riga si ricavano da quei due dati, non
        sono copiate: cambiarli riscriverebbe i consuntivi allievo già
        calcolati, anni passati compresi. Per un'offerta diversa si crea un
        corso a catalogo nuovo.
        """
        if {'x_lesson_duration', 'uom_id'} & vals.keys():
            changed = self.filtered(lambda p: (
                vals.get('x_lesson_duration', p.x_lesson_duration)
                != p.x_lesson_duration
                or vals.get('uom_id', p.uom_id.id) != p.uom_id.id))
            if changed and self.env['sale.order.line'].sudo().search_count([
                    ('product_id.product_tmpl_id', 'in', changed.ids),
                    ('state', '=', 'sale')], limit=1):
                raise UserError(_(
                    'Quota e unità di misura non si cambiano su un corso a '
                    'catalogo con iscrizioni confermate: le lezioni previste '
                    'di quelle iscrizioni ne dipendono. Crea un nuovo corso a '
                    'catalogo.'))
        return super().write(vals)
