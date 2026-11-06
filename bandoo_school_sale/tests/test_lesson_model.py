from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import format_date

from .test_settlement import BandooCase


@tagged('standard', 'at_install', 'bandoo')
class TestLessonModel(BandooCase):
    """Unità annua e quota: le lezioni previste si ricavano, il monte ore lo
    scrive Odoo (`modello_durata_lezioni_GO.md`)."""

    def setUp(self):
        super().setUp()
        self.hour = self.env.ref('uom.product_uom_hour')
        self.year_45 = self.env.ref('bandoo_school_sale.uom_year_45')
        self.year_theory = self.env.ref('bandoo_school_sale.uom_year_theory')
        self.template = self.env['project.project'].create({
            'name': 'Modello', 'allow_timesheets': True,
            'allow_billable': True,
        })
        self.instrument = self.env['product.product'].create({
            'name': 'Strumento 45′', 'type': 'service', 'list_price': 400.0,
            'service_tracking': 'project_only',
            'project_template_id': self.template.id, 'x_lesson_duration': 45,
            'uom_id': self.year_45.id, 'uom_po_id': self.year_45.id,
        })
        # partner_firstname (D-21) vuole cognome e nome espliciti anche sul
        # partner che la creazione dell'utente genera.
        self.teacher = self.env['res.users'].create({
            'lastname': 'Maestro', 'firstname': 'Wizard',
            'login': 'wizard@bandoo.test'})
        self.theory_course = self.env['project.project'].create(
            {'name': 'Solfeggio A', 'user_id': self.teacher.id})
        self.theory = self.env['product.product'].create({
            'name': 'Solfeggio', 'type': 'service', 'list_price': 120.0,
            'service_tracking': 'no', 'x_lesson_duration': 15,
            'uom_id': self.year_theory.id, 'uom_po_id': self.year_theory.id,
        })
        self.theory_course.write({
            'x_course_product_id': self.theory.product_tmpl_id.id,
            'x_lesson_duration': 60})

    def _wizard(self, project):
        wizard = self.env['bandoo.lesson.generate'].new({
            'project_id': project.id, 'date_start': '2026-09-07'})
        result = wizard._onchange_project_id()
        return wizard, result

    # --- unità di misura ---

    def test_riferimento_in_ore(self):
        # I rapporti si leggono come ore per anno (`data/uom_data.xml`), e
        # le equivalenze standard restano: 1 giorno = 8 ore.
        self.assertEqual(self.hour.uom_type, 'reference')
        self.assertEqual(self.year_45.ratio, 22.5)
        self.assertEqual(self.year_45._compute_quantity(1, self.hour), 22.5)
        self.assertEqual(self.year_theory._compute_quantity(1, self.hour), 7.0)
        day = self.env.ref('uom.product_uom_day')
        self.assertEqual(day._compute_quantity(1, self.hour), 8.0)

    # --- lezioni previste ---

    def test_previste_ricavate(self):
        self.assertEqual(self.instrument.x_lesson_target, 30)
        self.assertEqual(self.theory.x_lesson_target, 28)
        order = self._order(self.student, [(self.instrument, 400.0, 0.57)])
        # 0,57 × 22,5 h = 12,825 h, da 45′ = 17,1 → 17
        self.assertEqual(order.order_line.x_lesson_target, 17)

    def test_lezioni_scritte_diventano_quantita(self):
        # Il segretario scrive le lezioni rimaste; quantità e prezzo seguono.
        order = self._order(self.student, [(self.instrument, 400.0)])
        line = order.order_line
        line.x_lesson_target = 4
        self.assertEqual(line.product_uom_qty, 0.13)
        self.assertEqual(line.price_subtotal, 52.0)
        self.assertEqual(line.x_lesson_target, 4)
        # Nel form, prima del salvataggio, attraverso l'onchange.
        draft = self.env['sale.order.line'].new({
            'order_id': order.id, 'product_id': self.theory.id,
            'product_uom': self.year_theory.id, 'product_uom_qty': 1.0})
        draft.x_lesson_target = 3
        draft._onchange_x_lesson_target()
        self.assertEqual(draft.product_uom_qty, 0.11)
        self.assertEqual(draft.x_lesson_target, 3)

    def test_lezioni_scritte_su_ogni_frazione(self):
        # Da 1 a 30 lezioni, scritte e rilette, tornano identiche.
        order = self._order(self.student, [(self.instrument, 400.0)])
        line = order.order_line
        for lessons in range(1, 31):
            line.x_lesson_target = lessons
            self.assertEqual(line.x_lesson_target, lessons)

    def test_iscrizione_tardiva_scala_prezzo_ore_e_lezioni(self):
        student = self._partner('Tardiva')
        order = self._order(student, [(self.instrument, 400.0, 0.5)])
        order.action_confirm()
        line = order.order_line
        self.assertEqual(line.price_subtotal, 200.0)
        self.assertAlmostEqual(line.project_id.allocated_hours, 11.25)
        s = self._settlements(student)
        self.assertEqual(s.annual_price, 200.0)
        self.assertEqual(s.target, 15)

    def test_monte_ore_dalle_lezioni_previste(self):
        # 4 lezioni su 30 sono 0,13 anni, cioè 2,925 ore da conversione: il
        # monte ore è invece 4 × 45′ = 3 ore esatte.
        student = self._partner('Quattro')
        order = self._order(student, [(self.instrument, 400.0)])
        order.order_line.x_lesson_target = 4
        order.action_confirm()
        self.assertEqual(order.order_line.product_uom_qty, 0.13)
        self.assertEqual(order.order_line.project_id.allocated_hours, 3.0)

    def test_fatturazione_acconti_detrazione_saldo(self):
        # Il flusso di `S-12` su Odoo standard: due acconti a importo fisso,
        # la riga di detrazione dal consuntivo, il saldo uguale alla rata 3.
        detraction = self.env['product.product'].create({
            'name': 'Detrazione lezioni non fruite', 'type': 'service',
            'invoice_policy': 'order', 'taxes_id': [(5,)]})
        self.assertFalse(detraction.x_is_course)
        self.instrument.taxes_id = [(5,)]
        student = self._partner('Fatturata')
        order = self._order(student, [(self.instrument, 400.0)])
        order.order_line.x_lesson_target = 4
        order.action_confirm()
        project = order.order_line.project_id
        for n in range(3):
            self._timesheet(self._task(f'L{n}', project=project))

        def settlement():
            self.env.flush_all()
            self.env.invalidate_all()
            return self.env['bandoo.order.settlement'].search(
                [('order_id', '=', order.id)])

        def invoice(method, amount=0.0):
            self.env['sale.advance.payment.inv'].with_context(
                active_model='sale.order', active_ids=order.ids,
            ).create({'advance_payment_method': method,
                      'fixed_amount': amount}).create_invoices()
            move = order.invoice_ids.filtered(lambda m: m.state == 'draft')
            move.action_post()
            return move

        before = settlement()
        # 52 € per 4 lezioni, 3 erogate: detrazione 13, rate 17 + 17, saldo 5
        self.assertEqual((before.installment_1, before.deduction_to_invoice,
                          before.installment_3), (17.0, 13.0, 5.0))
        invoice('fixed', before.installment_1)
        invoice('fixed', before.installment_2)
        order.write({'order_line': [(0, 0, {
            'product_id': detraction.id, 'product_uom_qty': 1,
            'price_unit': -before.deduction_to_invoice})]})
        # La riga di detrazione non è un corso: il consuntivo non la vede.
        self.assertEqual(settlement().deduction_to_invoice, 13.0)
        balance = invoice('delivered')
        self.assertEqual(balance.amount_total, before.installment_3)
        self.assertEqual(order.invoice_status, 'invoiced')

    def test_previste_della_view_come_della_riga(self):
        # La stessa formula vive in Python e nella view SQL: devono
        # coincidere anche sulle frazioni scomode.
        for n, qty in enumerate((0.57, 0.33, 0.1, 1.0)):
            student = self._partner(f'Frazione{n}')
            order = self._order(student, [
                (self.instrument, 400.0, qty), (self.theory, 120.0, qty)])
            order.action_confirm()
            for settlement in self._settlements(student):
                self.assertEqual(
                    settlement.target, settlement.order_line_id.x_lesson_target)

    # --- configurazione ---

    def test_udm_non_oraria_respinta(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['product.product'].create({
                'name': 'Corso a Unità', 'type': 'service',
                'service_tracking': 'no', 'x_lesson_duration': 15,
            })

    def test_tempo_assegnato_del_modello_ignorato(self):
        # Con un tempo sul modello `sale_timesheet` copia quello invece di
        # convertire; il monte ore lo riscrive comunque la riga (`D-42`).
        self.template.allocated_hours = 10.0
        order = self._order(self.student, [(self.instrument, 400.0)])
        order.action_confirm()
        self.assertEqual(order.order_line.project_id.allocated_hours, 22.5)

    def test_quota_e_udm_bloccate_con_iscrizioni(self):
        # In bozza si cambiano: nessun consuntivo ne dipende ancora.
        self._order(self.student, [(self.instrument, 400.0)])
        self.instrument.x_lesson_duration = 30
        self.instrument.x_lesson_duration = 45
        self._order(self.student, [(self.instrument, 400.0)]).action_confirm()
        year_30 = self.env.ref('bandoo_school_sale.uom_year_30')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.instrument.x_lesson_duration = 30
        with self.assertRaises(UserError), self.cr.savepoint():
            self.instrument.write({'uom_id': year_30.id, 'uom_po_id': year_30.id})
        # Riscrivere lo stesso valore non è un cambio.
        self.instrument.x_lesson_duration = 45

    def test_durata_obbligatoria_sul_collettivo(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['project.project'].create({
                'name': 'Solfeggio senza durata',
                'x_course_product_id': self.theory.product_tmpl_id.id,
            })

    # --- lezioni ---

    def test_tempo_assegnato_individuale_dalla_quota(self):
        order = self._order(self.student, [(self.instrument, 400.0)])
        order.action_confirm()
        task = self._task('Saggio', project=order.order_line.project_id)
        self.assertAlmostEqual(task.allocated_hours, 0.75)

    def test_tempo_assegnato_collettivo_dal_gruppo(self):
        task = self._task('L1', project=self.theory_course)
        self.assertAlmostEqual(task.allocated_hours, 1.0)

    def test_wizard_individuale_esclude_due_saggi(self):
        order = self._order(self.student, [(self.instrument, 400.0)])
        order.action_confirm()
        wizard, result = self._wizard(order.order_line.project_id)
        self.assertEqual(wizard.recital_count, 2)
        self.assertEqual(wizard.count, 28)
        self.assertFalse(result)

    def test_wizard_individuale_tardivo(self):
        order = self._order(self.student, [(self.instrument, 400.0, 0.5)])
        order.action_confirm()
        wizard, _result = self._wizard(order.order_line.project_id)
        self.assertEqual(wizard.count, 13)  # 15 previste − 2 saggi

    def test_wizard_collettivo_senza_saggi(self):
        wizard, result = self._wizard(self.theory_course)
        self.assertEqual(wizard.recital_count, 0)
        self.assertEqual(wizard.count, 28)
        self.assertFalse(result)

    def test_wizard_avvisa_oltre_le_previste(self):
        # Una lezione già a calendario in un altro giorno: 1 + 28 > 28.
        self.env['project.task'].create({
            'name': 'Lezione extra', 'project_id': self.theory_course.id,
            'date_deadline': '2026-08-31 13:00:00'})
        _wizard, result = self._wizard(self.theory_course)
        self.assertIn('warning', result)

    def test_wizard_senza_responsabile_si_ferma(self):
        self.theory_course.user_id = False
        wizard, _result = self._wizard(self.theory_course)
        with self.assertRaises(UserError):
            wizard.action_generate()
        self.assertFalse(self.theory_course.task_ids)

    def test_insegnante_dal_responsabile_del_corso(self):
        # Generate e aggiunte a mano allo stesso modo; un'assegnazione
        # esplicita, il supplente, vince.
        wizard, _result = self._wizard(self.theory_course)
        wizard.action_generate()
        self.assertEqual(self.theory_course.task_ids.user_ids, self.teacher)
        # Come «Nuovo» dentro il corso: l'interfaccia porta il progetto nel
        # contesto, e Odoo non assegna la lezione a chi la crea.
        recital = self.env['project.task'].with_context(
            default_project_id=self.theory_course.id).create({'name': 'Saggio'})
        self.assertEqual(recital.user_ids, self.teacher)
        substitute = self.env['res.users'].create({
            'lastname': 'Supplente', 'firstname': 'Test',
            'login': 'supplente@bandoo.test'})
        lesson = self.env['project.task'].create({
            'name': 'Lezione', 'project_id': self.theory_course.id,
            'user_ids': [(6, 0, substitute.ids)]})
        self.assertEqual(lesson.user_ids, substitute)

    def test_nome_della_lezione_segue_la_data(self):
        # Il nome salvato non ha la data; quello visualizzato la prende dalla
        # data della lezione, anche dopo uno spostamento.
        wizard, _result = self._wizard(self.theory_course)
        wizard.count = 1
        wizard.action_generate()
        lesson = self.theory_course.task_ids
        self.assertEqual(lesson.name, 'Lezione')

        def shown(task):
            return '%s %s' % (task.name, format_date(
                self.env, fields.Datetime.context_timestamp(task, task.date_deadline)))
        self.assertTrue(lesson.display_name.startswith(shown(lesson)))
        lesson.date_deadline = '2026-09-08 13:00:00'
        self.assertTrue(lesson.display_name.startswith(shown(lesson)))
        self.assertIn('08', lesson.display_name)
        # Senza data, il nome e basta.
        undated = self.env['project.task'].create({
            'name': 'Saggio', 'project_id': self.theory_course.id})
        self.assertEqual(undated.display_name, 'Saggio')

    def test_wizard_rilanciato_non_avvisa(self):
        # Rilanciare il wizard sulle stesse date non crea lezioni nuove,
        # quindi non va oltre le previste.
        wizard, _result = self._wizard(self.theory_course)
        wizard.action_generate()
        self.assertEqual(len(self.theory_course.task_ids), 28)
        _wizard, result = self._wizard(self.theory_course)
        self.assertFalse(result)
