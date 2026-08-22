from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('standard', 'at_install', 'bandoo')
class TestTeacherHoursBill(TransactionCase):
    """Wizard: dalle ore non liquidate a un ordine d'acquisto per l'insegnante.

    Prezzo per insegnante dal listino fornitore (product.supplierinfo);
    prodotto scelto nel wizard, con default da impostazione.
    """

    def setUp(self):
        super().setUp()
        # Prodotto normale (non seed di modulo): costo = fallback senza listino.
        self.product = self.env['product.product'].create({
            'name': 'Ora di insegnamento', 'type': 'service',
            'purchase_ok': True, 'standard_price': 20.0,
            'uom_id': self.env.ref('uom.product_uom_hour').id,
            'uom_po_id': self.env.ref('uom.product_uom_hour').id,
        })
        self.env['ir.config_parameter'].sudo().set_param(
            'bandoo_school_purchase.teacher_hour_product_id', str(self.product.id))

        # hr_employee_firstname (D-22) crea il work contact e vi scrive
        # cognome e nome: il partner dell'insegnante non si crea a mano.
        self.teacher = self.env['hr.employee'].create({
            'lastname': 'Rossi', 'firstname': 'Mario',
        })
        self.teacher_partner = self.teacher.work_contact_id
        # Listino fornitore: la tariffa di Mario è 30/h.
        self.env['product.supplierinfo'].create({
            'partner_id': self.teacher_partner.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'price': 30.0, 'min_qty': 0.0,
        })
        self.course = self.env['project.project'].create({
            'name': 'Pianoforte', 'x_lesson_target': 4,
        })

    def _task(self, name, project=None):
        return self.env['project.task'].create({
            'name': name, 'project_id': (project or self.course).id,
            'date_deadline': '2026-09-01 13:00:00',
        })

    def _timesheet(self, task, employee=None, hours=1.0):
        return self.env['account.analytic.line'].create({
            'name': 'ore', 'task_id': task.id, 'project_id': task.project_id.id,
            'unit_amount': hours, 'employee_id': (employee or self.teacher).id,
            'date': '2026-09-01',
        })

    def _bill(self, employee=None, project=None, product=None):
        wizard = self.env['bandoo.teacher.hours.bill'].create({
            'employee_id': (employee or self.teacher).id,
            'project_id': project.id if project else False,
            'product_id': (product or self.product).id,
        })
        action = wizard.action_create_order()
        return self.env['purchase.order'].browse(action['res_id'])

    def test_una_riga_per_lezione(self):
        t1, t2 = self._task('L1'), self._task('L2')
        ts1, ts2 = self._timesheet(t1), self._timesheet(t2)
        po = self._bill()
        self.assertEqual(po.partner_id, self.teacher_partner)
        self.assertEqual(len(po.order_line), 2)
        self.assertEqual(set(po.order_line.mapped('product_qty')), {1.0})
        self.assertEqual(ts1.x_teacher_bill_line_id.order_id, po)
        self.assertEqual(ts2.x_teacher_bill_line_id.order_id, po)

    def test_prezzo_dal_listino_fornitore(self):
        # Mario ha una riga di listino a 30 -> il PO usa 30, non il costo 20.
        self._timesheet(self._task('L1'))
        po = self._bill()
        self.assertEqual(po.order_line.price_unit, 30.0)

    def test_fallback_costo_prodotto_senza_listino(self):
        # Insegnante senza listino fornitore -> si usa il costo del prodotto (20).
        other = self.env['hr.employee'].create({
            'lastname': 'Senza Listino', 'firstname': 'Test',
        })
        other_partner = other.work_contact_id
        self._timesheet(self._task('L1'), employee=other)
        po = self._bill(employee=other)
        self.assertEqual(po.order_line.price_unit, 20.0)

    def test_default_prodotto_da_impostazione(self):
        # Il wizard propone il prodotto salvato in ir.config_parameter.
        defaults = self.env['bandoo.teacher.hours.bill'].default_get(['product_id'])
        self.assertEqual(defaults.get('product_id'), self.product.id)

    def test_ore_stesso_task_sommate(self):
        t1 = self._task('L1')
        self._timesheet(t1, hours=1.0)
        self._timesheet(t1, hours=0.5)
        po = self._bill()
        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(po.order_line.product_qty, 1.5)

    def test_idempotenza(self):
        self._timesheet(self._task('L1'))
        self._bill()
        with self.assertRaises(UserError):
            self._bill()

    def test_supplente_ordine_distinto(self):
        sub = self.env['hr.employee'].create({
            'lastname': 'Supplente', 'firstname': 'Test',
        })
        sub_partner = sub.work_contact_id
        self._timesheet(self._task('L1'))
        self._timesheet(self._task('L2'), employee=sub)

        po_tit = self._bill()
        po_sub = self._bill(employee=sub)
        self.assertEqual(po_tit.partner_id, self.teacher_partner)
        self.assertEqual(po_sub.partner_id, sub_partner)
        self.assertEqual(len(po_tit.order_line), 1)
        self.assertEqual(len(po_sub.order_line), 1)

    def test_filtro_corso(self):
        other = self.env['project.project'].create({'name': 'Solfeggio'})
        self._timesheet(self._task('L1'))
        self._timesheet(self._task('S1', project=other))
        po = self._bill(project=self.course)
        self.assertEqual(len(po.order_line), 1)

    def test_annullo_libera_ore(self):
        ts = self._timesheet(self._task('L1'))
        po = self._bill()
        self.assertTrue(ts.x_teacher_bill_line_id)
        po.button_cancel()
        self.assertFalse(ts.x_teacher_bill_line_id)
        po2 = self._bill()
        self.assertEqual(ts.x_teacher_bill_line_id.order_id, po2)

    def test_lezione_senza_ore_non_conta(self):
        self._task('L1')
        with self.assertRaises(UserError):
            self._bill()
