# -*- coding: utf-8 -*-
import json
import logging
from requests import HTTPError

from odoo import models
from odoo.addons.google_account.models.google_service import TIMEOUT
from odoo.addons.google_calendar.models.google_sync import (
    after_commit,
    google_calendar_token,
)

_logger = logging.getLogger(__name__)


class GoogleSync(models.AbstractModel):
    _inherit = 'google.calendar.sync'

    def _google_insert(self, google_service, values, timeout=TIMEOUT):
        """Override: forzar sendUpdates=none para que Google no envíe correos.

        En el original, send_updates=True por defecto, lo que hace que Google
        envíe notificaciones a los asistentes. Aquí lo forzamos a False para
        que solo Odoo sea el responsable de enviar correos.
        """
        return super(
            GoogleSync, self.with_context(send_updates=False)
        )._google_insert(google_service, values, timeout=timeout)

    @after_commit
    def _google_patch(self, google_service, google_id, values, timeout=TIMEOUT):
        """Override: usar sendUpdates=none en actualizaciones de eventos."""
        with google_calendar_token(self.env.user.sudo()) as token:
            if token:
                try:
                    url = "/calendar/v3/calendars/primary/events/%s?sendUpdates=none" % google_id
                    headers = {
                        'Content-type': 'application/json',
                        'Authorization': 'Bearer %s' % token,
                    }
                    google_service.google_service._do_request(
                        url, json.dumps(values), headers, method='PATCH', timeout=timeout
                    )
                except HTTPError as e:
                    if e.response.status_code in (400, 403):
                        self._google_error_handling(e)
                if values:
                    self.exists().with_context(dont_notify=True).need_sync = False

    @after_commit
    def _google_delete(self, google_service, google_id, timeout=TIMEOUT):
        """Override: usar sendUpdates=none en eliminaciones de eventos."""
        with google_calendar_token(self.env.user.sudo()) as token:
            if token:
                is_recurrence = self._context.get('is_recurrence', False)
                google_service.google_service = google_service.google_service.with_context(
                    is_recurrence=is_recurrence
                )
                url = "/calendar/v3/calendars/primary/events/%s?sendUpdates=none" % google_id
                headers = {'Content-type': 'application/json'}
                params = {'access_token': token}
                if google_service.google_service._context.get('is_recurrence', True):
                    params['singleEvents'] = 'true'
                try:
                    google_service.google_service._do_request(
                        url, params, headers=headers, method='DELETE', timeout=timeout
                    )
                except HTTPError as e:
                    if e.response.status_code not in (410, 403):
                        raise e
                    _logger.info("Google event %s was already deleted", google_id)
                self.exists().with_context(dont_notify=True).need_sync = False
