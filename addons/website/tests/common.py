# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import contextlib
from unittest.mock import MagicMock, Mock, patch

import werkzeug.urls
from werkzeug.exceptions import NotFound
from werkzeug.test import EnvironBuilder

import odoo.http
from odoo.fields import Command
from odoo.tests import HOST, HttpCase
from odoo.tools import file_open
from odoo.tools.misc import DotDict, frozendict


@contextlib.contextmanager
def MockRequest(
    env, *, path='/mockrequest', routing=True, multilang=True,
    context=frozendict(), cookies=frozendict(), country_code=None,
    website=None, remote_addr=HOST, environ_base=None, url_root=None,
):
    from odoo.tests.common import HttpCase  # noqa: PLC0415
    lang_code = context.get('lang', env.context.get('lang', 'en_US'))
    env = env(context=dict(context, lang=lang_code))
    if HttpCase.http_port():
        base_url = HttpCase.base_url()
    else:
        base_url = f"http://{HOST}:{odoo.tools.config['http_port']}"
    request = Mock(
        # request
        httprequest=Mock(
            host='localhost',
            path=path,
            app=odoo.http.root,
            environ=dict(
                EnvironBuilder(
                    path=path,
                    base_url=base_url,
                    environ_base=environ_base,
                ).get_environ(),
                REMOTE_ADDR=remote_addr,
            ),
            cookies=cookies,
            referrer='',
            remote_addr=remote_addr,
            url_root=url_root,
            args=[],
        ),
        type='http',
        future_response=odoo.http.FutureResponse(),
        params={},
        redirect=env['ir.http']._redirect,
        session=DotDict(
            odoo.http.get_default_session(),
            context={'lang': ''},
            force_website_id=website and website.id,
        ),
        geoip=odoo.http.GeoIP('127.0.0.1'),
        db=env.registry.db_name,
        env=env,
        registry=env.registry,
        cr=env.cr,
        uid=env.uid,
        context=env.context,
        cookies=cookies,
        lang=env['res.lang']._get_data(code=lang_code),
        website=website,
        render=lambda *a, **kw: '<MockResponse>',
    )
    if url_root is not None:
        request.httprequest.url = werkzeug.urls.url_join(url_root, path)
    if website:
        request.website_routing = website.id
    if country_code:
        try:
            request.geoip._city_record = odoo.http.geoip2.models.City(['en'], country={'iso_code': country_code})
        except TypeError:
            request.geoip._city_record = odoo.http.geoip2.models.City({'country': {'iso_code': country_code}})

    # The following code mocks match() to return a fake rule with a fake
    # 'routing' attribute (routing=True) or to raise a NotFound
    # exception (routing=False).
    #
    #   router = odoo.http.root.get_db_router()
    #   rule, args = router.bind(...).match(path)
    #   # arg routing is True => rule.endpoint.routing == {...}
    #   # arg routing is False => NotFound exception
    router = MagicMock()
    match = router.return_value.bind.return_value.match
    if routing:
        match.return_value[0].routing = {
            'type': 'http',
            'website': True,
            'multilang': multilang
        }
    else:
        match.side_effect = NotFound

    def update_context(**overrides):
        request.env = request.env(context=dict(request.context, **overrides))
        request.context = request.env.context

    request.update_context = update_context

    with contextlib.ExitStack() as s:
        odoo.http._request_stack.push(request)
        s.callback(odoo.http._request_stack.pop)
        s.enter_context(patch('odoo.http.root.get_db_router', router))

        yield request


class HttpCaseWithWebsiteUser(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")
        country = cls.env.ref("base.us")
        state = cls.env["res.country.state"].search([("code", "=", "NY")], limit=1)
        partner_vals = {
            "name": "Rafe Restricted",
            "company_id": company.id,
            "company_name": "YourCompany",
            "street": "725 5th Ave",
            "city": "New York",
            "state_id": state.id if state else False,
            "zip": "10022",
            "country_id": country.id,
            "tz": "America/New_York",
            "email": "rafe.cameron23@example.com",
            "phone": "+1(492)-563-3759",
        }
        cls.partner_website_user = cls.env["res.partner"].create(partner_vals)
        cls.user_website_user = cls.env["res.users"].create({
            "partner_id": cls.partner_website_user.id,
            "login": "website_user",
            "password": "website_user",
            "signature": "<span>-- <br/>+Mr Restricted</span>",
            "company_id": company.id,
            "image_1920": base64.b64encode(file_open("website/static/src/img/user-restricted-image.png", "rb").read()),
            "group_ids": [
                Command.unlink(cls.env.ref("website.group_website_designer").id),
                Command.link(cls.env.ref("website.group_website_restricted_editor").id),
                Command.link(cls.env.ref("base.group_user").id),
            ],
        })
