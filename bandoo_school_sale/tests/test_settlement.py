from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


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

    def test_rata3_riga_negativa_non_azzerata(self):
        # Detrazione enorme (poche tenute): la rata 3 di riga resta negativa
        # (credito); l'azzeramento vive solo sul conguaglio per ordine.
        s = self._settlement(280.0, 28, 2, 1)
        self.assertEqual(s.missed_lessons, 26)
        self.assertEqual(s.deduction, 270.0)
        self.assertEqual(s.installment_3, -176.0)  # 280 - 186 - 270

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

    def test_recupero_oltre_le_previste(self):
        # Tutte le lezioni del corso tenute, una giustificata recuperata in un
        # altro corso collettivo: il recupero la compensa (D-36).
        s = self._settlement(120.0, 4, 5, 1)
        self.assertEqual(s.missed_lessons, 0)
        self.assertEqual(s.paid_lessons, 4)
        self.assertEqual(s.deduction, 0.0)
        self.assertEqual(s.installment_3, 40.0)  # 120 - 40 - 40


class BandooCase(TransactionCase):
    """Setup comune: corso collettivo con prodotto, studente figlio del
    genitore, ordine confermato."""

    def setUp(self):
        super().setUp()
        self.course = self.env['project.project'].create({
            'name': 'Chitarra', 'x_lesson_target': 4,
        })
        self.product = self._course_product('Corso Chitarra', self.course, 400.0)
        self.student = self._partner('Allievo')
        # Il genitore è un contatto associato dentro la scheda dello studente.
        self.guardian = self._partner('Genitore', parent_id=self.student.id)
        # hr_employee_firstname (D-22): cognome e nome sull'impiegato, che li
        # propaga sul work contact creato da hr. Niente `name`, niente split.
        self.employee = self.env['hr.employee'].create({
            'lastname': 'Maestro', 'firstname': 'Test',
        })
        self.order = self._order(self.student, [(self.product, 400.0)])
        self.order.action_confirm()

    def _partner(self, lastname, firstname='Test', **vals):
        # partner_firstname impone cognome E nome (D-21): si passano espliciti,
        # non si lascia dedurre lo split da `name`, che con l'ordine
        # `last_first` leggerebbe la prima parola come cognome.
        return self.env['res.partner'].create(
            {'lastname': lastname, 'firstname': firstname, **vals})

    def _course_product(self, name, project, price, target=4):
        """Corso a catalogo collettivo («Crea un ordine» = Nulla, lezioni
        previste) e il suo corso collettivo (`D-35`)."""
        product = self.env['product.product'].create({
            'name': name, 'type': 'service', 'list_price': price,
            'service_tracking': 'no', 'x_lesson_target': target,
        })
        project.x_course_product_id = product.product_tmpl_id
        return product

    def _order(self, student, product_prices):
        """Iscrizione = ordine standard: l'allievo è l'intestatario. Le righe
        collettive nascono già assegnate al corso del loro corso a catalogo,
        come quando la segreteria lo indica all'iscrizione."""
        Project = self.env['project.project']
        return self.env['sale.order'].create({
            'partner_id': student.id,
            'order_line': [
                (0, 0, {'product_id': product.id,
                        'price_unit': price, 'product_uom_qty': 1.0,
                        'project_id': Project.search([(
                            'x_course_product_id', '=',
                            product.product_tmpl_id.id)], limit=1).id})
                for product, price in product_prices
            ],
        })

    def _task(self, name, project=None):
        return self.env['project.task'].create({
            'name': name, 'project_id': (project or self.course).id,
            'date_deadline': '2026-09-01 13:00:00',
        })

    def _timesheet(self, task):
        return self.env['account.analytic.line'].create({
            'name': 'ore', 'task_id': task.id,
            'project_id': task.project_id.id,
            'unit_amount': 1.0, 'employee_id': self.employee.id,
            'date': '2026-09-01',
        })

    def _settlements(self, student):
        # La view SQL legge il DB: flush delle scritture + invalidazione della
        # cache di lettura, così i grezzi rispecchiano i dati appena creati.
        self.env.flush_all()
        self.env.invalidate_all()
        return self.env['bandoo.enrollment.settlement'].search(
            [('partner_id', '=', student.id)])


@tagged('standard', 'at_install', 'bandoo')
class TestSettlementIntegration(BandooCase):
    """Catena completa: iscrizione -> lezioni/timesheet/presenze -> view SQL."""

    def test_iscrizione_popola_corso(self):
        self.assertIn(self.student, self.course.enrolled_student_ids)

    def test_riga_collettiva_sul_suo_corso(self):
        self.assertEqual(self.order.order_line.project_id, self.course)

    def test_conteggi_e_recupero_collettivo(self):
        t1, t2, t3 = self._task('L1'), self._task('L2'), self._task('L3')
        # 2 lezioni tenute (timesheet), 1 giustificata su lezione tenuta.
        self._timesheet(t1)
        self._timesheet(t2)
        line = t1.attendance_line_ids.filtered(
            lambda l: l.partner_id == self.student)
        line.status = 'absent_justified'

        s = self._settlements(self.student)
        self.assertEqual(len(s), 1)
        self.assertEqual(s.target, 4)
        self.assertEqual(s.lessons_held, 2)
        self.assertEqual(s.justified_absences, 1)
        self.assertEqual(s.missed_lessons, 2)
        # prezzo lezione 100; detrazione (1+2)*100 = 300; 400-266-300 = -166
        self.assertEqual(s.deduction, 300.0)
        self.assertEqual(s.installment_3, -166.0)

        # Recupero collettivo: la 3a lezione viene tenuta (timesheet).
        # Senza alcun link esplicito, lessons_held sale -> missed scende.
        self._timesheet(t3)
        s = self._settlements(self.student)
        self.assertEqual(s.lessons_held, 3)
        self.assertEqual(s.missed_lessons, 1)
        self.assertEqual(s.justified_absences, 1)
        self.assertEqual(s.deduction, 200.0)

    def test_lezione_senza_timesheet_non_conta(self):
        # Una task senza ore registrate non è "tenuta": non riduce missed.
        self._task('L1')  # nessun timesheet
        s = self._settlements(self.student)
        self.assertEqual(s.lessons_held, 0)
        self.assertEqual(s.missed_lessons, 4)

    def test_ordine_due_righe_aggregato(self):
        # Il credito dello strumento (2 giustificate) abbatte la rata 3 del
        # solfeggio nello stesso ordine.
        solfeggio = self.env['project.project'].create({
            'name': 'Solfeggio', 'x_lesson_target': 4,
        })
        solfeggio_product = self._course_product('Solfeggio', solfeggio, 120.0)
        student = self._partner('Allievo2')
        order = self._order(student, [
            (self.product, 400.0), (solfeggio_product, 120.0),
        ])
        order.action_confirm()
        # Tutte le lezioni tenute su entrambi i corsi; sulle prime due dello
        # strumento l'allievo è assente giustificato.
        for course in (self.course, solfeggio):
            for n in range(4):
                task = self._task(f'L{n}', project=course)
                self._timesheet(task)
                if course == self.course and n < 2:
                    task.attendance_line_ids.filtered(
                        lambda l: l.partner_id == student
                    ).status = 'absent_justified'

        settlements = self._settlements(student)
        self.assertEqual(len(settlements), 2)
        strumento = settlements.filtered(lambda s: s.project_id == self.course)
        solf = settlements - strumento
        self.assertEqual(strumento.installment_3, -66.0)  # 400 - 266 - 200
        self.assertEqual(solf.installment_3, 40.0)        # 120 - 80 - 0

        order_settlement = self.env['bandoo.order.settlement'].search(
            [('order_id', '=', order.id)])
        self.assertEqual(order_settlement.total_price, 520.0)
        self.assertEqual(order_settlement.deduction, 200.0)
        self.assertEqual(order_settlement.installment_1, 173.0)  # round(520/3)
        self.assertEqual(order_settlement.installment_2, 173.0)
        # max(0, 520 - 346 - 200) = 0: il credito dello strumento assorbe
        # il solfeggio, il residuo (26) e' perso.
        self.assertEqual(order_settlement.installment_3, 0.0)

    def test_ordini_distinti_non_si_compensano(self):
        # Il credito di un ordine non abbatte la rata 3 di un altro ordine.
        student2 = self._partner('Allievo2')
        order2 = self._order(student2, [(self.product, 400.0)])
        order2.action_confirm()
        # 4 lezioni tenute: self.student con 2 giustificate (credito 66),
        # student2 sempre presente.
        for n in range(4):
            task = self._task(f'L{n}')
            self._timesheet(task)
            if n < 2:
                task.attendance_line_ids.filtered(
                    lambda l: l.partner_id == self.student
                ).status = 'absent_justified'

        self.env.flush_all()
        self.env.invalidate_all()
        order_settlements = self.env['bandoo.order.settlement'].search(
            [('order_id', 'in', (self.order | order2).ids)])
        s1 = order_settlements.filtered(lambda s: s.order_id == self.order)
        s2 = order_settlements - s1
        # Ordine con credito (detrazione 200 > residuo): rata 3 a 0...
        self.assertEqual(s1.deduction, 200.0)
        self.assertEqual(s1.installment_3, 0.0)  # max(0, 400 - 266 - 200)
        # ...ma non abbatte la rata 3 dell'altro ordine.
        self.assertEqual(s2.deduction, 0.0)
        self.assertEqual(s2.installment_3, 134.0)  # 400 - 266 - 0

    def test_rate_ordine_arrotondate_sul_totale(self):
        # Le rate 1/2 dell'ordine sono round(totale/3), non la somma delle
        # rate di riga: due corsi da 100 danno 67 (round(200/3)), non 33+33.
        projects = [self.env['project.project'].create({'name': name})
                    for name in ('Canto', 'Batteria')]
        products = [self._course_product(project.name, project, 100.0, target=2)
                    for project in projects]
        order = self._order(self.student, [(p, 100.0) for p in products])
        order.action_confirm()
        # Corsi interamente svolti e frequentati: nessuna detrazione.
        for project in projects:
            for n in range(2):
                task = self._task(f'L{n}', project=project)
                self._timesheet(task)

        self.env.flush_all()
        self.env.invalidate_all()
        order_settlement = self.env['bandoo.order.settlement'].search(
            [('order_id', '=', order.id)])
        self.assertEqual(order_settlement.total_price, 200.0)
        self.assertEqual(order_settlement.deduction, 0.0)
        self.assertEqual(order_settlement.installment_1, 67.0)  # round(200/3)
        self.assertEqual(order_settlement.installment_2, 67.0)
        self.assertEqual(order_settlement.installment_3, 66.0)  # 200 - 134

    def test_iscrizione_tardiva_conteggio_per_iscritto(self):
        # 4 lezioni tutte svolte PRIMA dell'iscrizione tardiva.
        for n in range(4):
            self._timesheet(self._task(f'L{n}'))
        late = self._partner('Tardivo')
        order = self._order(late, [(self.product, 100.0)])
        # Proposta dal corso (4), ridotta alle lezioni pattuite residue.
        self.assertEqual(order.order_line.x_lesson_target, 4)
        order.order_line.x_lesson_target = 1
        order.action_confirm()

        # Nessuna lezione erogata all'iscritto (quelle pre-iscrizione non
        # contano): detrazione piena, rata 3 d'ordine azzerata (le rate 1-2
        # restano dovute: credito oltre l'ordine perso, come da spec).
        s = self._settlements(late)
        self.assertEqual(s.target, 1)
        self.assertEqual(s.lessons_held, 0)
        self.assertEqual(s.missed_lessons, 1)
        self.assertEqual(s.deduction, 100.0)
        o = self.env['bandoo.order.settlement'].search(
            [('order_id', '=', order.id)])
        self.assertEqual(o.installment_3, 0.0)

        # La lezione residua viene erogata (creata dopo la conferma, quindi
        # include l'iscritto): nessuna detrazione, paga il concordato pieno.
        self._timesheet(self._task('L5'))
        s = self._settlements(late)
        self.assertEqual(s.lessons_held, 1)
        self.assertEqual(s.missed_lessons, 0)
        self.assertEqual(s.deduction, 0.0)
        self.assertEqual(s.installment_3, 34.0)  # 100 - 33 - 33

    def test_ordine_prezzo_zero(self):
        # Borsa di studio/scambio: ordine a prezzo zero, conguaglio a zero.
        student2 = self._partner('Borsista')
        order = self._order(student2, [(self.product, 0.0)])
        order.action_confirm()
        self.assertIn(student2, self.course.enrolled_student_ids)
        s = self._settlements(student2)
        self.assertEqual(s.annual_price, 0.0)
        self.assertEqual(s.installment_1, 0.0)
        self.assertEqual(s.installment_3, 0.0)


@tagged('standard', 'at_install', 'bandoo')
class TestEnrollmentFlow(BandooCase):
    """Iscrizione come ordine standard: validazioni ed elenco iscritti."""

    def test_prodotto_non_corso_senza_vincoli(self):
        fee = self.env['product.product'].create({
            'name': 'Quota associativa', 'type': 'service', 'list_price': 30.0,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.student.id,
            'order_line': [(0, 0, {
                'product_id': fee.id, 'price_unit': 30.0,
                'product_uom_qty': 1.0,
            })],
        })
        order.action_confirm()  # non è un corso: nessun corso agganciato
        self.assertFalse(order.order_line.project_id)

    def test_riga_aggiunta_a_ordine_confermato_iscrive(self):
        # Le righe aggiunte a un ordine già confermato nascono in stato
        # 'sale' senza passare da action_confirm: l'iscrizione dell'intestatario
        # al nuovo corso deve scattare comunque (buco emerso dal test manuale
        # 2026-07-10). Un ordine = un allievo, più corsi.
        solfeggio = self.env['project.project'].create({
            'name': 'Solfeggio', 'x_lesson_target': 4})
        solfeggio_product = self._course_product('Solfeggio', solfeggio, 120.0)
        self.order.write({'order_line': [(0, 0, {
            'product_id': solfeggio_product.id, 'project_id': solfeggio.id,
            'price_unit': 120.0, 'product_uom_qty': 1.0,
        })]})
        self.assertIn(self.student, solfeggio.enrolled_student_ids)

    def test_durata_scende_su_registro_e_lezioni(self):
        """La durata dell'articolo diventa Tempo assegnato sulle lezioni.

        Senza, le ore registrate dall'insegnante non hanno un termine di
        confronto e il compenso si fonda su un numero non verificabile.
        """
        template = self.env['project.project'].create({
            'name': 'Template Prova', 'allow_timesheets': True,
            'allow_billable': True,
        })
        product = self.env['product.product'].create({
            'name': 'Corso Individuale Prova', 'type': 'service',
            'list_price': 600.0, 'service_tracking': 'project_only',
            'project_template_id': template.id, 'x_lesson_duration': 45,
            'x_lesson_target': 30,
        })
        order = self._order(self.student, [(product, 600.0)])
        order.action_confirm()
        registro = order.order_line.project_id

        self.assertEqual(registro.x_lesson_duration, 45)
        # 30 lezioni previste da 45 minuti = 22,5 ore d'anno
        self.assertAlmostEqual(registro.allocated_hours, 22.5)

        # vale anche per una lezione aggiunta a mano: e' il caso dei saggi
        lezione = self.env['project.task'].create(
            {'name': 'Saggio invernale', 'project_id': registro.id})
        self.assertAlmostEqual(lezione.allocated_hours, 0.75)

    def test_insegnante_su_riga_collettiva_respinto(self):
        """Il corso collettivo ha gia' il suo responsabile: indicarlo sulla
        riga non farebbe nulla, quindi viene respinto."""
        # partner_firstname (D-21) rifiuta un partner senza cognome e nome,
        # e la creazione di un utente ne crea uno: vanno passati espliciti.
        user = self.env['res.users'].create({
            'lastname': 'Insegnante', 'firstname': 'Test',
            'login': 'ins@bandoo.test'})
        self.env['hr.employee'].create({
            'lastname': 'Insegnante', 'firstname': 'Test', 'user_id': user.id})
        with self.assertRaises(ValidationError):
            self.order.order_line[0].x_teacher_id = user

    def test_due_righe_stesso_corso_respinte(self):
        """Due iscrizioni allo stesso corso nello stesso ordine: bloccate.

        Senza il vincolo condividerebbero un registro solo, e il conguaglio
        conterebbe le stesse lezioni per entrambe.
        """
        with self.assertRaises(ValidationError):
            self._order(self.student, [(self.product, 400.0),
                                       (self.product, 400.0)])

    def test_riga_azzerata_non_impedisce_reiscrizione(self):
        """Una riga annullata (quantita' zero) non fa doppione: si puo'
        reiscrivere allo stesso corso nello stesso ordine."""
        order = self._order(self.student, [(self.product, 400.0)])
        order.order_line.product_uom_qty = 0
        self.env['sale.order.line'].create({
            'order_id': order.id, 'product_id': self.product.id,
            'price_unit': 400.0, 'product_uom_qty': 1.0})
        self.assertEqual(len(order.order_line), 2)

    def test_riga_azzerata_non_iscrive(self):
        # Su ordine confermato le righe non si eliminano: la convenzione
        # Odoo è quantità 0. La riga azzerata non deve iscrivere né contare
        # nei conguagli (buco emerso dal test manuale 2026-07-10).
        solfeggio = self.env['project.project'].create({
            'name': 'Solfeggio', 'x_lesson_target': 4})
        solfeggio_product = self._course_product('Solfeggio', solfeggio, 120.0)
        self.order.write({'order_line': [(0, 0, {
            'product_id': solfeggio_product.id, 'project_id': solfeggio.id,
            'price_unit': 120.0, 'product_uom_qty': 1.0,
        })]})
        self.assertIn(self.student, solfeggio.enrolled_student_ids)

        line = self.order.order_line.filtered(
            lambda l: l.project_id == solfeggio)
        line.product_uom_qty = 0.0
        self.assertNotIn(self.student, solfeggio.enrolled_student_ids)
        self.assertFalse(self._settlements(self.student).filtered(
            lambda s: s.project_id == solfeggio))
        order_settlement = self.env['bandoo.order.settlement'].search(
            [('order_id', '=', self.order.id)])
        self.assertEqual(order_settlement.total_price, 400.0)  # solo Chitarra

    def test_annullamento_esclude_da_lezioni_successive(self):
        student2 = self._partner('Allievo2')
        order2 = self._order(student2, [(self.product, 400.0)])
        order2.action_confirm()
        self.assertIn(student2, self.course.enrolled_student_ids)

        order2._action_cancel()
        self.assertNotIn(student2, self.course.enrolled_student_ids)
        task = self._task('L1')
        self.assertNotIn(student2, task.attendance_line_ids.partner_id)
        self.assertIn(self.student, task.attendance_line_ids.partner_id)

    def test_riallineamento_alla_conferma(self):
        t_rendicontata, t_futura = self._task('L1'), self._task('L2')
        self._timesheet(t_rendicontata)
        # Iscrizione a metà anno: la conferma iscrive alle sole lezioni non
        # rendicontate, senza premere niente (S-08).
        student2 = self._partner('Tardivo')
        self._order(student2, [(self.product, 200.0)]).action_confirm()
        self.assertIn(student2, t_futura.attendance_line_ids.partner_id)
        self.assertNotIn(student2, t_rendicontata.attendance_line_ids.partner_id)

    def test_riallinea_presenze_nei_due_sensi(self):
        task = self._task('L1')
        intruso = self._partner('Intruso')
        task.attendance_line_ids = [(0, 0, {'partner_id': intruso.id})]
        task.attendance_line_ids.filtered(
            lambda l: l.partner_id == self.student).unlink()

        self.course.action_align_attendance()
        # Torna chi è iscritto, esce chi non lo è; rilanciato non duplica.
        self.assertEqual(task.attendance_line_ids.partner_id, self.student)
        self.course.action_align_attendance()
        self.assertEqual(len(task.attendance_line_ids), 1)

    def test_constraint_individuale_malconfigurato(self):
        # Un corso a catalogo individuale vuole modello, durata e lezioni
        # previste (`D-34`).
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['product.product'].create({
                'name': 'Corso rotto', 'type': 'service',
                'service_tracking': 'project_only', 'x_lesson_target': 4,
            })



@tagged('standard', 'at_install', 'bandoo')
class TestCollectiveCourses(BandooCase):
    """Corsi collettivi: più corsi per corso a catalogo (`S-08`, `D-32`)."""

    def setUp(self):
        super().setUp()
        # Secondo corso dello stesso corso a catalogo.
        self.course_b = self.env['project.project'].create({
            'name': 'Chitarra B',
            'x_course_product_id': self.product.product_tmpl_id.id,
        })

    def test_cambio_corso_collettivo(self):
        # A: una lezione rendicontata e una no; B: una lezione da fare.
        a_done, a_todo = self._task('A1'), self._task('A2')
        self._timesheet(a_done)
        b_todo = self._task('B1', project=self.course_b)

        self.order.order_line.project_id = self.course_b
        # Le rendicontate restano, le non rendicontate passano al nuovo corso.
        self.assertIn(self.student, a_done.attendance_line_ids.partner_id)
        self.assertNotIn(self.student, a_todo.attendance_line_ids.partner_id)
        self.assertIn(self.student, b_todo.attendance_line_ids.partner_id)
        # Il consuntivo conta su tutti i corsi del corso a catalogo.
        self._timesheet(b_todo)
        s = self._settlements(self.student)
        self.assertEqual(s.lessons_held, 2)
        self.assertEqual(s.target, 4)

    def test_riga_senza_corso_poi_assegnata(self):
        student2 = self._partner('DaAssegnare')
        order = self.env['sale.order'].create({
            'partner_id': student2.id,
            'order_line': [(0, 0, {'product_id': self.product.id,
                                   'price_unit': 400.0})],
        })
        order.action_confirm()
        # Confermata senza corso: compare fra i «Collettivi da assegnare»,
        # ed è già nel consuntivo, con zero lezioni.
        action = self.env.ref(
            'bandoo_school_sale.action_sale_order_line_collective_to_assign')
        to_assign = self.env['sale.order.line'].search(
            safe_eval(action.domain))
        self.assertIn(order.order_line, to_assign)
        self.assertEqual(self._settlements(student2).lessons_held, 0)

        order.order_line.project_id = self.course_b
        self.assertIn(student2, self.course_b.enrolled_student_ids)
        self.assertNotIn(order.order_line, self.env['sale.order.line'].search(
            safe_eval(action.domain)))

    def test_corso_di_altro_catalogo_respinto(self):
        other = self.env['project.project'].create({'name': 'Altro'})
        self._course_product('Altro', other, 100.0)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.order.order_line.project_id = other

@tagged('standard', 'at_install', 'bandoo')
class TestLessonFlags(BandooCase):
    """Punto 4/5: 'Ai fini retta' derivato dallo stato, 'svolta' dalle ore."""

    def test_billing_status_derivato(self):
        task = self._task('L1')
        line = task.attendance_line_ids
        self.assertEqual(line.billing_status, 'pays')
        line.status = 'absent'
        self.assertEqual(line.billing_status, 'pays')
        line.status = 'absent_justified'
        self.assertEqual(line.billing_status, 'free')

    def test_svolta_derivata_dalle_ore(self):
        t1, t2 = self._task('L1'), self._task('L2')
        self.assertFalse(t1.x_is_held)
        self._timesheet(t1)
        self.assertTrue(t1.x_is_held)
        Task = self.env['project.task']
        self.assertEqual(
            Task.search([('project_id', '=', self.course.id),
                         ('x_is_held', '=', True)]), t1)
        self.assertEqual(
            Task.search([('project_id', '=', self.course.id),
                         ('x_is_held', '=', False)]), t2)


@tagged('standard', 'at_install', 'bandoo')
class TestIndividualCourse(BandooCase):
    """Corso individuale: progetto generato da template alla conferma."""

    def setUp(self):
        super().setUp()
        # Attivata esplicitamente: il test confronta il nome anche in it_IT,
        # e su un database appena creato quella lingua non esiste. Senza
        # questa riga il test passa solo dove l'italiano è già installato.
        self.env['res.lang']._activate_lang('it_IT')
        self.template = self.env['project.project'].create({
            'name': 'Template Pianoforte', 'active': False,
        })
        self.piano = self.env['product.product'].create({
            'name': 'Lezioni Pianoforte', 'type': 'service',
            'list_price': 400.0, 'service_tracking': 'project_only',
            'project_template_id': self.template.id,
            'x_lesson_target': 4, 'x_lesson_duration': 45,
        })

    def test_individuale_end_to_end(self):
        order = self._order(self.student, [(self.piano, 400.0)])
        order.action_confirm()
        line = order.order_line

        # Corso generato dal modello: attivo, lezioni previste copiate dalla
        # riga, zero lezioni fantasma; la riga lo aggancia via project_id.
        project = line.project_id
        self.assertTrue(project)
        self.assertNotEqual(project, self.template)
        self.assertTrue(project.active)
        self.assertEqual(project.x_lesson_target, 4)
        self.assertFalse(project.tasks)
        # `Allievo Test` è `res.partner.name` ricomposto da partner_firstname
        # nell'ordine `Cognome Nome` deciso in D-21: il letterale vale anche da
        # sentinella se quell'ordine cambiasse.
        self.assertEqual(project.name, 'Lezioni Pianoforte - Allievo Test')
        # Il nome è coerente in tutte le lingue (campo traducibile).
        self.assertEqual(
            project.with_context(lang='it_IT').name,
            'Lezioni Pianoforte - Allievo Test')

        # Elenco iscritti derivato: il solo studente dell'ordine.
        self.assertEqual(project.enrolled_student_ids, self.student)

        # Lezione generata -> presenze del solo studente; conguaglio ok.
        task = self._task('L1', project=project)
        self.assertEqual(task.attendance_line_ids.partner_id, self.student)
        self._timesheet(task)
        s = self._settlements(self.student).filtered(
            lambda s: s.project_id == project)
        self.assertEqual(s.target, 4)
        self.assertEqual(s.lessons_held, 1)
        self.assertEqual(s.missed_lessons, 3)


@tagged('standard', 'at_install', 'bandoo')
class TestLineTracking(BandooCase):
    """Modifiche alla riga di iscrizione confermata: traccia nel chatter
    dell'iscrizione, come fa Odoo per la quantità (`S-03`)."""

    def _tracking_bodies(self, order):
        return [str(m.body) for m in order.message_ids
                if 'Riga di iscrizione modificata' in str(m.body)]

    def test_lezioni_previste_tracciate(self):
        self.order.order_line.x_lesson_target = 2
        bodies = self._tracking_bodies(self.order)
        self.assertEqual(len(bodies), 1)
        self.assertIn('Lezioni previste: 4 → 2', bodies[0])

    def test_prezzo_tracciato(self):
        self.order.order_line.price_unit = 300.0
        bodies = self._tracking_bodies(self.order)
        self.assertEqual(len(bodies), 1)
        self.assertIn('Prezzo unitario:', bodies[0])

    def test_cambio_corso_collettivo_tracciato(self):
        course_b = self.env['project.project'].create({
            'name': 'Chitarra B',
            'x_course_product_id': self.product.product_tmpl_id.id,
        })
        self.order.order_line.project_id = course_b
        bodies = self._tracking_bodies(self.order)
        self.assertEqual(len(bodies), 1)
        self.assertIn('Corso: Chitarra → Chitarra B', bodies[0])

    def test_cambio_prodotto_respinto_a_ordine_confermato(self):
        # Il prodotto non si traccia perché non si cambia: `sale_project`
        # rende non modificabile il prodotto di un servizio confermato.
        other = self._course_product(
            'Corso Violino', self.env['project.project'].create(
                {'name': 'Violino'}), 500.0)
        with self.assertRaises(UserError):
            self.order.order_line.product_id = other

    def test_modifica_in_bozza_non_tracciata(self):
        draft = self._order(self._partner('Bozza'), [(self.product, 400.0)])
        draft.order_line.x_lesson_target = 2
        self.assertFalse(self._tracking_bodies(draft))

    def test_modifica_senza_cambiamenti_non_tracciata(self):
        self.order.order_line.write({'x_lesson_target': 4, 'name': 'Altro'})
        self.assertFalse(self._tracking_bodies(self.order))
