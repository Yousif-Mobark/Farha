from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class MaintenanceRequests(models.Model):
    _inherit = 'maintenance.request'
    _description = 'Maintenance Management'

    call_date = fields.Datetime(string="Call Received Date", required=True, default=str(datetime.now()))
    category = fields.Many2one('maintenance.equipment.category', string='Equipment Category')
    bank_name = fields.Many2one('res.partner', string="Bank Name")
    location = fields.Many2one('equipments.location',string="Location")
    city = fields.Many2one('equipments.city',string="City")
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
    work_end_time = fields.Datetime(help="End time of work", states={'engineer': [('required', True)]})
    model = fields.Many2one('equipments.model', string="Model" )
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', required = True,
                                   ondelete='restrict', index=True ,domain="[('model','=',model)]")
    spar_part_id = fields.One2many('spar.part', 'maintenance_request_id', string="Spar Part")
    fault = fields.Text(string='Fault')
    cuase = fields.Text(string='Cuase')
    action = fields.Text(string="Action")
    comment = fields.Text(string="comment")
    picking_from_stock_id = fields.Many2one('stock.picking', string='Stock Picking')
    picking_from_technician_id = fields.Many2one('stock.picking', string='Stock technician')
    sale_order_id = fields.Many2one('sale.order', string='Sale Oredr')
    electricity = fields.Boolean(string='Electricity')
    air_condition = fields.Boolean(string='Air Condition')
    site_condition = fields.Boolean(string='Sit Condition')
    money = fields.Boolean(string='Amount of Money')
    electricity1 = fields.Char(string='Electricity')
    air_condition1 = fields.Char(string='Air Condition')
    site_condition1 = fields.Char(string='Sit Condition')
    money1 = fields.Char(string='Amount of Money')
    call_type = fields.Selection([('call','Call'),('pm','PM'),
                                  ('install','Installation'),('assist','Assistance')],default='call')

    @api.onchange('category',"bank_name",'model','location')
    def _onchange_category(self):
        domain=[]
        self.equipment_id=False
        if self.category:
            domain.append(('category_id', '=', self.category.id))
        if self.bank_name:
            domain.append(('partner_id', '=', self.bank_name.id))
        if self.model:
            domain.append(('model', '=', self.model.id))
        if self.location:
            domain.append(('location1', '=', self.location.id))
        domain = {'equipment_id': domain}
        return {'domain': domain}

    @api.onchange('equipment_id')
    def _onchange_equipment(self):
        if self.equipment_id:
            self.category=self.equipment_id.category_id
            self.bank_name=self.equipment_id.partner_id
            self.model=self.equipment_id.model
            self.location=self.equipment_id.location1
            self.city = self.equipment_id.city


    @api.constrains('work_start_time', 'work_end_time')
    def end_date_constrain(self):
        if self.work_start_time and self.work_end_time:
            if self.work_start_time > self.work_end_time:
                raise UserError(_("Work start Date must be greater the work end date"))

    @api.multi
    @api.onchange('work_start_time', 'work_end_time')
    def _compute_consumed_time(self):
        for record in self:
            if record.work_start_time and record.work_end_time:
                work_end_time = datetime.strptime(record.work_start_time, '%Y-%m-%d %H:%M:%S')
                work_start_time = datetime.strptime(record.work_end_time, '%Y-%m-%d %H:%M:%S')
                day = (work_start_time - work_end_time).days
                hour = (work_start_time - work_end_time).seconds//3600
                minute = ((work_start_time - work_end_time).seconds%3600)//60
                self.consumed_time = str(day)+" "+ str(hour)+':'+str(minute)

    @api.model
    def equipment_warranty(self):
        # contract_object = self.env['equipment.contract'].search([('state', '=', 'valid')])
        if self.status == 'warranty':
            self.equipment_id.write({
                'warranty_start' : self.work_end_time,
                'has_warranty': 'yes',
                'state': 'inprogress'
            })
            group_manager = self.env.ref('hr.group_hr_manager').id
            # first of all get users
            self.env.cr.execute(
                '''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (group_manager))
            for fm in list(filter(lambda x: (
                    self.env['res.users'].sudo().search([('id', '=', x)])), self.env.cr.fetchall())):
                vals = {
                    'activity_type_id': self.env['mail.activity.type'].sudo().search([],
                                                                                     limit=1).id,
                    'res_id': self.equipment_id.id,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'maintenance.equipment')],
                        limit=1).id,
                    'user_id': fm[0] or 1,
                    'summary': " The Contract of  " + self.equipment_id.name + ' has been new warranty'
                }
                self.env['mail.activity'].sudo().create(vals)



    @api.multi
    def button_stock_picking(self):
        if self.spar_part_id:
            self._create_picking()
        if self.state == 'engineer':
            self.equipment_warranty()
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
                order.write({'picking_from_stock_id': picking_stock.id})
            else:
                picking_stock.unlink()
            if picking_technician.move_lines:
                order.write({'picking_from_technician_id': picking_technician.id})
            else:
                picking_technician.unlink()

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
            if not order.sale_order_id.order_line :
                order.sale_order_id.unlink()


class Spar_part(models.Model):
    _name = 'spar.part'
    _description = "Maintenance Spare"

    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', stirng='Service', required=True)
    description = fields.Char('Description', related='product_id.name')
    qty = fields.Float('Requested Qty', default=1)
    spar_source = fields.Selection([('technician', 'Technician')],default='technician')
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
        #     if rec.spar_source == 'stock' and rec.warranty == False:
        #         rec.location_id = rec.maintenance_request_id.picking_type_id.default_location_src_id.id \
        #                           or location.id,
        #         rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id.id or location.id
        #     elif rec.spar_source == 'technician' and rec.warranty == False:
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
            'price_unit': self.product_id.standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.maintenance_request_id.name,
            'warehouse_id': self.maintenance_request_id.picking_type_id.warehouse_id.id,
            'quantity_done': self.qty,
        }
        return self.env['stock.move'].create(template)

    @api.multi
    def _create_stock_moves(self, picking_stock, picking_technicain):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self.filtered(lambda x: x):
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
            # if rec.spar_source == 'stock':
            #     rec.location_id = rec.maintenance_request_id.picking_type_id.default_location_src_id.id \
            #                       or location.id,
            #     rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id.id or location.id
            # elif rec.spar_source == 'technician':
            rec.location_id = rec.maintenance_request_id.employee_id.location_id.id or location.id
            rec.location_dest_id = rec.maintenance_request_id.picking_type_id.default_location_dest_id.id or location.id

        res = []



class Equipments_model(models.Model):
    _name = 'equipments.model'
    _rec_name = "name"
    _description = 'Equipments Model'

    name = fields.Char(string="Name" ,required=True)
    code = fields.Char(string="code" , required=True)

class Equipments_city(models.Model):
    _name = 'equipments.city'
    _rec_name = "name"
    _description = 'Equipments city'

    name = fields.Char(string="Name" , required=True)
    code = fields.Char(string="code" , required=True)

    locations = fields.One2many("equipments.location","city")

class Equipments_loction(models.Model):
    _name = 'equipments.location'
    _rec_name = "name"
    _description = 'Equipments location'

    name = fields.Char(string="Name" , required=True)
    code = fields.Char(string="code" , required=True)
    city = fields.Many2one('equipments.city',string='City')



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale order line Model'

    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Source Location')


class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'

    # @api.model
    # def create(self, vals):
    #     result = super(StockMove, self).create(vals)
    #     if result.sale_line_id:
    #          result.location_id = result.sale_line_id.location_id
    #          result.location_dest_id = result.location_dest_id
    #
    #     return result


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'


    contract_id = fields.Many2one('equipment.contract', string='Contract')
    state = fields.Selection(
        [('draft', 'Draft'), ('inprogress', 'In progress'), ('done', 'Done')],
        string="State",
        default="draft")
    location = fields.Selection(
        [('inkhartoum', 'Khartoum'), ('outkhartoum', 'Out Khartoum')], string="Location", default="inkhartoum")
    location1 = fields.Many2one('equipments.location', string="Location")

    has_warranty = fields.Selection([('no', 'No'), ('yes', 'Yes')], string="Has Warranty", default="no")
    warranty_start = fields.Datetime(string='Warranty Start Date')
    warranty_end = fields.Datetime(string='Warranty end Date')
    model = fields.Many2one('equipments.model', string="Model", )
    partner_id = fields.Many2one('res.partner', string='Bank Name', domain="[('supplier', '=', 1)]")
    city= fields.Many2one('equipments.city')

    @api.multi
    def button_state(self):
        if self.state == 'draft':
            print(10 * "butom")
            if self.has_warranty == 'yes':
                group_manager = self.env.ref('hr.group_hr_manager').id

                # first of all get users
                self.env.cr.execute(
                    '''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (group_manager))
                print("ppppppppppppppppp", group_manager)
                for fm in list(filter(lambda x: (
                        self.env['res.users'].sudo().search([('id', '=', x)])), self.env.cr.fetchall())):
                    print("lllllllllllll", fm)
                    vals = {
                        'activity_type_id': self.env['mail.activity.type'].sudo().search([],
                                                                                         limit=1).id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model'].sudo().search(
                            [('model', '=', 'maintenance.equipment')],
                            limit=1).id,
                        'user_id': fm[0] or 1,
                        'summary': " The Contarct of  " + self.name + ' has been new warranty'
                    }
                    self.env['mail.activity'].sudo().create(vals)
                self.state = 'inprogress'

            elif self.state == 'inprogress':
                 self.state = 'done'

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    type  = fields.Selection(
        [('maintenance', 'Maintenance'), ('custody', 'Custody'), ('Manufacturing', 'manufacturing')],
        string="Type",)

class Respartner(models.Model):
    _inherit="res.partner"

    is_bank= fields.Boolean()