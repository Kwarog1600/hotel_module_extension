from odoo import _, fields, models,api
from dateutil.relativedelta import relativedelta
from datetime import timedelta

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
        for reservation_line in self.reservation_line:
            # Iterate through the rooms in the reservation line
            for room in reservation_line.reserve:
                # Schedule housekeeping on checkout
                housekeeping_vals = {
                    'current_date': fields.Date.today(),
                    'clean_type': 'checkout',
                    'room_id': room.id,  # Use room.id to reference the room record
                    'inspector_id': self.env.user.id,  # Assuming the current user is the inspector
                    'inspect_date_time': fields.Datetime.now(),
                    'state': 'dirty',
                }
                self.env['hotel.housekeeping'].create(housekeeping_vals)

        # Change reservation state to done
        self.write({'state': 'done'})

class SpecifiedRoomReserveList(models.Model):
    _name = "hotel.specified.room.reservation"

    date_from = fields.Datetime("Date From", default=lambda self: fields.Datetime.now())
    date_to = fields.Datetime(
        "Date To",
        default=lambda self: fields.Datetime.now() + relativedelta(days=30),
    )

    reservation_listing_result = fields.One2many(
        "hotel.reservation.listing.line", "reservation_list_id", string="Reservations"
    )

    @api.onchange("date_from", "date_to")
    def reservation_listing(self):
        
        if self.date_from and self.date_to:
            chk_date_from = self.date_from
            chk_date_to = self.date_to

            room_ids = self.env['hotel.room'].search([])

            room_ids = self.env['hotel.reservation'].search(
                [('checkin', '>=', chk_date_from),
                 ('checkout', '<=', chk_date_to),
                 ('room_reservation_line.reserve', room_ids)])

            room_reservation_lines = self.env['hotel.room.reservation.line'].search(
                [
                    ("check_in", "<=", chk_date_to),
                    ("check_out", ">=", chk_date_from),
                    ("room_id", "=", room_id),
                ]
            )

            # Clear existing results
            reservation_lines = []

            # Generate all dates in the given range
            current_date = chk_date_from
            while current_date <= chk_date_to:
                state = 'free'  # Default state is 'free'
                
                # Check if the current date falls within any reservation
                for reservation_line in room_reservation_lines:
                    if reservation_line.check_in <= current_date <= reservation_line.check_out:
                        if reservation_line.resevation_id.state == 'draft':
                            state = reservation_line.reservation_id.state 
                            break
                        elif reservation_line.reservation_id.state == 'confirm':
                            state = 'reserved'
                            break

                reservation_lines.append((0, 0, {
                    'room_name': reservation_line.room_id,  # Assuming room_id has a name field
                    'customer_name': reservation_line.reservation_id.partner_id.name if state != 'free' else '',
                    'check_in': current_date,
                    'check_out': current_date,  # Using the same date for single day
                    'state': state,
                }))
                
                # Move to the next date
                current_date += timedelta(days=1)

            # Update One2many field with reservation lines or free slots
            self.reservation_listing_result = reservation_lines

class ReservationListingLine(models.Model):
    _name = "hotel.reservation.listing.line"
    _description = "Reservation Listing Line"

    room_id = fields.Char("Room")
    date = fields.Datetime("Check-In")
    state = fields.Selection(
        [
            ('free', 'Free'),
            ('confirmed', 'Confirmed'),
            ('reserved', 'Reserved'),
            ('unavailable', 'Unavailable'),
        ],
        string="State",
    )
    reservation_list_id = fields.Many2one(
        "hotel.specified.room.reservation", string="Reservation List"
    )
