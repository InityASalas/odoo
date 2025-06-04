# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tools.misc import str2bool

from . import const
from . import controllers
from . import models
from . import report
from . import wizard


def _post_init_hook(env):
    _synchronize_crons(env)


def _synchronize_crons(env):
    for param, cron_xmlid in const.PARAM_CRON_MAPPING.items():
        if cron := env.ref(cron_xmlid, raise_if_not_found=False):
            cron.active = str2bool(env['ir.config_parameter'].get_param(param, 'False'))
