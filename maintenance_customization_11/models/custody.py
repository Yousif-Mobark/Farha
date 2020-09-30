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



class CustodyClearnce(models.Model):
    _name = 'custody.clearance'
    _description = "Custody Clearance"
    _rec_name = 'employee'

    department = fields.Many2one('hr.department', string='Department',related='employee.department_id' ,required='True')
    employee = fields.Many2one('hr.employee', string='Employee', required='True')
    date = fields.Datetime(string='Date', default=str(datetime.now()), required='True')
    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Canceled'), ('confirm', 'In Progress'), ('done', 'Validated')], default='draft')
    spar_part_id = fields.One2many('spar.part.clearance', 'custody_spar_part', string="Spar Part")
    # exhausted = fields.Boolean('Include Exhausted Products', readonly=True, states={'draft': [('readonly', False)]})
    filter = fields.Selection([('none', 'All products'), ('partial', 'Select products manually')], defaut='non' ,required=True, )
    stock_picking = fields.Many2one('stock.picking', string='Stock Picking')


    @api.multi
    def button_start_inventory(self):
        if self.state == 'draft' and self.filter == 'none':
            self.action_start()
            self.state = 'confirm'
        elif self.state == 'draft':
            self.state = 'confirm'

    @api.multi
    def button_validate_inventory(self):
        if self.state == 'confirm' and self.spar_part_id:
            self._create_picking()
            self.state = 'done'
        else:
            raise UserError(_("You must select item(s) to validate Inventory"))


    @api.multi
    def action_cancel_draft(self):
        self.write({'state': 'draft'})





    def _get_picking_type(self):
        company = self.env['res.company']._company_default_get('maintenance.request')
        pick_in = self.env['stock.picking.type'].search(
            [('warehouse_id.company_id', '=', company.id), ('code', '=', 'outgoing')], limit=1,
        )
        return pick_in[0]

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', default=_get_picking_type)

    @api.model
    def _prepare_picking(self):
        picking_type_id = self.picking_type_id
        print(picking_type_id)
        location = self.env.ref('stock.stock_location_customers')

        return {
            'picking_type_id': picking_type_id.id,
            'date_order': self.date,
            'origin': self.employee.name + ' ' + "Custody",
            'location_dest_id':  picking_type_id.default_location_dest_id.id,
            'location_id': self.employee.location_id.id or picking_type_id.default_location_src_id.id,
            # 'company_id': self.company_id.id,
            'maintenance_request_id': self.id,
            'state': 'assigned',
        }

    @api.multi
    def _create_picking(self):
        print(50*'m')
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
            order.write({'stock_picking': picking.id})

    def action_start(self):
        for inventory in self.filtered(lambda x: x.state not in ('done')):
            vals = {}
            if not self.spar_part_id:
                vals.update(
                    {'spar_part_id': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
            inventory.write(vals)
        return True

    def _get_inventory_lines_values(self):
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'child_of', [self.employee.location_id.id])])
        domain = ' location_id in %s AND quantity != 0 AND active = TRUE'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']


        self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
            FROM stock_quant
            LEFT JOIN product_product
            ON product_product.id = stock_quant.product_id
            WHERE %s
            GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            print(100 * '3')

            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        # if self.exhausted:
        #     exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
        #     vals.extend(exhausted_vals)
        print(vals)
        return vals


class SparPartClearance(models.Model):
    _name = 'spar.part.clearance'
    _description = ""

    custody_spar_part = fields.Many2one('custody.clearance', string='Custody Spar Part', ondelete='cascade')
    product_id = fields.Many2one('product.product', stirng='Service', required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',)
    description = fields.Char('Description', related="product_id.name")
    product_qty = fields.Float('Requested Qty')
    location_id = fields.Many2one('stock.location', 'Inventoried Location',)

    @api.onchange('product_id')
    def get_product_decription(self):
        if self.product_id:
            self.description = self.product_id.name

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
            'product_uom_qty': self.product_qty,
            'date': date.today(),
            'date_expected': date.today(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            # 'company_id': self.request_id.company_id.id,
            'price_unit': self.product_id.standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.custody_spar_part.employee.name + ' ' + "Custody",
            'warehouse_id': self.custody_spar_part.picking_type_id.warehouse_id.id,
            'quantity_done': self.product_qty,
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
