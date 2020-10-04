from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class manufacturingRequests(models.Model):
    _name = 'manufacturing.request'
    _description = 'Maintenance Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="name", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    start_date = fields.Datetime(string='Start Date', default=str(datetime.now()), required='True')
    end_date = fields.Datetime(string='End Date', default=str(datetime.now()), required='True')
    defect = fields.Text(string="Defect")
    picking_stock_out_id = fields.Many2one('stock.picking', string='Stock Picking', readonly=True)
    picking_stock_in_id = fields.Many2one('stock.picking', string='Stock Picking', readonly=True)
    spar_part_id = fields.One2many('spar.manufacturing', 'manufacturing_request_id', string="Spar Part")
    state = fields.Selection(
        [('draft', 'Draft'), ('inprogress', 'In progress'), ('done', 'Finshed')],
        string="State",
        default="draft")

    @api.multi
    def button_draft_inprogress(self):
        if self.state == 'draft':
            self._create_picking_out()
            self.state = 'inprogress'


    @api.multi
    def button_inprogress_done(self):
        if self.state == 'inprogress' and self.picking_stock_out_id.state=='done':
            self._create_picking_in()
            self.state = 'done'
        else:
            raise UserError(_("You must validate the picking '%s' first" )%(self.picking_stock_out_id.name,))

    def _get_picking_type(self):
        company = self.env['res.company']._company_default_get('maintenance.request')
        pick_in = self.env['stock.picking.type'].search(
            [('warehouse_id.company_id', '=', company.id), ('code', '=', 'outgoing')], limit=1,
        )
        return pick_in[0]

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', default=_get_picking_type, required=True)


    @api.model
    def _prepare_picking_out(self):
        picking_type_id = self.picking_type_id
        print(picking_type_id)
        location = self.env.ref('stock.stock_location_customers')

        return {
            'picking_type_id': picking_type_id.id,
            'date_order': self.end_date,
            'origin': self.name,
            'location_dest_id': picking_type_id.default_location_dest_id.id or location.id,
            'location_id': picking_type_id.default_location_src_id.id,

            'state': 'assigned',
        }

    @api.model
    def _prepare_picking_in(self):
        picking_type_id = self.picking_type_id
        print(picking_type_id)
        location = self.env.ref('stock.stock_location_suppliers')

        return {
            'picking_type_id': picking_type_id.id,
            'date_order': self.end_date,
            'origin': self.name,
            'location_dest_id': picking_type_id.default_location_src_id.id,
            'location_id': location.id or picking_type_id.default_location_dest_id.id,
            # 'company_id': self.company_id.id,
            # 'maintenance_request_id': self.id,
            'state': 'assigned',
        }



    @api.multi
    def _create_picking_out(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            res_stock = order._prepare_picking_out()
            picking_stock = StockPicking.create(res_stock)
            print(picking_stock)
            moves_stock = order.spar_part_id._create_stock_moves(picking_stock)
            moves_stock = moves_stock.filtered(lambda x: x.state not in ('done', 'cancel'))
            seq = 0
            for move in sorted(moves_stock, key=lambda move: move.date_expected):
                seq += 5
                move.sequence = seq

            if picking_stock.move_lines:
                print(13 * '1')
                order.write({'picking_stock_out_id': picking_stock.id})
            else:
                picking_stock.unlink()
                print(13 * '2')

    @api.multi
    def _create_picking_in(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            res_stock = order._prepare_picking_in()
            picking_stock = StockPicking.create(res_stock)
            moves_stock = order._prepare_stock_moves_in(picking_stock)
            order.write({'picking_stock_in_id': picking_stock.id})


    @api.multi
    def _prepare_stock_moves_in(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        location = self.env.ref('stock.stock_location_suppliers')
        picking_type_id = self.picking_type_id
        res = []
        template = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': 1,
            'date': self.start_date,
            'date_expected': self.end_date,
            'location_dest_id':  location.id or picking_type_id.default_location_dest_id.id,
            'location_id': picking_type_id.default_location_src_id.id ,
            'picking_id': picking.id,
            'state': 'draft',
            'price_unit': self.product_id.standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.name,
            # 'warehouse_id': self.manufacturing_request_id.picking_type_id.warehouse_id.id,
            # 'account_analytic_id': self.account_analytic_id.id,
        }
        return self.env['stock.move'].create(template)


class SparManufacturing(models.Model):
    _name = 'spar.manufacturing'
    _rec_name = 'name'
    _description = ""

    name = fields.Char( string='Name')
    manufacturing_request_id = fields.Many2one('manufacturing.request', string='Maintenance Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', stirng='Service', required=True)
    description = fields.Char('Description', related='product_id.name')
    qty = fields.Float('Requested Qty', default=1)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    product_qty = fields.Float('Requested Qty')

    @api.onchange('product_id')
    def get_product_decription(self):
        if self.product_id:
            self.description = self.product_id.name
            self.product_uom_id = self.product_id.uom_id.id



    @api.multi
    def _create_stock_moves(self, picking_stock):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            print(line.product_id.name)
            print(30 * 'q')
            if picking_stock:
                val = line._prepare_stock_moves(picking_stock)

        return done

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        location = self.env.ref('stock.stock_location_customers')

        res = []
        template = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.product_qty,
            'date': self.manufacturing_request_id.start_date,
            'date_expected': self.manufacturing_request_id.end_date,
            'location_id': self.manufacturing_request_id.picking_type_id.default_location_src_id.id,
            'location_dest_id': self.manufacturing_request_id.picking_type_id.default_location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'price_unit': self.product_id.standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.manufacturing_request_id.name,
            'warehouse_id': self.manufacturing_request_id.picking_type_id.warehouse_id.id,
        }
        return self.env['stock.move'].create(template)
