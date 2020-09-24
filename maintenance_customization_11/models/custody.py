from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class Equipments_model(models.Model):
    _inherit = 'hr.employee'
    _rec_name = "name"
    _description = ''

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env.ref('stock.stock_location_stock').id)
    # def _get_picking_type(self):
    #     company = self.env['res.company']._company_default_get('maintenance.request')
    #     pick_in = self.env['stock.picking.type'].search(
    #         [('warehouse_id.company_id', '=', company.id), ('code', '=', 'outgoing')], limit=1,
    #     )
    #     return pick_in[0]
    #
    # picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', default = _get_picking_type)
    #
    # @api.model
    # def _prepare_picking(self):
    #     picking_type_id = self.picking_type_id
    #     print(picking_type_id)
    #     location = self.env.ref('stock.stock_location_customers')
    #
    #     return {
    #         'picking_type_id': picking_type_id.id,
    #         'date_order': self.work_end_time,
    #         'origin': self.name,
    #         'location_dest_id': picking_type_id.default_location_dest_id.id or location.id,
    #         'location_id': picking_type_id.default_location_src_id.id,
    #         # 'company_id': self.company_id.id,
    #         'maintenance_request_id': self.id,
    #         'state': 'assigned',
    #     }
    #
    # @api.multi
    # def _create_picking(self):
    #     StockPicking = self.env['stock.picking']
    #     for order in self:
    #         res = order._prepare_picking()
    #         picking = StockPicking.create(res)
    #         print(picking)
    #         moves = order.spar_part_id._create_stock_moves(picking)
    #         moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))
    #         seq = 0
    #         for move in sorted(moves, key=lambda move: move.date_expected):
    #             seq += 5
    #             move.sequence = seq


class HrCustody(models.Model):
    _name = 'hr.custody'
    _description = "Employee Custody"
    _rec_name = 'employee'

    department = fields.Many2one('hr.department', string='Department', required='True')
    employee = fields.Many2one('hr.employee', string='Requested By', required='True')
    date = fields.Datetime(string='Date', default=str(datetime.now()), required='True')
    state = fields.Selection(
        [('draft', 'Draft'), ('supervisor', 'Supervisor'), ('manager', 'Manager'), ('engineer', 'Engineer'),
         ('supplier', 'Supplier'),('done', 'Confirm')] ,default='draft')
    spar_part_id = fields.One2many('spar.part.hr', 'custody_spar_part', string="Spar Part")

    @api.multi
    def button_draft_supervisor(self):
        if self.state == 'draft':
            self.state = 'supervisor'

    @api.multi
    def button_supervisor_manager(self):
        if self.state == 'supervisor':
            self.state = 'manager'

    @api.multi
    def button_manager_engineer(self):
        if self.state == 'manager':
            self.state = 'engineer'

    @api.multi
    def button_engineer_supplier(self):
        if self.state == 'engineer':
            self.state = 'supplier'

    @api.multi
    def button_suplier_done(self):
        if self.state == 'supplier':
            self.state = 'done'


class SparPartHr(models.Model):
    _name = 'spar.part.hr'
    _description = ""

    custody_spar_part = fields.Many2one('hr.custody', string='Custody Spar Part', ondelete='cascade')
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
            'date': date.today(),
            'date_expected': date.today(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            # 'company_id': self.request_id.company_id.id,
            'price_unit': self.product_id.standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.employee_spar_part.name,
            'warehouse_id': self.employee_spar_part.picking_type_id.warehouse_id.id,
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
