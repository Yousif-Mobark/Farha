
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PosRecapReportWizard(models.TransientModel):
    _name = 'pos.recap.report.wizard'

    def _default_date_start(self):
        print("lkfddddddddddddd")
        my_date = date.today()
        my_time = datetime.min.time()
        date_start = datetime.combine(my_date, my_time)
        print("lkfddddddddddddd")
        return date_start

    def _default_date_end(self):
        print("lkfddddddddddddd")
        my_date = date.today()
        my_time = datetime.min.time()
        date_start = datetime.combine(my_date, my_time)
        result = date_start + timedelta(hours=23, minutes=59 ,seconds=59)
        return result


    date_start = fields.Datetime(string="Start Date", required=True, default=_default_date_start)
    date_end = fields.Datetime(string="End Date", required=True, default=_default_date_end)
    pos_config_ids = fields.Many2many('pos.config', default=lambda s: s.env['pos.config'].search([]))


    @api.multi
    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref('cj_custom_report.recap_report').report_action(self, data=data)


class ReportPosRecap(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.cj_custom_report.pos_recap_report_view'

    @api.model
    def get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        # date_start_obj = datetime.strptime(date_start, '%Y-%m-%d ')
        # date_end_obj = datetime.strptime(date_end, '%Y-%m-%d')

        docs = []

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'docs': docs,
        }

