from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_project_id = fields.Many2one(
        'project.project', string='Corso',
        compute='_compute_x_project_id', store=True,
    )
    x_teacher_id = fields.Many2one(
        'res.users', string='Insegnante',
        domain="[('employee_ids', '!=', False)]",
        help="Facoltativo: se l'insegnante e' gia' noto all'iscrizione, "
             "diventa il responsabile del registro alla conferma. Lasciandolo "
             "vuoto il registro nasce in attesa di assegnazione.",
    )
    x_lesson_target = fields.Integer(
        string='Appuntamenti previsti', compute='_compute_x_lesson_target',
        store=True, readonly=False,
        help='Appuntamenti coperti da questa iscrizione — lezioni e saggi: '
             'proposti dal corso, da ridurre per le iscrizioni a metà anno '
             '(il conguaglio detrae gli appuntamenti non erogati '
             'all\'iscritto rispetto a questo numero).',
    )

    @api.depends('project_id', 'product_id')
    def _compute_x_project_id(self):
        """Progetto del corso: per gli individuali è quello generato alla
        conferma (project_id standard), per i collettivi quello condiviso
        indicato sul prodotto."""
        for line in self:
            line.x_project_id = (
                line.project_id or line.product_id.x_course_project_id
            )

    @api.depends('product_id')
    def _compute_x_lesson_target(self):
        """Proposta dal corso (collettivo: progetto condiviso; individuale:
        template); resta modificabile per le iscrizioni a metà anno."""
        for line in self:
            product = line.product_id
            line.x_lesson_target = (
                product.x_course_project_id.x_lesson_target
                or product.project_template_id.x_lesson_target
                or 0
            )

    @api.constrains('product_id', 'order_id', 'product_uom_qty')
    def _check_one_line_per_course(self):
        """Un corso per ordine: due righe dello stesso prodotto porterebbero
        a un registro solo.

        Odoo genera un progetto per coppia (ordine, template di progetto), non
        per riga: due iscrizioni allo stesso articolo condividerebbero il
        registro, e il conguaglio attribuirebbe le stesse lezioni a entrambe —
        senza errore. Meglio fermarsi qui, dove si puo' ancora dire cosa fare.

        Quantita' zero = riga annullata (convenzione Odoo sugli ordini
        confermati): non conta come iscrizione, quindi non fa doppione.
        """
        for line in self:
            if not line.product_id.x_is_course or not line.product_uom_qty:
                continue
            twins = line.order_id.order_line.filtered(
                lambda other, line=line: (
                    other != line
                    and other.product_uom_qty
                    and other.product_id.product_tmpl_id
                    == line.product_id.product_tmpl_id))
            if twins:
                raise ValidationError(_(
                    'Il corso "%s" compare piu\' di una volta nello stesso '
                    'ordine. Ogni iscrizione ha il suo registro: per un '
                    'secondo strumento dello stesso tipo di corso, apri un '
                    'ordine distinto.') % line.product_id.product_tmpl_id.name)

    @api.constrains('x_teacher_id', 'product_id')
    def _check_teacher_only_on_generated_course(self):
        """L'insegnante di riga vale solo dove la riga genera un registro.

        Su un corso collettivo il registro esiste gia' e ha il suo
        responsabile: indicarlo qui non farebbe nulla, e il nulla silenzioso
        e' peggio di un errore.
        """
        for line in self:
            if line.x_teacher_id and (
                    line.product_id.service_tracking != 'project_only'):
                raise ValidationError(_(
                    "L'insegnante si indica sulle iscrizioni ai corsi "
                    "individuali. Per un corso collettivo il responsabile "
                    "sta sul corso stesso."))

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
        """Il registro nasce senza responsabile.

        Odoo lo erediterebbe dal template (`sale_project`), e il template ha
        per forza un responsabile: il campo prende il valore di chi lo ha
        creato. Cosi' "in attesa di insegnante" non sarebbe mai una
        condizione interrogabile, perche' il campo non sarebbe mai vuoto.

        Vince invece l'insegnante indicato sulla riga, quando c'e': e' il caso
        in cui la scuola lo sa gia' al momento dell'iscrizione.
        """
        values = super()._timesheet_create_project_prepare_values()
        if self.product_id.x_is_course:
            values['user_id'] = self.x_teacher_id.id or False
            # La durata scende dall'articolo al registro, e da li' a ogni
            # lezione. Il monte ore del registro non si imposta qui: lo
            # riscriverebbe `sale_timesheet` subito dopo la copia.
            values['x_lesson_duration'] = self.product_id.x_lesson_duration
        return values

    def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        if self.product_id.x_is_course and project.x_lesson_duration:
            # Monte ore dell'anno: appuntamenti per durata. Va scritto qui e
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
