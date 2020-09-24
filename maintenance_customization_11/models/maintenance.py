from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class MaintenanceRequests(models.Model):
    _inherit = 'maintenance.request'
    _description = 'Maintenance Management'

    call_date = fields.Datetime(string="Call Received Date", required=True, default=str(datetime.now()))
    bank_name = fields.Many2one('res.partner', string="Bank Name")
    location = fields.Char(string="Location")
    city = fields.Char(string="City")
    serial_number = fields.Char(string="Serial Number", size=50, )
    maintenance_type = fields.Selection(
        [('corrective', 'Corrective'), ('preventive', 'Preventive'), ('periodic', 'Periodic')],
        string='Maintenance Type',
        default="corrective")
    state = fields.Selection(
        [('draft', 'Draft'), ('supervisor', 'Supervisor'), ('engineer', 'Engineers'), ('done', 'Done')],
        string="State",
        default="draft")
    status = fields.Selection(
        [('warranty', 'Warranty'), ('contract', 'Contract'), ('call', 'Per Call'), ('inspection', 'Inspection')],
        string="Status",
        default="warranty")
    depature_time = fields.Datetime(string="Depature time", default=str(datetime.now()))
    arrival_time = fields.Datetime(string="Arrival time", default=str(datetime.now()))
    consumed_time = fields.Datetime(string="Time Consumed ", default=str(datetime.now()))
    work_start_time = fields.Datetime(string="Work Time From", default=str(datetime.now()),
                                      help="Start time of work")
    work_end_time = fields.Datetime(help="End time of work")
    model = fields.Many2one('equipments.model', string="Model", )
    spar_part_id = fields.One2many('spar.part', 'maintenance_request_id', string="Spar Part")
    fault = fields.Text(string='Fault')
    cuase = fields.Text(string='Cuase')
    action = fields.Text(string="Action")
    comment = fields.Text(string="comment")

    @api.multi
    def button_stock_picking(self):
        if self.spar_part_id:
           print(50*'#')
           self._create_picking()
        if self.state == 'engineer':
            self.state = 'done'

    @api.multi
    def button_draft_supervisor(self):
        if self.state == 'draft':

           self.state = 'supervisor'

    @api.multi
    def button_supervisor_eng(self):
        if self.state == 'supervisor':
           self.state = 'engineer'





    def _get_picking_type(self):
        company = self.env['res.company']._company_default_get('maintenance.request')
        pick_in = self.env['stock.picking.type'].search(
            [('warehouse_id.company_id', '=', company.id), ('code', '=', 'outgoing')], limit=1,
        )
        return pick_in[0]

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', default = _get_picking_type)

    @api.model
    def _prepare_picking(self):
        picking_type_id = self.picking_type_id
        print(picking_type_id)
        location = self.env.ref('stock.stock_location_customers')

        return {
            'picking_type_id': picking_type_id.id,
            'date_order': self.work_end_time,
            'origin': self.name,
            'location_dest_id': picking_type_id.default_location_dest_id.id or location.id,
            'location_id': picking_type_id.default_location_src_id.id,
            # 'company_id': self.company_id.id,
            'maintenance_request_id': self.id,
            'state': 'assigned',
        }

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            res = order._prepare_picking()
            picking = StockPicking.create(res)
            print(picking)
            moves = order.spar_part_id._create_stock_moves(picking)
            moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))
            seq = 0
            for move in sorted(moves, key=lambda move: move.date_expected):
                seq += 5
                move.sequence = seq




class Spar_part(models.Model):
    _name = 'spar.part'
    _description = ""

    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', stirng='Service', required=True)
    description = fields.Text('Description', required=True)
    qty = fields.Float('Requested Qty', default=1)

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        res = []
        template = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.qty,
            'date': self.maintenance_request_id.work_end_time,
            'date_expected': self.maintenance_request_id.work_end_time,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            # 'company_id': self.request_id.company_id.id,
            'price_unit': self.product_id.standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.maintenance_request_id.name,
            'warehouse_id': self.maintenance_request_id.picking_type_id.warehouse_id.id,
            # 'account_analytic_id': self.account_analytic_id.id,
        }
        return self.env['stock.move'].create(template)

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            val = line._prepare_stock_moves(picking)

        return done



class Equipments_model(models.Model):
    _name = 'equipments.model'
    _rec_name = "name"
    _description = 'Equipments Model'

    name = fields.Char(string="Name")
    code = fields.Char(string="code")







