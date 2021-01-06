from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class EquipmentsContract(models.Model):
    _name = 'equipment.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "partner_id"
    _description = ''

    # name = fields.Char(string='name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    equipment = fields.One2many('equipment.equipment', 'equipment_contract_id' , string='Equipment')
    start_date = fields.Datetime(string='Start Date', default=lambda a:str(datetime.now()), required='True')
    end_date = fields.Datetime(string='End Date',default=lambda a:str(datetime.now()), required='True')
    state = fields.Selection(
        [('draft', 'Draft'), ('valid', 'Valid'), ('expired', 'Expired')],
        string="State",
        default="draft")
    note = fields.Text('Internal Note')
    cost = fields.Float(string="Contract Total Amount")
    invoice_count = fields.Integer(compute='_invoice_count', string='# Invoice', copy=False)
    spar_state = fields.Selection(
        [('no', 'No'), ('yes', 'Yes')],
        string="Spar Included",
        default="no")
    living_state = fields.Selection([('no', 'No'), ('yes', 'Yes')],string="Living Included",default="no")
    living_cost = fields.Float(string="Living Cost")
    equipment_number = fields.Integer(string="Equipment Number",compute='_get_equipment_number' ,store=True)


    @api.one
    @api.depends('equipment')
    def _get_equipment_number(self):
        total = 0
        for rec in self.equipment:
            print(self.equipment)
            total += len(rec.equipment)
        self.equipment_number = total

    @api.multi
    def _invoice_count(self):
        invoice_ids = self.env['account.invoice'].search([('contract_id', '=', self.id)])
        self.invoice_count = len(invoice_ids)

    @api.multi
    def action_view_invoice(self):
        inv_obj = self.env['account.invoice'].search(
            [('contract_id', '=', self.id), ('type', '=', 'out_invoice')])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
        view_id = self.env.ref('account.invoice_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids and inv_ids[0]
                }

                return value
            else:
                if len(inv_ids) > 1:
                    action['domain'] = [('id', 'in', inv_ids)]
                return action

    @api.multi
    def button_state(self):
        if self.state == 'draft':
            self.state = 'valid'
        elif self.state == 'valid':
            self.state = 'expired'
        elif self.state == 'expired':
            self.state = 'draft'



    @api.multi
    def create_invoice(self):
        account_created = self.env['account.invoice']
        today_time = datetime.strptime(str(datetime.today()), '%Y-%m-%d %H:%M:%S.%f')
        account_object_vals = {
            'partner_id': self.partner_id.id,
            'contract_id': self.id,
            'date_invoice': str(today_time),
            'account_id': self.partner_id.property_account_receivable_id.id,
            'state': 'draft',
            'quantity': 1,
            'journal_id': 1,
            'currency_id': self.partner_id.company_id.currency_id.id,

        }
        account_created = account_created.create(account_object_vals)
        try:
            product_id = self.env.ref('maintenance_customization_11.contract_fee_product_product')
        except:
            raise UserError("you have delete configuration product ; please upgrade Maintenance module.")
        account_line_object1 = self.env['account.invoice.line']
        if not product_id.property_account_income_id :
            raise UserError("please Specify Income account for "+product_id.name)
        account_line_vals1 = {
            'product_id': product_id.id,
            'name': 'Contract Fees',
            'price_unit': self.cost,
            'invoice_id': account_created.id,
            'account_id': product_id.property_account_income_id.id,
            'quantity': 1,

        }

        account_line_object1.create(account_line_vals1)

        self.inv_generated = True

    @api.model
    def equipment_contract_schedule_action(self):
        contract_object = self.env['equipment.contract'].search([('state', '=', 'valid')])
        for record in contract_object:
            if record.end_date == datetime.today():
                group_manager = self.env.ref('hr.group_hr_manager').id

                # first of all get users
                record.env.cr.execute(
                    '''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (group_manager))
                print("ppppppppppppppppp", group_manager)
                for fm in list(filter(lambda x: (
                        record.env['res.users'].sudo().search([('id', '=', x)])), record.env.cr.fetchall())):
                    print("lllllllllllll", fm)
                    vals = {
                        'activity_type_id': record.env['mail.activity.type'].sudo().search([],
                                                                                           limit=1).id,
                        'res_id': record.id,
                        'res_model_id': record.env['ir.model'].sudo().search([('model', 'like', 'equipment.contract')],
                                                                             limit=1).id,
                        'user_id': fm[0] or 1,
                        'summary': " The Contarct of  " + record.equipment.name + ' has been exiperd'
                    }
                    self.env['mail.activity'].sudo().create(vals)

                record.state = 'expired'


class Spar_part(models.Model):
    _name = 'equipment.equipment'
    _description = ""

    equipment_contract_id = fields.Many2one('equipment.contract', string='Equipment contract', ondelete='cascade')
    equipment = fields.Many2one('maintenance.equipment',  string='Equipment', required='True')
    name = fields.Char('Description', related='equipment.name')
    location = fields.Selection(
        [('inkhartoum', 'Khartoum'), ('outkhartoum', 'Out Khartoum')], string="Location", related='equipment.location')

    # @api.multi
    # @api.onchange('equipment')
    # def set_contract_id(self):
    #     id = self.env.ref(self.equipment_contract_id.id)
    #     if self.equipment_contract_id.id:
    #         print(self.equipment_contract_id.id, )
    #         self._cr.execute(
    #             "update maintenance_equipment set contract_id =%s   where id = %s",
    #             (self.equipment_contract_id.id, self.equipment.id))
    #         print(self.equipment.contract_id.id)


class CustomerInvoice(models.Model):
    _inherit = 'account.invoice'

    contract_id = fields.Char('Contract No.', help='Auto-generated Contract No')
