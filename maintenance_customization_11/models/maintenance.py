from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class MaintenanceRequests(models.Model):
    _inherit = 'maintenance.request'
    _description = 'Maintenance Management'

    call_date = fields.Datetime(string="Call Received Date", required=True, default=str(datetime.now()))
    bank_name = fields.Many2one('res.partner',string="Bank Name")
    location = fields.Char(string="Location")
    city = fields.Char(string="City")
    serial_number = fields.Char(string="Serial Number", size=50, )
    maintenance_type = fields.Selection(
        [('corrective', 'Corrective'), ('preventive', 'Preventive'), ('periodic', 'Periodic')], string='Maintenance Type',
        default="corrective")
    status = fields.Selection(
        [('warranty', 'Warranty'), ('contract', 'Contract'), ('call', 'Per Call'), ('inspection', 'Inspection')],
        string="State",
        default="warranty")
    state = fields.Selection(
        [('warranty', 'Warranty'), ('contract', 'Contract'), ('call', 'Per Call'), ('inspection', 'Inspection')],
        string="State",
        default="warranty")
    depature_time = fields.Datetime(string="Depature time",  default=str(datetime.now()))
    arrival_time = fields.Datetime(string="Arrival time",  default=str(datetime.now()))
    consumed_time = fields.Datetime(string="Time Consumed ",  default=str(datetime.now()))
    work_start_time = fields.Datetime(string="Work Time From",  default=str(datetime.now()),
                                      help="Start time of work")
    work_end_time = fields.Datetime(  help="End time of work")
    model = fields.Many2one('equipments.model', string="Model", )
    spar_part_id = fields.One2many('spar.part', 'maintenance_request_id', string="Spar Part")
    fault = fields.Text(string='Fault')
    cuase = fields.Text(string='Cuase')
    action = fields.Text(string="Action")
    comment = fields.Text(string="comment")


class Spar_part(models.Model):
    _name = 'spar.part'
    _description = ""

    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade')
    name = fields.Many2one('product.product', stirng='Service', required=True)
    description = fields.Text('Description', required=True)
    qty = fields.Float('Requested Qty', default=1)


class Equipments_model(models.Model):
    _name = 'equipments.model'
    _rec_name = "name"
    _description = 'Equipments Model'

    name = fields.Char(string="Name")
    code = fields.Char(string="code")
