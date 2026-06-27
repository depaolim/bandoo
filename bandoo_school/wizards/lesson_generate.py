from datetime import datetime, time, timedelta

import pytz

from odoo import _, fields, models
from odoo.exceptions import UserError


class LessonGenerate(models.TransientModel):
    _name = 'bandoo.lesson.generate'
    _description = 'Genera lezioni ricorrenti'

    project_id = fields.Many2one(
        'project.project', string='Corso', required=True,
    )
    room_id = fields.Many2one('bandoo.room', string='Aula')
    user_ids = fields.Many2many('res.users', string='Insegnante')
    name_prefix = fields.Char(string='Prefisso nome', default='Lezione')
    date_start = fields.Date(
        string='Prima lezione', required=True,
        default=fields.Date.context_today,
    )
    start_time = fields.Float(
        string='Ora inizio', required=True, default=15.0,
        help='Ora di inizio della lezione, in ora locale.',
    )
    count = fields.Integer(string='Numero lezioni', required=True, default=28)
    interval_weeks = fields.Integer(
        string='Cadenza (settimane)', required=True, default=1,
    )

    def action_generate(self):
        self.ensure_one()
        if self.count <= 0:
            raise UserError(_('Il numero di lezioni deve essere maggiore di zero.'))
        if self.interval_weeks <= 0:
            raise UserError(_('La cadenza deve essere di almeno una settimana.'))
        if not 0 <= self.start_time < 24:
            raise UserError(_("L'ora di inizio deve essere tra 0:00 e 23:59."))

        hour = int(self.start_time)
        minute = round((self.start_time - hour) * 60)
        tz = pytz.timezone(self.env.user.tz or 'UTC')

        Task = self.env['project.task']
        # Idempotenza: non ricreare lezioni su giorni già occupati nel corso
        # (così il wizard serve anche a ricaricare/estendere un calendario).
        # date_deadline è un Datetime salvato in UTC: riporto al giorno locale.
        existing_days = {
            pytz.utc.localize(dt).astimezone(tz).date()
            for dt in Task.search([
                ('project_id', '=', self.project_id.id),
                ('date_deadline', '!=', False),
            ]).mapped('date_deadline')
        }

        prefix = self.name_prefix or _('Lezione')
        vals_list = []
        for i in range(self.count):
            day = self.date_start + timedelta(weeks=i * self.interval_weeks)
            if day in existing_days:
                continue
            # Ora locale dell'utente → UTC naive per l'ORM.
            local_dt = tz.localize(datetime.combine(day, time(hour, minute)))
            deadline = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
            vals_list.append({
                'name': '%s %s' % (prefix, day.isoformat()),
                'project_id': self.project_id.id,
                'date_deadline': deadline,
                'room_id': self.room_id.id,
                'user_ids': [(6, 0, self.user_ids.ids)],
            })

        # La create di project.task popola da sé le presenze dagli iscritti.
        Task.create(vals_list)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Lezioni'),
            'res_model': 'project.task',
            'view_mode': 'calendar,list,form',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
        }
