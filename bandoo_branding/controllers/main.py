from odoo import http
from odoo.addons.hr_attendance_reason.controllers.main import HrAttendance

"""
Log Warning:
    WARNING bandoo odoo.http:
    <function odoo.addons.hr_attendance_reason.controllers.main.manual_selection_with_geolocation>
    called ignoring args {'attendance_reason_id'}

Solution:
  - bandoo_branding/__init__.py — imports the new controllers package
  - bandoo_branding/controllers/__init__.py — imports main
  - bandoo_branding/controllers/main.py — subclasses the OCA controller
    - adding attendance_reason_id=False to the signature so Odoo's HTTP layer passes it through instead of ignoring it
    - added @http.route("/hr_attendance/manual_selection", type="json", auth="public") matching
      the OCA original. Odoo requires overriding controller methods to repeat the decorator.
      Without it, Odoo auto-decorates and warns.
"""

class HrAttendance(HrAttendance):
    @http.route("/hr_attendance/manual_selection", type="json", auth="public")
    def manual_selection_with_geolocation(
        self, token, employee_id, pin_code,
        latitude=False, longitude=False, attendance_reason_id=False,
    ):
        return super().manual_selection_with_geolocation(
            token, employee_id, pin_code, latitude, longitude
        )
