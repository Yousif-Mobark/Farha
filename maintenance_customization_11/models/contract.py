from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class EquipmentsContract(models.Model):
    _name = 'equipment.contract'
    _rec_name = "name"
    _description = ''

    name = fields.Char(string='name', required=True)
    equipment = fields.Many2one('maintenance.equipment', string='Equipment',required='True')
    start_date = fields.Datetime(string='Date', default=str(datetime.now()), required='True')
    end_date = fields.Datetime(string='Date', default=str(datetime.now()), required='True')
    state = fields.Selection(
        [('draft', 'Draft'), ('valid', 'Valid'), ('expired', 'Expired')],
        string="State",
        default="draft")
    note = fields.Text('Internal Note')

    @api.multi
    def button_state(self):
        if self.state=='draft':
            self.state='valid'
        elif self.state=='valid':
            self.state = 'expired'