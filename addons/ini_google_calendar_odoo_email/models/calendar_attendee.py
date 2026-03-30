# -*- coding: utf-8 -*-
from odoo import models
from odoo.addons.calendar.models.calendar_attendee import Attendee as BaseCalendarAttendee


class Attendee(models.Model):
    _name = 'calendar.attendee'
    _inherit = 'calendar.attendee'

    def _send_mail_to_attendees(self, mail_template, force_send=False):
        """Override: siempre enviar correos desde Odoo.

        El módulo google_calendar suprime el envío de Odoo cuando hay token de
        Google activo (asumiendo que Google enviará los correos). Este override
        ignora esa lógica y siempre usa el sistema de correo de Odoo,
        independientemente de si Google Calendar está sincronizado o no.
        """
        BaseCalendarAttendee._send_mail_to_attendees(self, mail_template, force_send)
