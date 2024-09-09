from odoo import _, fields, models,api

from odoo.exceptions import UserError,ValidationError


class HotelReservationExt(models.Model):

    _inherit = "hotel.reservation"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('checkedin', 'Checked In'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
    ], string='Status', readonly=True, default='draft', track_visibility='onchange')
    
    amenities = fields.One2many('hotel.housekeeping', 'service_id', string='Services Provided')

    def action_checkin(self):
        if self.state == 'confirm':
            self.write({'state': 'checkedin'})

    def action_checkout(self):
        if self.state == 'checkedin':
            # Schedule housekeeping on checkout
            housekeeping_vals = {
                'current_date': fields.Date.today(),
                'clean_type': 'checkout',
                'room_id': self.room_id.id,
                'inspector_id': self.env.user.id,  # Assuming the current user is the inspector
                'inspect_date_time': fields.Datetime.now(),
                'state': 'dirty',
            }
            self.env['hotel.housekeeping'].create(housekeeping_vals)

            # Change reservation state to done
            self.write({'state': 'done'})


# class SpecifiedRoomReserveList(models.Model):
#     _name = "hotel.specified.room.reservation"

#     room_id = fields.Text("Room")
#     date_from = fields.Datetime("Date From", default=lambda self: fields.Date.today())
#     date_to = fields.Datetime(
#     "Date To",
#     default=lambda self: fields.Date.today() + relativedelta(days=30),
#     )


#     @api.onchange("date_from", "date_to")
#     def reservation_listing(self):
#         room_obj = self.env["hotel.room"]  # Model for hotel room

#         room_reservation_lines = self.env['hotel.room.reservation.line'].search(
#         [
#             ("room_id", "=", room_id),  # Replace room_id with the actual room id
#             ("check_in", "<=", chk_date),
#             ("check_out", ">=", chk_date),
#         ]
#     )

