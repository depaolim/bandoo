from odoo import _, fields, models
from odoo.exceptions import UserError


class TeacherHoursBill(models.TransientModel):
    _name = 'bandoo.teacher.hours.bill'
    _description = 'Consuntivo insegnante'

    employee_id = fields.Many2one(
        'hr.employee', string='Insegnante', required=True,
        help='Le ore da liquidare sono i fogli ore registrati da questo '
             'insegnante (chi ha tenuto la lezione, anche se supplente).',
    )
    project_id = fields.Many2one(
        'project.project', string='Corso',
        help='Facoltativo: limita al solo corso indicato.',
    )
    def action_create_order(self):
        self.ensure_one()

        domain = [
            ('employee_id', '=', self.employee_id.id),
            ('x_teacher_bill_line_id', '=', False),
            ('task_id', '!=', False),
            ('unit_amount', '>', 0),
        ]
        if self.project_id:
            domain.append(('project_id', '=', self.project_id.id))
        timesheets = self.env['account.analytic.line'].search(
            domain, order='date, id')
        if not timesheets:
            raise UserError(_(
                'Nessuna ora da liquidare per %s.') % self.employee_id.display_name)

        # Il prodotto ore è del corso (`S-11`): senza, non si inventa un
        # prezzo. Si ferma prima di creare l'ordine, nominando i corsi.
        missing = timesheets.project_id.filtered(
            lambda p: not p.x_teacher_hour_product_id)
        if missing:
            raise UserError(_(
                'Questi corsi non hanno un prodotto ore insegnante: %s. '
                'Impostarlo sul corso, poi rilanciare.')
                % ', '.join(missing.mapped('display_name')))

        partner = (
            self.employee_id.work_contact_id
            or self.employee_id.user_id.partner_id
        )
        if not partner:
            raise UserError(_(
                "L'insegnante %s non ha un contatto collegato: "
                "impossibile intestare l'ordine d'acquisto.")
                % self.employee_id.display_name)
        if not partner.supplier_rank:
            partner.sudo().supplier_rank = 1

        order = self.env['purchase.order'].create({'partner_id': partner.id})

        # Una riga d'ordine per lezione (task): sommo le ore dei fogli ore
        # dello stesso task. dict = ordine di inserimento (per data crescente).
        by_task = {}
        for line in timesheets:
            by_task.setdefault(line.task_id, self.env['account.analytic.line'])
            by_task[line.task_id] |= line

        for task, lines in by_task.items():
            hours = sum(lines.mapped('unit_amount'))
            # Un ordine solo, prodotto per riga dal corso della lezione: righe
            # a prezzi diversi. Non imposto price_unit: purchase lo calcola
            # dal listino fornitore (l'insegnante) o dal costo del prodotto.
            product = task.project_id.x_teacher_hour_product_id
            pol = self.env['purchase.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'name': '%s (%s)' % (task.name, task.project_id.name or ''),
                'product_qty': hours,
                'product_uom': product.uom_po_id.id,
            })
            lines.x_teacher_bill_line_id = pol

        return {
            'type': 'ir.actions.act_window',
            'name': _('Ordine ore insegnante'),
            'res_model': 'purchase.order',
            'res_id': order.id,
            'view_mode': 'form',
        }
