from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import except_orm, Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta


class EquipmentsContract(models.Model):
    _name = 'equipment.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _description = ''

    name = fields.Char(string='name', required=True)
    equipment = fields.Many2one('maintenance.equipment', string='Equipment',required='True')
    start_date = fields.Datetime(string='Start Date', default=str(datetime.now()), required='True')
    end_date = fields.Datetime(string='Start Date', default=str(datetime.now()), required='True')
    state = fields.Selection(
        [('draft', 'Draft'), ('valid', 'Valid'), ('expired', 'Expired')],
        string="State",
        default="draft")
    note = fields.Text('Internal Note')
    # location = fields.Selection(
    #     [('draft', 'Draft'), ('valid', 'Valid')],
    #     string="State",
    #     default="draft")

    @api.multi
    def button_state(self):
        if self.state=='draft':
            self.state='valid'
        elif self.state=='valid':
            self.state = 'expired'

    @api.model
    def equipment_contract_schedule_action(self):
        print(10 * '89')
        contract_object = self.env['equipment.contract'].search([('state','=','valid')])
        for record in contract_object:
           if record.end_date == record.start_date:
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
                       'res_model_id': record.env['ir.model'].sudo().search([('model', 'like', 'equipment.contract')], limit=1).id,
                       'user_id': fm[0] or 1,
                       'summary': " The Contarct of  "+record.equipment.name + ' has been exiperd'
                    }
                    self.activity_id = self.env['mail.activity'].sudo().create(vals)

                    print("000000000000000000000000", self.activity_id)
               record.state='expired'


