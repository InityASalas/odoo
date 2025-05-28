import logging
import re

from odoo.tools.misc import OrderedSet

_logger = logging.getLogger(__name__)


class Info:
    def __init__(self, tags=None, module=None, klass=None, method=None, path=None):
        self.tags = tags
        self.module = module
        self.klass = klass
        self.method = method
        self.path = str(path) if path else None
        if self.path:
            self.path = self.path.replace('.', '/')
            if not self.path.endswith('.py'):
                self.path += '.py'
            for prefix in ('odoo.addons', 'odoo.upgrade'):
                self.path = self.path.removeprefix(prefix)

    def match(self, test):
        no_tag_match = self.tags and test.tags and self.tags not in test.tags
        no_file_match = self.path and test.path and not self.path.endswith(test.path)
        no_module_match = not self.path and test.module and self.module and self.module != test.module
        no_class_match = self.klass and self.klass != test.klass
        no_method_match = self.method and self.method != test.method
        return not (
            no_tag_match
            or no_file_match
            or no_module_match
            or no_class_match
            or no_method_match
        )


class TagsSelector:
    """ Test selector based on tags. """

    # [-][tag][/module][:class][.method][[params]]
    filter_spec_re = re.compile(
        r'''
        ^
        ([+-]?)               # operator_re
        (\*|\w*)              # tag_re
        (\/[\w\/\.-]+.py)?    # file_re
        (?:\/(\w+))?          # module_re
        (?::(\w*))?           # test_class_re
        (?:\.(\w*))?          # test_method_re
        (?:\[(.*)\])?         # parameters
        $''',
        re.VERBOSE,
    )

    def __init__(self, spec):
        """ Parse the spec to determine tags to whitelist and blacklist. """
        parts = re.split(r',(?![^\[]*\])', spec)  # split on all comma not inside [] (not followed by ])
        filter_specs = [t.strip() for t in parts if t.strip()]
        self.blacklist = set()
        self.whitelist = set()
        self.parameters = OrderedSet()

        for filter_spec in filter_specs:
            match = self.filter_spec_re.match(filter_spec)
            if not match:
                _logger.error('Invalid tag %s', filter_spec)
                continue

            sign, tag, file_path, module, klass, method, parameters = match.groups()
            is_whitelist = sign != '-'
            is_blacklist = not is_whitelist

            if not tag and is_whitelist:
                # including /module:class.method implicitly requires 'standard'
                tag = 'standard'
            elif not tag or tag == '*':
                # '*' indicates all tests (instead of 'standard' tests only)
                tag = None
            filter_info = Info(tag, module, klass, method, file_path)

            if parameters:
                # we could check here that test supports negated parameters
                self.parameters.add((filter_info, ('-' if is_blacklist else '+', parameters)))
                is_blacklist = False

            if is_whitelist:
                self.whitelist.add(filter_info)
            if is_blacklist:
                self.blacklist.add(filter_info)

        if (self.blacklist or self.parameters) and not self.whitelist:
            self.whitelist.add(Info('standard', None, None, None, None))

    def _check(self, test_info):
        test_params = []

        if any(filter_info.match(test_info) for filter_info in self.blacklist):
            return False

        if not any(filter_info.match(test_info) for filter_info in self.whitelist):
            return False

        for filter_info, parameter in self.parameters:
            if filter_info.match(test_info):
                test_params.append(parameter)

        return test_params

    def check(self, test):
        """ Return whether ``arg`` matches the specification: it must have at
            least one tag in ``self.whitelist`` and none in ``self.blacklist`` for each tag category.
        """
        if not hasattr(test, 'test_tags'):  # handle the case where the Test does not inherit from BaseCase and has no test_tags
            _logger.debug("Skipping test '%s' because no test_tag found.", test)
            return False

        if result := self._check(Info(  # noqa: E712
            module=test.test_module,
            klass=test.__class__.__name__,
            tags=test.test_tags | {test.test_module},
            method=test._testMethodName,
            path=test.__module__,
        )) != False:
            test._test_params = result
            return True

        return False
