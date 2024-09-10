from odoo import _, fields, models,api
from odoo.exceptions import ValidationError


class HotelHousekeeping(models.Model):

    _inherit = "hotel.housekeeping"

    state = fields.Selection(selection_add=[('repair', 'Under Repair')],
                             ondelete={'repair': 'set default'})
    service_id = fields.Many2one('hotel.reservation', string='Service Reference')