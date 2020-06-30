from odoo import fields, models, api


class WizFillHideMenus(models.TransientModel):
    _name = "wiz.fill.hide_menu"

    user_ids = fields.Many2many('res.users', string='Users', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)

    @api.multi
    def copy_users_menus(self):
        active_user_id = self._context.get("active_id")
        users = self.env['res.users'].search([])

        company = self.company_id.id
        menus = self.env['menu.line'].search([])
        menu_list = []
        for menu in menus:
            for user in menu.user_ids:
                if user.id in self.user_ids.mapped('id'):
                    menu_list.append(menu)

        menu_set = set(menu_list)
        menu_unique_list = list(menu_set)
        for rec in menu_unique_list:
            for user in self.user_ids:
                for men in user.hidden_menu_ids:
                    if men.company_id.id == self.company_id.id:
                        rec.write({'user_ids': [(4, active_user_id, 0)]})
                    else:
                        menu = self.env['menu.line'].search([('menu_id', '=', men.menu_id.id), ('company_id', '=', company)])
                        if len(menu) > 0:
                            menu[0].write({'user_ids': [(4, active_user_id, 0)]})
                        else:
                            self.env['menu.line'].create({
                                'menu_id': men.menu_id.id,
                                'user_ids': [(4, active_user_id, 0)],
                                'company_id': company,
                            })
