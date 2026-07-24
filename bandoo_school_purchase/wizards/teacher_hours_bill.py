from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TeacherHoursBill(models.TransientModel):
    _name = 'bandoo.teacher.hours.bill'
    _description = 'Compenso ore insegnante'

    employee_id = fields.Many2one(
        'hr.employee', string='Insegnante', required=True,
        help='Le ore da liquidare sono i fogli ore registrati da questo '
             'insegnante (chi ha tenuto la lezione, anche se supplente).',
    )
    project_id = fields.Many2one(
        'project.project', string='Corso',
        help='Facoltativo: limita al solo corso indicato.',
    )
    product_id = fields.Many2one(
        'product.product', string='Prodotto ore', required=True,
        domain=[('purchase_ok', '=', True)],
        default=lambda self: self._default_product_id(),
        help="Voce d'ordine per le ore. Il prezzo per insegnante viene dal "
             "listino fornitore del prodotto (tab Acquisti → Fornitori); "
             "in assenza di listino si usa il costo del prodotto.",
    )

    @api.model
    def _default_product_id(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'bandoo_school_purchase.teacher_hour_product_id')
        if param and param.isdigit():
            product = self.env['product.product'].browse(int(param))
            if product.exists():
                return product.id
        return False

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
            # Non imposto price_unit: purchase lo calcola dal listino del
            # fornitore di riga (l'insegnante) o, se assente, dal costo prodotto.
            pol = self.env['purchase.order.line'].create({
                'order_id': order.id,
                'product_id': self.product_id.id,
                'name': '%s (%s)' % (task.name, task.project_id.name or ''),
                'product_qty': hours,
                'product_uom': self.product_id.uom_po_id.id,
            })
            lines.x_teacher_bill_line_id = pol

        return {
            'type': 'ir.actions.act_window',
            'name': _('Compenso insegnante'),
            'res_model': 'purchase.order',
            'res_id': order.id,
            'view_mode': 'form',
        }
