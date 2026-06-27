from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('standard', 'at_install', 'bandoo')
class TestSettlementArithmetic(TransactionCase):
    """Aritmetica del conguaglio in isolamento (campi grezzi -> rate).

    Usa record virtuali `.new()`: niente DB view, si testa solo `_compute_amounts`.
    """

    def _settlement(self, annual_price, target, lessons_held, justified_absences):
        return self.env['bandoo.enrollment.settlement'].new({
            'annual_price': annual_price,
            'target': target,
            'lessons_held': lessons_held,
            'justified_absences': justified_absences,
        })

    def test_normale_rata3_positiva(self):
        # P=280, target=28 -> prezzo lezione 10; tutte tenute, 2 giustificate.
        s = self._settlement(280.0, 28, 28, 2)
        self.assertEqual(s.price_per_lesson, 10.0)
        self.assertEqual(s.missed_lessons, 0)
        self.assertEqual(s.deduction, 20.0)
        self.assertEqual(s.installment_1, 93.0)
        self.assertEqual(s.installment_2, 93.0)
        # 280 - 93 - 93 - 20 = 74
        self.assertEqual(s.installment_3, 74.0)

    def test_clamp_rata3_a_zero(self):
        # Detrazione enorme (poche tenute) -> rata 3 azzerata, mai negativa.
        s = self._settlement(280.0, 28, 2, 1)
        self.assertEqual(s.missed_lessons, 26)
        self.assertEqual(s.deduction, 270.0)
        self.assertEqual(s.installment_3, 0.0)

    def test_target_zero_nessuna_divisione(self):
        # target=0 non deve sollevare ZeroDivisionError.
        s = self._settlement(280.0, 0, 0, 0)
        self.assertEqual(s.price_per_lesson, 0.0)
        self.assertEqual(s.missed_lessons, 0)
        self.assertEqual(s.deduction, 0.0)
        self.assertEqual(s.installment_3, 94.0)  # 280 - 93 - 93

    def test_solo_mai_erogate(self):
        # Nessuna giustificata, 8 lezioni non erogate dal corso.
        s = self._settlement(280.0, 28, 20, 0)
        self.assertEqual(s.missed_lessons, 8)
        self.assertEqual(s.deduction, 80.0)
        self.assertEqual(s.installment_3, 14.0)  # 280 - 186 - 80

    def test_solo_giustificate(self):
        # Tutte le lezioni erogate, 3 assenze giustificate.
        s = self._settlement(280.0, 28, 28, 3)
        self.assertEqual(s.missed_lessons, 0)
        self.assertEqual(s.deduction, 30.0)
        self.assertEqual(s.installment_3, 64.0)  # 280 - 186 - 30


@tagged('standard', 'at_install', 'bandoo')
class TestSettlementIntegration(TransactionCase):
    """Catena completa: iscrizione -> lezioni/timesheet/presenze -> view SQL."""

    def setUp(self):
        super().setUp()
        self.course = self.env['project.project'].create({
            'name': 'Chitarra', 'x_is_course': True,
            'x_list_price': 400.0, 'x_lesson_target': 4,
        })
        self.student = self.env['res.partner'].create({
            'name': 'Allievo', 'x_is_student': True, 'x_is_member': True,
        })
        self.guardian = self.env['res.partner'].create({'name': 'Genitore'})
        self.employee = self.env['hr.employee'].create({'name': 'Maestro'})

        product = self.env.ref('bandoo_school_sale.product_enrollment')
        self.order = self.env['sale.order'].create({
            'partner_id': self.guardian.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'x_student_id': self.student.id,
                'x_project_id': self.course.id,
                'price_unit': 400.0,
                'product_uom_qty': 1.0,
                'name': 'Iscrizione',
            })],
        })
        self.order.action_confirm()

    def _task(self, name):
        return self.env['project.task'].create({
            'name': name, 'project_id': self.course.id,
            'date_deadline': '2026-09-01 13:00:00',
        })

    def _timesheet(self, task):
        return self.env['account.analytic.line'].create({
            'name': 'ore', 'task_id': task.id, 'project_id': self.course.id,
            'unit_amount': 1.0, 'employee_id': self.employee.id,
            'date': '2026-09-01',
        })

    def _settlement(self):
        # La view SQL legge il DB: flush delle scritture + invalidazione della
        # cache di lettura, così i grezzi rispecchiano i dati appena creati.
        self.env.flush_all()
        self.env.invalidate_all()
        return self.env['bandoo.enrollment.settlement'].search(
            [('partner_id', '=', self.student.id)])

    def test_iscrizione_popola_corso(self):
        self.assertIn(self.student, self.course.enrolled_student_ids)

    def test_conteggi_e_recupero_collettivo(self):
        t1, t2, t3 = self._task('L1'), self._task('L2'), self._task('L3')
        # 2 lezioni tenute (timesheet), 1 giustificata su lezione tenuta.
        self._timesheet(t1)
        self._timesheet(t2)
        line = t1.attendance_line_ids.filtered(
            lambda l: l.partner_id == self.student)
        line.status = 'absent_justified'

        s = self._settlement()
        self.assertEqual(len(s), 1)
        self.assertEqual(s.target, 4)
        self.assertEqual(s.lessons_held, 2)
        self.assertEqual(s.justified_absences, 1)
        self.assertEqual(s.missed_lessons, 2)
        # prezzo lezione 100; detrazione (1+2)*100 = 300; 400-266-300 -> clamp 0
        self.assertEqual(s.deduction, 300.0)
        self.assertEqual(s.installment_3, 0.0)

        # Recupero collettivo: la 3a lezione viene tenuta (timesheet).
        # Senza alcun link esplicito, lessons_held sale -> missed scende (Buco 1).
        self._timesheet(t3)
        s = self._settlement()
        self.assertEqual(s.lessons_held, 3)
        self.assertEqual(s.missed_lessons, 1)
        self.assertEqual(s.justified_absences, 1)
        # detrazione (1+1)*100 = 200; 400-266-200 -> 0 ancora? 400-466 -> 0
        self.assertEqual(s.deduction, 200.0)

    def test_lezione_senza_timesheet_non_conta(self):
        # Una task senza ore registrate non è "tenuta": non riduce missed.
        self._task('L1')  # nessun timesheet
        s = self._settlement()
        self.assertEqual(s.lessons_held, 0)
        self.assertEqual(s.missed_lessons, 4)
