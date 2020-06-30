# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    hidden_menu_ids = fields.Many2many('menu.line', 'hide_menu_user_rel', 'user_id', 'menu_line_id')

    # Earlier Needs to restart server to take invisible effect 
    # After User Request added clear cache code so no need to restart server
    @api.model
    def create(self, values):
        self.env['ir.ui.menu'].clear_caches()
        return super(ResUsers, self).create(values)

    def write(self, values):
        self.env['ir.ui.menu'].clear_caches()
        return super(ResUsers, self).write(values)

class res_company(models.Model):
    _inherit = 'res.company'

    menu_lines = fields.One2many('menu.line', 'company_id', 'Menu lines')


class menu_line(models.Model):
    _name = 'menu.line'
    _description = 'Menu Line'
    _rec_name = 'menu_id'

    menu_id = fields.Many2one('ir.ui.menu', string='Menu To Hide', required=True)
    user_ids = fields.Many2many('res.users', 'hide_menu_user_rel', 'menu_line_id', 'user_id', string='User', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ids = super(IrUiMenu, self).search(args, offset=0, limit=None, order=order, count=False)
        ids_list = [rec.id for rec in ids]
        user = self.env['res.users'].browse(self._uid)
        self._cr.execute("""SELECT l.menu_id FROM menu_line l WHERE
                        l.id IN(SELECT r.menu_line_id FROM  hide_menu_user_rel r WHERE r.user_id = %d)
                        AND l.company_id = %d""" % (self._uid, user.company_id.id))

        for menu_id in self._cr.fetchall():
            if menu_id[0] in ids_list:
                ids_list.remove(menu_id[0])
        ids = self.env['ir.ui.menu'].browse(ids_list)
        if offset:
            ids = ids[offset:]
        if limit:
            ids = ids[:limit]
        return len(ids) if count else ids
