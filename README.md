# Bandoo addons

Odoo 18 addons for the Bandoo project — a music school running on top of
Odoo's Project, Timesheet and Sales apps.

Three modules, layered by dependency:

## bandoo_school

Core domain: courses, lessons, attendance.

- Courses are `project.project` records; lessons are `project.task` records
  (with an `Aula` / room, a teacher, and a "held" flag).
- `bandoo.room` — physical rooms.
- `bandoo.lesson.student.line` — per-student attendance on each lesson, with
  a status (present / justified / unjustified) and a computed billing status.
- `bandoo.lesson.attendance` — read-only SQL view aggregating attendance for
  reporting.
- `bandoo.lesson.generate` wizard — bulk-generates recurring lessons for a
  course (start date, time, count, weekly interval).

Depends on: `project`, `hr_timesheet`, `contacts`.

## bandoo_school_sale

Sales layer on top of `bandoo_school`: enrollments, fees and settlement.

- A `product.template` can be flagged as a course and linked to a course
  project; a `sale.order.line` then carries the enrolled student and target
  number of lessons.
- `bandoo.enrollment.settlement` — per-enrollment settlement: yearly price,
  lessons held, justified absences, price per lesson, deduction and the three
  installments.
- `bandoo.order.settlement` — per-order settlement, aggregating the lines.
- `res.partner` gains a `Socio` (member) flag.

Depends on: `bandoo_school`, `sale_management`, `sale_project`.

## bandoo_branding

Login-page branding and the meta-module that pins the full list of modules
to install for a Bandoo instance.

- Custom logo and login templates.
- Its `depends` list is the effective install manifest for the deployment
  (HR, attendance, timesheets, portal, spreadsheet dashboards, TOTP, …),
  including `bandoo_school` and `bandoo_school_sale`.
