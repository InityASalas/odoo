import atexit
import logging
import re
import textwrap
import threading
from datetime import datetime
from pathlib import Path

from odoo.api import SUPERUSER_ID, Environment
from odoo.cli.command import Command
from odoo.modules.registry import Registry
from odoo.service.db import exp_drop, exp_duplicate_database
from odoo.tools import config

from odoo.addons import __path__ as addons_paths

_logger = logging.getLogger(__name__)


def get_tests_regex(tags):
    from odoo.tests.tag_selector import Info, TagsSelector  # noqa: PLC0415

    tag_selector = TagsSelector(tags)

    re_function = re.compile(r'\s*def (test_[^(]+)')
    re_class = re.compile(r'\s*class ([^(:]+)')
    re_tagged = re.compile(r'\s*@tagged\((.*)\)')

    for path in addons_paths:
        for testpath in Path(path).rglob("*/tests/test_*.py"):
            module = testpath.parent.parent.stem
            path = '.'.join(y.stem for y in (list(testpath.parents[:2][::-1])) + [testpath])
            with testpath.open('r') as testfile:
                tags, klass, method = None, None, None
                for line in testfile:
                    if match := re.match(re_tagged, line):
                        tags = {x.strip().strip("'") for x in match.group(1).split(',')}
                        tags |= {'standard', 'at_install'}
                        tags = sorted(tag for tag in tags if f'-{tag}' not in tags)
                    elif match := re.match(re_class, line):
                        klass = match.group(1)
                    elif match := re.match(re_function, line):
                        method = match.group(1)
                        info = Info(tags=tags, module=module, klass=klass, method=method, path=path)
                        if tag_selector._check(info) != False:  # noqa: E712
                            yield info


class Test(Command):
    """ Run selected tests """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser.add_argument(
            '-c', '--config', dest='config',
            help="use a specific configuration file")
        self.parser.add_argument(
            '-d', '--database', dest='db_name', default=None,
            help="database name, connection details will be taken from the config file")
        self.parser.add_argument(
            '-t', '--tempdb', dest='temp_db', action='store_true',
            help=textwrap.dedent("""\
                Create a temp db from the current one just for tests then drop it.
                Will be ignored if no test tagged `at-install` is selected.
            """))
        self.parser.add_argument(
            'tags', nargs='*', metavar='TAG',
            help=textwrap.dedent("""\
                List, or comma-separated list of filters to select tests to execute.

                format:  [-][tag][/module][:class][.method][[params]]

                -        blacklist matching tests instead of including them.
                tag      whitelist test classes with a matching `@tagged` decorator.
                         All Test classes have `standard` and `at_install` tags
                         until explicitly removed, see the decorator documentation.
                         '*' will match all tags.
                         Default is 'standard', or '*' if '-' is present.
                module   whitelist test classes from the matching module.
                class    whitelist matching test classes.
                method   whitelist matching test methods.
                params   pass these parameters to a test method that supports them.
                         If negated, the parameter will be passed over as negated.

                Parts of the filter are combined with the OR condition.
                Different filters are combined with the AND condition.

                `at-install` tests will be executed right after module installation.
                `post-install` tests will be executed after all modules are installed.

                Examples:
                $ odoo-bin test :TestClass.test_func /test_module external
                $ odoo-bin test -at_install,/account,/l10n_it,/l10n_it_edi
                $ odoo-bin test /web.test_js[mail]
            """))

    def run(self, cmdargs):
        parsed_args = self.parser.parse_args(args=cmdargs)

        config_args = ['--test-tags', ",".join(parsed_args.tags)]
        if parsed_args.config:
            config_args += ['-c', parsed_args.config]
        if parsed_args.db_name:
            config_args += ['-d', parsed_args.db_name]
        config.parse_config(config_args, setup_logging=True)

        db_names = config['db_name']
        if not db_names or len(db_names) > 1:
            self.parser.error("Please provide a single database in the config file")
        parsed_args.tags = config['test_tags']

        if parsed_args.temp_db:
            nowstr = datetime.now().strftime('%Y%m%d%H%M%S')
            tempdb = f"tempdb_{nowstr}"
            parsed_args.db_name = tempdb
            # Duplicate database
            exp_duplicate_database(db_names[0], tempdb)
            # Schedule for deletion
            atexit.register(exp_drop, tempdb)
        else:
            parsed_args.db_name = db_names[0]

        from odoo.tests import loader  # noqa: PLC0415

        all_modules = []
        at_install = []
        for info in get_tests_regex(parsed_args.tags):
            tags = info.tags or []
            if 'at_install' in tags:
                at_install.append(info.module)
            all_modules.append(info.module)

        config['init'] = config['update'] = at_install
        threading.current_thread().dbname = parsed_args.db_name
        Registry.new(  # registry =
            parsed_args.db_name,
            install_modules=all_modules,
            upgrade_modules=at_install,
        )
        _logger.info("Starting post tests")
        post_install_suite = loader.make_suite(all_modules, 'post_install')
        if post_install_suite.has_http_case():
            raise ValueError("Unsupported. Needs server to run.")
            # with registry.cursor():
            #     env = Environment(cr, SUPERUSER_ID, {})
            #     env['ir.qweb']._pregenerate_assets_bundles()

        loader.run_suite(post_install_suite)
