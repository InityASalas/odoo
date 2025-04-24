import inspect
import logging
import time
from collections import Counter

import odoo


class PerfCounter:
    def __enter__(self):
        self.log_method("%s started", self.name)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        other = PerfCounter(copy=self)
        self.log_method(other.delta(self))

    def __init__(
        self, name=None, fmt=None, assertion_report=None,
        cr=None, log_method=None, copy=None,
    ):
        self.name = name or (copy and copy.name)
        self.fmt = fmt or (copy and copy.fmt)
        self.assertion_report = assertion_report or (copy and copy.assertion_report)
        self.cr = cr or (copy and copy.cr)
        if self.log_method:
            self.log_method = log_method
        elif copy:
            self.log_method = copy.log_method
        else:
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            logger_scope = module.__name__ if module else __name__
            logger = logging.getLogger(logger_scope)
            self.log_method = logger.info
        self.counters = Counter({
            'time': time.time(),
            'cursor_queries': self.cr.sql_log_count if self.cr else 0,
            'extra_queries': odoo.sql_db.sql_counter,
            'tests': self.assertion_report.testsRun if self.assertion_report else 0,
        })

    def delta(self, other):
        delta = self.counters - other.counters
        if 'extra_queries' in delta and 'cursor_queries' in delta:
            delta['extra_queries'] -= delta['cursor_queries']
        delta = {k: v for k, v in delta.items() if v}
        tokens = self.fmt or {
            'name': "{name} finished",
            'time': "{time:.2f}s elapsed",  # noqa: RUF027
            'tests': "{tests} tests",
            'cursor_queries': "{cursor_queries} queries",
            'extra_queries': "{extra_queries} extra",
        }
        tokens = {k: v for k, v in tokens.items() if k in delta or k in ('time', 'name')}
        return ", ".join(fmt.format(**delta, name=self.name) for _k, fmt in tokens.items())
