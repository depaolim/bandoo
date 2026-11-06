from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LessonGenerate(models.TransientModel):
    _name = 'bandoo.lesson.generate'
    _description = 'Genera lezioni ricorrenti'

    project_id = fields.Many2one(
        'project.project', string='Corso', required=True,
    )
    room_id = fields.Many2one('bandoo.room', string='Aula')
    # Senza data: la data la mostra il nome visualizzato della lezione, che la
    # segue quando la lezione si sposta.
    name_prefix = fields.Char(string='Nome', default='Lezione')
    date_start = fields.Date(
        string='Prima lezione', required=True,
        default=fields.Date.context_today,
    )
    start_time = fields.Float(
        string='Ora inizio', required=True, default=15.0,
        help='Ora di inizio della lezione, in ora locale.',
    )
    count = fields.Integer(
        string='Numero lezioni', required=True, default=28,
        help='Quante lezioni generare adesso. Meno delle lezioni previste '
             'dal corso: i saggi si aggiungono a mano quando se ne conosce '
             'la data.')
    recital_count = fields.Integer(
        string='Saggi esclusi', required=True, default=0,
        help='Saggi da aggiungere a mano quando se ne conosce la data: non si '
             'generano ora. Sottratti dalle lezioni previste per proporre '
             'quante lezioni generare.')
    interval_weeks = fields.Integer(
        string='Cadenza (settimane)', required=True, default=1,
    )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """Proposte dal corso (modificabili): saggi e numero lezioni.

        Le lezioni da generare sono le lezioni previste **meno i saggi**:
        quelli si aggiungono a mano quando se ne conosce la data. Proporre il
        numero pieno farebbe generare lezioni di troppo, e il consuntivo
        allievo le conterebbe come erogate (`S-05`). Quanti saggi lo dice il
        corso: il solfeggio non ne ha.
        """
        if not self.project_id:
            return
        self.recital_count = self.project_id._get_recital_count()
        return self._onchange_recital_count()

    @api.onchange('recital_count')
    def _onchange_recital_count(self):
        target = self.project_id and self.project_id._get_lesson_target()
        if target:
            self.count = max(0, target - (self.recital_count or 0))
        return self._onchange_count()

    @api.onchange('count', 'date_start', 'interval_weeks')
    def _onchange_count(self):
        """Avviso, non blocco, se il corso finirebbe con più lezioni delle
        previste: le lezioni in più costano all'insegnante e nessun
        consuntivo allievo le vede (`S-05`)."""
        target = self.project_id and self.project_id._get_lesson_target()
        if not target or self.count <= 0 or self.interval_weeks <= 0:
            return
        existing = len(self.project_id.task_ids)
        new = len(self._days_to_generate())
        total = existing + new + (self.recital_count or 0)
        if total > target:
            return {'warning': {
                'title': _('Più lezioni delle previste'),
                'message': _(
                    'Il corso avrebbe %(total)s lezioni (%(existing)s già '
                    'presenti, %(new)s da generare, %(recitals)s saggi da '
                    'aggiungere) contro %(target)s previste.',
                    total=total, existing=existing, new=new,
                    recitals=self.recital_count or 0, target=target),
            }}

    def _local_tz(self):
        return pytz.timezone(self.env.user.tz or 'UTC')

    def _days_to_generate(self):
        """Giorni delle lezioni da creare: la cadenza a partire dalla prima,
        meno i giorni in cui il corso ha già una lezione."""
        tz = self._local_tz()
        # Idempotenza: non ricreare lezioni su giorni già occupati nel corso
        # (così il wizard serve anche a ricaricare/estendere un calendario).
        # date_deadline è un Datetime salvato in UTC: riporto al giorno locale.
        existing_days = {
            pytz.utc.localize(dt).astimezone(tz).date()
            for dt in self.project_id.task_ids.filtered(
                'date_deadline').mapped('date_deadline')
        }
        days = (self.date_start + timedelta(weeks=i * self.interval_weeks)
                for i in range(self.count))
        return [day for day in days if day not in existing_days]

    def action_generate(self):
        self.ensure_one()
        if not self.project_id.user_id:
            # L'insegnante delle lezioni è il responsabile del corso: senza,
            # nascerebbero lezioni che nessun insegnante vede.
            raise UserError(_(
                'Il corso "%s" non ha un responsabile: indicalo prima di '
                'generare le lezioni.', self.project_id.display_name))
        if self.count <= 0:
            raise UserError(_('Il numero di lezioni deve essere maggiore di zero.'))
        if self.interval_weeks <= 0:
            raise UserError(_('La cadenza deve essere di almeno una settimana.'))
        if not 0 <= self.start_time < 24:
            raise UserError(_("L'ora di inizio deve essere tra 0:00 e 23:59."))

        hour = int(self.start_time)
        minute = round((self.start_time - hour) * 60)
        tz = self._local_tz()

        Task = self.env['project.task']
        prefix = self.name_prefix or _('Lezione')
        vals_list = []
        for day in self._days_to_generate():
            # Ora locale dell'utente → UTC naive per l'ORM.
            local_dt = tz.localize(datetime.combine(day, time(hour, minute)))
            deadline = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
            vals_list.append({
                'name': prefix,
                'project_id': self.project_id.id,
                'date_deadline': deadline,
                'room_id': self.room_id.id,
                # Esplicito: senza `default_project_id` nel contesto Odoo
                # assegnerebbe la lezione a chi lancia il wizard.
                'user_ids': [(6, 0, self.project_id.user_id.ids)],
            })

        # La create di project.task popola da sé presenze e tempo assegnato.
        Task.create(vals_list)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Lezioni'),
            'res_model': 'project.task',
            'view_mode': 'calendar,list,form',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
        }
