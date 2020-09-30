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
    consumed_time = fields.Char(string="Time Consumed ", default=0)
    work_start_time = fields.Datetime(string="Work Time From", default=str(datetime.now()),
                                      help="Start time of work")
    work_end_time = fields.Datetime(help="End time of work")
    model = fields.Many2one('equipments.model', string="Model", )
    spar_part_id = fields.One2many('spar.part', 'maintenance_request_id', string="Spar Part")
    fault = fields.Text(string='Fault')
    cuase = fields.Text(string='Cuase')
    action = fields.Text(string="Action")
    comment = fields.Text(string="comment")
    picking_from_stock_id = fields.Many2one('stock.picking', string='Stock Picking')
    picking_from_technician_id = fields.Many2one('stock.picking', string='Stock technician')
    sale_order_id = fields.Many2one('sale.order', string='Sale Oredr')

    @api.constrains('work_start_time', 'work_end_time')
    def end_date_constrain(self):
        if self.work_start_time > self.work_end_time:
            print(10 * "cons")
            raise UserError(_("Work start Date must be greater the work end date"))

    @api.multi
    @api.onchange('work_start_time', 'work_end_time')
    def _compute_consumed_time(self):
        for record in self:
            if record.work_start_time and record.work_end_time:
                work_end_time = datetime.strptime(record.work_start_time, '%Y-%m-%d %H:%M:%S')
                work_start_time = datetime.strptime(record.work_end_time, '%Y-%m-%d %H:%M:%S')
                self.consumed_time = abs((work_start_time - work_end_time).days)

    @api.multi
    def button_stock_picking(self):

        if self.spar_part_id:
            print(50 * '#')
            self._create_picking()
            self._create_sale_order()
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

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', default=_get_picking_type, required=True)

    @api.model
    def _prepare_picking_stock(self):
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

    @api.model
    def _prepare_picking_technician(self):
        picking_type_id = self.picking_type_id
        print(picking_type_id)
        location = self.env.ref('stock.stock_location_customers')

        return {
            'picking_type_id': picking_type_id.id,
            'date_order': self.work_end_time,
            'origin': self.name,
            'location_dest_id': picking_type_id.default_location_dest_id.id or location.id,
            'location_id': self.employee_id.location_id.id or picking_type_id.default_location_src_id.id,
            # 'company_id': self.company_id.id,
            'maintenance_request_id': self.id,
            'state': 'assigned',
        }

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            res_stock = order._prepare_picking_stock()
            res_techinicain = order._prepare_picking_technician()
            picking_stock = StockPicking.create(res_stock)
            picking_technician = StockPicking.create(res_techinicain)
            print(picking_stock)
            print(picking_technician)
            moves_stock = order.spar_part_id._create_stock_moves(picking_stock, None)
            moves_stock = moves_stock.filtered(lambda x: x.state not in ('done', 'cancel'))
            seq = 0
            for move in sorted(moves_stock, key=lambda move: move.date_expected):
                seq += 5
                move.sequence = seq
            moves_technician = order.spar_part_id._create_stock_moves(None, picking_technician)

            moves_technician = moves_technician.filtered(lambda x: x.state not in ('done', 'cancel'))
            seq = 0
            for move in sorted(moves_technician, key=lambda move: move.date_expected):
                seq += 5
                move.sequence = seq
            if picking_stock.move_lines:
                print(13 * '1')
                order.write({'picking_from_stock_id': picking_stock.id})
            else:
                picking_stock.unlink()
                print(13 * '2')
            if picking_technician.move_lines:
                order.write({'picking_from_technician_id': picking_technician.id})
                print(13 * '3')
            else:
                picking_technician.unlink()
                print(13 * '4')

    @api.model
    def _prepare_sale_order(self):

        return {
            'partner_id': self.bank_name.id,
            'validity_date': date.today(),
            'state': 'draft',
        }

    @api.multi
    def _create_sale_order(self):
        SaleOrder = self.env['sale.order']
        for order in self:
            res_sale = order._prepare_sale_order()
            sale_order = SaleOrder.create(res_sale)
            print(sale_order.partner_id.name)
            move = order.spar_part_id.create_sale_order_line(sale_order)
            order.write({'sale_order_id': sale_order.id})
            # order.sale_order_id = sale_order.id


class Spar_part(models.Model):
    _name = 'spar.part'
    _description = ""

    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', stirng='Service', required=True)
    description = fields.Char('Description', related='product_id.name')
    qty = fields.Float('Requested Qty', default=1)
    spar_source = fields.Selection([('stock', 'Stock'), ('technician', 'Technician')])
    location_id = fields.Many2one('stock.location', string='Source Location', readonly=True)
    location_dest_id = fields.Many2one('stock.location', string='Source Dist Location', readonly=True)
    stock_spar = fields.Boolean('From Stock', defualt=False)
    warranty = fields.Boolean('Warranty', defualt=False)

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        location = self.env.ref('stock.stock_location_customers')
        for rec in self:
            if rec.spar_source == 'stock' and rec.warranty == False:
                rec.location_id = rec.maintenance_request_id.picking_type_id.default_location_src_id.id \
                                  or location.id,
                rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id.id or location.id
            elif rec.spar_source == 'technician' and rec.warranty == False:
                rec.location_id = rec.maintenance_request_id.employee_id.location_id.id or location.id
                rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id or location.id

        res = []
        template = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.qty,
            'date': self.maintenance_request_id.work_end_time,
            'date_expected': self.maintenance_request_id.work_end_time,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
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
    def _create_stock_moves(self, picking_stock, picking_technicain):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self.filtered(lambda x: x.spar_source == 'stock' and x.warranty == False):
            print(line.product_id.name)
            print(30 * 'q')
            if picking_stock:
                val = line._prepare_stock_moves(picking_stock)
        for line in self.filtered(lambda x: x.spar_source == 'technician' and x.warranty == False):
            print(line.product_id.name)
            print(30 * 'b')
            if picking_technicain:
                val = line._prepare_stock_moves(picking_technicain)

        return done

    @api.multi
    def _prepare_sale_order_line(self, order_id):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        location = self.env.ref('stock.stock_location_customers')
        for rec in self:
            if rec.warranty == True:
                rec.location_id = rec.maintenance_request_id.picking_type_id.default_location_src_id.id \
                                  or location.id,
                rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id.id or location.id
            elif rec.warranty == True:
                rec.location_id = rec.maintenance_request_id.employee_id.location_id.id or location.id
                rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id.id or location.id

        res = []
        template = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.qty,
            'order_id': order_id.id,
            'location_dest_id': self.location_dest_id.id,
            'location_id': self.location_id.id,
            'state': 'draft',
        }
        print(self.location_id, self.location_dest_id)
        return self.env['sale.order.line'].create(template)

    @api.multi
    def create_sale_order_line(self, order_id):
        done = self.env['sale.order.line'].browse()
        # done = self.env['stock.move'].browse()
        for line in self.filtered(lambda x: x.warranty == True):
            val = line._prepare_sale_order_line(order_id)
        return done


class Equipments_model(models.Model):
    _name = 'equipments.model'
    _rec_name = "name"
    _description = 'Equipments Model'

    name = fields.Char(string="Name")
    code = fields.Char(string="code")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale order line Model'

    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Source Location')


class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'

    @api.model
    def create(self, vals):
        result = super(StockMove, self).create(vals)
        if result.sale_line_id :
            print(20 * "osman", result.sale_line_id.location_id)
            result.location_id = result.sale_line_id.location_id
        # self.write({
        #     'location_id': result.sale_line_id.location_id
        # })
        # self.sale_line_id.location_dest_id:
            print(20 * "osman", result.sale_line_id.location_dest_id)
            result.location_dest_id = result.location_dest_id
        # self.write({
        #     'location_dest_id': result.location_dest_id
        # })
        return result


class manufacturingRequests(models.Model):
    _name = 'manufacturing.request'
    _description = 'Maintenance Management'

    name = fields.Char(string="Location")
    product_id = fields.Many2one('product.product', string ="Product", required=True)
    employee_id = fields.Many2one('hr.employee_id', string="Employee", required=True)
    department_id = fields.Many2one( 'hr.department', string="Department" , required=True)
    start_date = fields.Datetime(string='Start Date', default=str(datetime.now()), required='True')
    end_date = fields.Datetime(string='End Date', default=str(datetime.now()), required='True')
    defect = fields.Text(string="Defect")
    picking_stock_id = fields.Many2one('stock.picking', string='Stock Picking',readonly=True)
    spar_part_id = fields.One2many('spar.manufacturing', 'manufacturing_request_id', string="Spar Part")
    state = fields.Selection(
        [('draft', 'Draft'), ('inprogress', 'In progress'), ('done', 'Finshed')],
        string="State",
        default="draft")

    def _get_picking_type(self):
        company = self.env['res.company']._company_default_get('maintenance.request')
        pick_in = self.env['stock.picking.type'].search(
            [('warehouse_id.company_id', '=', company.id), ('code', '=', 'outgoing')], limit=1,
        )
        return pick_in[0]

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', default=_get_picking_type, required=True)


class SparManufacturing(models.Model):
    _name = 'spar.manufacturing'
    _description = ""

    manufacturing_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', stirng='Service', required=True)
    description = fields.Char('Description', related='product_id.name')
    qty = fields.Float('Requested Qty', default=1)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    product_qty = fields.Float('Requested Qty')


    @api.onchange('product_id')
    def get_product_decription(self):
        if self.product_id:
            print("ppppppppppppppppppppp")
            self.description = self.product_id.name
            self.product_uom_id = self.product_id.uom_id.id


    @api.multi
    def button_draft_inprogress(self):

        if self.state == 'draft':
            self.state = 'inprogress'


    @api.multi
    def button_inprogress_done(self):
        if self.state == 'inprogress':
            self.state = 'done'







