from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_amount

# Campi che decidono il consuntivo allievo o il corso: cambiati a
# iscrizione confermata, lasciano traccia nel chatter. (Il prodotto
# no: `sale_project` non lo lascia cambiare su un servizio confermato)
TRACKED_FIELDS = {
    'price_unit': 'Prezzo unitario',
    'x_lesson_target': 'Lezioni previste',
    'project_id': 'Corso'
}


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_teacher_id = fields.Many2one(
        'res.users', string='Insegnante',
        domain="[('employee_ids', '!=', False)]",
        help="Facoltativo: se l'insegnante è già noto all'iscrizione, "
             "diventa il responsabile del corso individuale alla conferma. "
             "Lasciandolo vuoto il corso nasce in attesa di insegnante.",
    )
    x_lesson_target = fields.Integer(
        string='Lezioni previste', compute='_compute_x_lesson_target',
        store=True, readonly=False,
        help='Lezioni coperte da questa iscrizione, saggi compresi: '
             'proposte dal corso a catalogo, da ridurre prima di confermare '
             'per le iscrizioni a metà anno (il consuntivo allievo detrae le '
             'lezioni mai erogate rispetto a questo numero).',
    )

    @api.depends('product_id')
    def _compute_x_lesson_target(self):
        """Proposte dal corso a catalogo, uguali per individuali e collettivi
        (`D-35`); restano modificabili per le iscrizioni a metà anno."""
        for line in self:
            line.x_lesson_target = line.product_id.x_lesson_target

    @api.constrains('product_id', 'order_id', 'product_uom_qty')
    def _check_one_line_per_course(self):
        """Un solo corso individuale per iscrizione, e un corso a catalogo
        collettivo una volta sola.

        Odoo genera un progetto per coppia (ordine, modello), non per riga, e
        il modello di corso individuale è uno solo (`D-35`): due righe
        individuali condividerebbero il corso, e il consuntivo allievo
        attribuirebbe le stesse lezioni a entrambe, senza errore.

        Quantità zero = riga annullata (convenzione Odoo sugli ordini
        confermati): non conta come iscrizione, quindi non fa doppione.
        """
        for line in self:
            if not line.product_id.x_is_course or not line.product_uom_qty:
                continue
            others = line.order_id.order_line.filtered(
                lambda other, line=line: (
                    other != line
                    and other.product_uom_qty
                    and other.product_id.x_is_course))
            if line.product_id.service_tracking == 'project_only':
                if others.filtered(
                        lambda other: other.product_id.service_tracking
                        == 'project_only'):
                    raise ValidationError(_(
                        "Un'iscrizione può contenere un solo corso "
                        "individuale: per un secondo strumento apri "
                        "un'altra iscrizione."))
            elif others.filtered(
                    lambda other, line=line: other.product_id.product_tmpl_id
                    == line.product_id.product_tmpl_id):
                raise ValidationError(_(
                    'Il corso a catalogo "%s" compare più volte '
                    "nell'iscrizione.") % line.product_id.product_tmpl_id.name)

    @api.constrains('x_teacher_id', 'product_id')
    def _check_teacher_only_on_generated_course(self):
        """L'insegnante di riga vale solo dove la riga genera un corso
        individuale.

        Un corso collettivo esiste già e ha il suo responsabile: indicarlo
        qui non farebbe nulla, e il nulla silenzioso è peggio di un errore.
        """
        for line in self:
            if line.x_teacher_id and (
                    line.product_id.service_tracking != 'project_only'):
                raise ValidationError(_(
                    "L'insegnante si indica sulle iscrizioni ai corsi "
                    "individuali. Per un corso collettivo il responsabile "
                    "sta sul corso stesso."))

    @api.constrains('project_id', 'product_id')
    def _check_collective_course_matches_product(self):
        """Sulle righe collettive il corso è un corso collettivo del loro
        corso a catalogo (`S-08`).

        Il consuntivo allievo conta le lezioni sui corsi collettivi del corso
        a catalogo della riga: un corso di un altro corso a catalogo
        darebbe lezioni che nessun consuntivo vede. Sulle righe individuali
        il corso lo genera la conferma, e non si sceglie.
        """
        for line in self:
            if (not line.project_id or not line.product_id.x_is_course
                    or line.product_id.service_tracking == 'project_only'):
                continue
            if line.project_id.x_course_product_id != (
                    line.product_id.product_tmpl_id):
                raise ValidationError(_(
                    'Il corso "%(course)s" non è un corso collettivo di '
                    '"%(product)s".',
                    course=line.project_id.display_name,
                    product=line.product_id.product_tmpl_id.name))

    def _course_label(self):
        """Come si chiama il corso di questa riga: "Pianoforte 45'".

        Strumento e durata sono dati veri — il valore d'attributo della
        variante e il campo durata dell'articolo — non pezzi di nome
        ritagliati. Se manca l'uno o l'altra si ripiega sul nome
        dell'articolo, che e' sempre valorizzato.
        """
        self.ensure_one()
        product = self.product_id
        attributes = ' '.join(
            product.product_template_attribute_value_ids.mapped('name'))
        if attributes and product.x_lesson_duration:
            return "%s %d'" % (attributes, product.x_lesson_duration)
        return attributes or product.name

    def _timesheet_create_project_prepare_values(self):
        """Il corso individuale nasce senza responsabile.

        Odoo lo erediterebbe dal modello (`sale_project`), e il modello ha
        per forza un responsabile: il campo prende il valore di chi lo ha
        creato. Così "in attesa di insegnante" non sarebbe mai una
        condizione interrogabile, perché il campo non sarebbe mai vuoto.

        Vince invece l'insegnante indicato sulla riga, quando c'è: è il caso
        in cui la scuola lo sa già al momento dell'iscrizione.
        """
        values = super()._timesheet_create_project_prepare_values()
        if self.product_id.x_is_course:
            values['user_id'] = self.x_teacher_id.id or False
            # La durata scende dal corso a catalogo al corso, e da lì a ogni
            # lezione. Il monte ore del corso non si imposta qui: lo
            # riscriverebbe `sale_timesheet` subito dopo la copia.
            values['x_lesson_duration'] = self.product_id.x_lesson_duration
            # Le lezioni previste della riga, non del corso a catalogo: per
            # un'iscrizione a metà anno sono già ridotte, e il wizard
            # Genera lezioni propone quelle.
            values['x_lesson_target'] = self.x_lesson_target
        return values

    def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        if self.product_id.x_is_course and project.x_lesson_duration:
            # Monte ore dell'anno: lezioni previste per durata. Va scritto qui e
            # non fra i valori di creazione, perche' `sale_timesheet` lo
            # ricalcola dopo la copia dalla quantita' ordinata — una riga
            # d'iscrizione vale 1, quindi ne uscirebbe un'ora.
            project.allocated_hours = (
                project.x_lesson_duration / 60.0 * (self.x_lesson_target or 0))
        if self.product_id.x_is_course and self.order_id.partner_id:
            # Nome operativo al posto dello standard "S00042 - <template>".
            # Il nome progetto è traducibile e la copia del template porta le
            # traduzioni: va riscritto in ogni lingua installata, non solo in
            # quella della sessione.
            for lang, _lang_name in self.env['res.lang'].get_installed():
                project.with_context(lang=lang).name = '%s - %s' % (
                    self.with_context(lang=lang)._course_label(),
                    self.order_id.partner_id.name)
        return project

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Riga aggiunta a un'iscrizione già confermata: iscrive subito (S-03).
        # sudo(): come in sale_order.py, manutenzione del registro scuola
        lines.filtered(
            lambda l: l.state == 'sale').project_id.sudo().action_align_attendance()
        return lines

    def write(self, vals):
        tracked = [f for f in TRACKED_FIELDS if f in vals]
        confirmed = self.filtered(lambda l: l.state == 'sale')
        before = {line: {f: line[f] for f in tracked} for line in confirmed}
        if not {'project_id', 'product_uom_qty'} & vals.keys():
            res = super().write(vals)
        else:
            # Il corso lasciato si raccoglie prima: dopo la scrittura la riga
            # punta già a quello nuovo, e il vecchio terrebbe l'allievo.
            left = confirmed.project_id
            res = super().write(vals)
            joined = self.filtered(lambda l: l.state == 'sale').project_id
            # sudo(): come in sale_order.py, manutenzione del registro scuola
            (left | joined).sudo().action_align_attendance()
        for line, old in before.items():
            line._post_tracked_changes(old)
        return res

    def _post_tracked_changes(self, old):
        """Vecchio → nuovo nel chatter dell'iscrizione, come fa Odoo per la
        quantità: la riga non ha un chatter suo."""
        changes = [
            _('%(field)s: %(old)s → %(new)s', field=TRACKED_FIELDS[f],
        old=self._format_tracked(f, value),
        new=self._format_tracked(f, self[f]))
        for f, value in old.items() if value != self[f]]
        if changes:
            self.order_id.message_post(body=Markup('<b>%s</b><br/>%s<br/>%s') % (
                _('Riga di iscrizione modificata'), self.product_id.display_name,
                Markup('<br/>').join(changes)))

    def _format_tracked(self, fname, value):
        if fname == 'price_unit':
            return format_amount(self.env, value, self.currency_id)
        if isinstance(value, models.BaseModel):
            return value.display_name or '—'
        return str(value)
