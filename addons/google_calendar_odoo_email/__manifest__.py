# -*- coding: utf-8 -*-
{
    'name': 'Google Calendar - Forzar Correo de Odoo',
    'summary': 'Envía notificaciones de calendario por Odoo, no por Google',
    'description': """
        Cuando el módulo de Google Calendar está configurado, por defecto Google
        envía los correos de invitación/actualización a los asistentes.
        Este módulo cambia ese comportamiento para que Odoo sea siempre el
        responsable de enviar los correos, ignorando el sistema de notificaciones
        de Google Calendar.
    """,
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'author': 'Custom',
    'depends': ['google_calendar'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
