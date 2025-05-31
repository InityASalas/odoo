from odoo.addons.account.tests.test_tax import TestTaxCommon
from odoo.tests import tagged
from odoo.exceptions import ValidationError

from odoo.addons.account_tax_python.tools.formula_utils import check_formula, normalize_formula


@tagged('post_install', '-at_install')
class TestTaxesComputation(TestTaxCommon):

    def python_tax(self, formula, **kwargs):
        self.number += 1
        vals = {
            **kwargs,
            'name': f"code_({self.number})",
            'amount_type': 'code',
            'amount': 0.0,
            'formula': formula,
        }
        if 'price_include' in vals:
            price_include = vals.pop('price_include')
            if self.env.company.account_price_include != price_include:
                vals['price_include_override'] = price_include
            else:
                vals['price_include_override'] = False
        return self.env['account.tax'].create(vals)

    def _jsonify_tax(self, tax):
        values = super()._jsonify_tax(tax)
        values['formula_decoded_info'] = tax.formula_decoded_info
        return values

    def assert_python_taxes_computation(
        self,
        formula,
        price_unit,
        expected_values,
        product_values=None,
        price_include='tax_excluded',
    ):
        tax = self.python_tax(formula, price_include=price_include)
        if product_values:
            product = self.env['product.product'].create({
                'name': "assert_python_taxes_computation",
                **product_values,
            })
        else:
            product = None
        return self.assert_taxes_computation(tax, price_unit, expected_values, product=product)

    def test_formula(self):
        self.assert_python_taxes_computation(
            "max(quantity * price_unit * 0.21, quantity * 4.17)",
            130.0,
            {
                'total_included': 157.3,
                'total_excluded': 130.0,
                'taxes_data': (
                    (130.0, 27.3),
                ),
            },
        )
        self.assert_python_taxes_computation(
            "max(quantity * price_unit * 0.21, quantity * 4.17)",
            130.0,
            {
                'total_included': 130.0,
                'total_excluded': 102.7,
                'taxes_data': (
                    (102.7, 27.3),
                ),
            },
            price_include='tax_included',
        )
        self.assert_python_taxes_computation(
            "product.volume * quantity * 0.35",
            100.0,
            {
                'total_included': 135.0,
                'total_excluded': 100.0,
                'taxes_data': (
                    (100.0, 35.0),
                ),
            },
            product_values={'volume': 100.0},
        )
        self.assert_python_taxes_computation(
            'product["volume"] > 100 and 10 or 5',
            100.0,
            {
                'total_included': 110.0,
                'total_excluded': 100.0,
                'taxes_data': (
                    (100.0, 10.0),
                ),
            },
            product_values={'volume': 105.0},
        )
        self.assert_python_taxes_computation(
            "product['volume'] > 100 and 10 or 5",
            100.0,
            {
                'total_included': 105.0,
                'total_excluded': 100.0,
                'taxes_data': (
                    (100.0, 5.0),
                ),
            },
            product_values={'volume': 50.0},
        )
        self.assert_python_taxes_computation(
            "product.volume > 100 and 5 or None",
            100.0,
            {
                'total_included': 100.0,
                'total_excluded': 100.0,
                'taxes_data': [],
            },
            product_values={'volume': 50.0},
        )
        self.assert_python_taxes_computation(
            "(product.volume or 5.0) and 0.0 or 10.0",
            100.0,
            {
                'total_included': 110.0,
                'total_excluded': 100.0,
                'taxes_data': (
                    (100.0, 10.0),
                ),
            },
            product_values={'volume': 0.0},
        )
        self.assert_python_taxes_computation(
            "max(product.volume, 5.0) + 0.0 + -.0",
            100.0,
            {
                'total_included': 105.0,
                'total_excluded': 100.0,
                'taxes_data': (
                    (100.0, 5.0),
                ),
            },
            product_values={'volume': 0.0},
        )
        self._run_js_tests()

    def test_invalid_formula(self):
        invalid_formulas = [
            'product.product_tmpl_id',  # no relational fields
            'product.sudo()',  # You don't have access to any record.
            'tuple(1, 2, 3)',  # only min/max functions, no other callables
            'set(1, 2, 3)',
            '[1, 2, 3]',
            '1,',
            '{1, 2}',
            '{1: 2}',
            '(i for _ in product)',
            '"test"',  # strings are only allowed in subscripts of product
            'product[min("volume", "price")]',
            'product()',
            'product[0]',
            'product[:10]',
            'product["field_that_does_not_exist"]',
            'product.field_that_does_not_exist',
            'product.ids',
            'product._fields',
            'product._cr',
            'range(1, 10)',
        ]

        for formula in invalid_formulas:
            with self.subTest(formula=formula):
                with self.assertRaises(ValidationError):
                    self.python_tax(formula=formula)

    def test_ast_transformer_normalizes(self):
        # this test simply checks that the AST transformer does not raise any error when
        # collecting attributes and rewriting the formula, and also to list a couple of edge cases.
        # of course all these weird edge cases must be filtered out by the validator later on
        valid_cases = [
            (
                "((10_000 / product.__dunders__) * (product['shall'] - product[\"n0t\"] + ((product._pass)))) -.01",
                "10000 / product['__dunders__'] * (product['shall'] - product['n0t'] + product['_pass']) - 0.01",
                {"__dunders__", "shall", "n0t", "_pass"}
            ),
            (
                "-bob[eats(product . sandwich)] + +product. \\\nwith_fries_inside and product['IS_THE_WAY']",
                "-bob[eats(product['sandwich'])] + +product['with_fries_inside'] and product['IS_THE_WAY']",
                {"sandwich", "with_fries_inside", "IS_THE_WAY"}
            ),
            (
                "(product.help_youself, product['with some']) if product[None] else product.tarte_al_djote['grault']",
                "(product['help_youself'], product['with some']) if product[None] else product['tarte_al_djote']['grault']",
                {"help_youself", "with some", "tarte_al_djote"}
            ),
        ]

        for formula, expected_normalized, expected_fields in valid_cases:
            with self.subTest(code=formula):
                normalized_formula, accessed_fields = normalize_formula(self.env, formula)
                self.assertEqual(accessed_fields, expected_fields)
                self.assertEqual(normalized_formula, expected_normalized)

    def test_ast_validator(self):
        to_fail = [
            # no attributes
            # transformer pass before validation rewrote attrs to subscripts,
            # so we don't allow attributes in validation step
            "product.field",
            "isinstance",
            "product.env",
            "(None for _ in ()).gi_frame.f_builtins['__import__']",

            # only whitelisted nodes (no tuples, sets, dicts, lists, etc)
            "1,",
            "product,",
            "min(1, 2),",
            "()",
            "{}",
            "[]",
            "{1: product}",
            "{1, 2}",
            "[product]",
            "(None for _ in product)",

            # only string subscripts of product are allowed
            "product[None]",
            "product[1]",
            "product[:]",
            "not_product['field']",

            # no arbitrary function calls
            "product['a_callable']()",
            "product()",
            "(min or max)(1, 2)",
            "isinstance(1, ())",

            # no arbitrary name load
            "a",
            "__builtins__",
            "isinstance",
        ]
        for formula in to_fail:
            with self.subTest(code=formula):
                with self.assertRaises(ValidationError):
                    check_formula(self.env, formula)
