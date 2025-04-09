from odoo.tests import common


class TestWebReadGroup(common.TransactionCase):
    """Test the 'length' logic of web_read_group_unity, groups logic
    are tested in test_formatted_read_group"""

    maxDiff = None

    def test_limit_offset_performance(self):
        Model = self.env["test_read_group.aggregate"]
        Model.create(
            [
                {"key": 1, "value": 1},
                {"key": 1, "value": 2},
                {"key": 1, "value": 3},
                {"key": 2, "value": 4},
                {"key": 2},
                {"key": 2, "value": 5},
                {},
                {"value": 6},
            ],
        )

        # warmup
        Model.web_read_group_unity([], groupby=["key"], aggregates=["value:sum"])

        # One query for read_group because limit is reached
        with self.assertQueryCount(1):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    limit=4,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        # One _read_group with the limit and other without to get the length
        with self.assertQueryCount(2):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    limit=2,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                    ],
                    "length": 3,
                },
            )

        # One _read_group/query because limit is reached
        with self.assertQueryCount(1):
            self.assertEqual(
                Model.web_read_group_unity(
                    [], groupby=["key"], aggregates=["value:sum"], offset=1
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        with self.assertQueryCount(2):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    offset=1,
                    limit=2,
                    forced_order=[{"name": "key", "asc": False}],
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                    ],
                    "length": 3,
                },
            )

    def test_unfolded_group_limit(self):
        Model = self.env["test_read_group.aggregate"]
        records = Model.create(
            [
                {"key": 1, "value": 1},
                {"key": 1, "value": 2},
                {"key": 1, "value": 3},
                {"key": 2, "value": 4},
                {"key": 2},
                {"key": 2, "value": 5},
                {},
                {"value": 6},
            ],
        )

        read_spec = {
            "key": {},
            "value": {},
        }
        key1_read_records = records[:3].web_read(read_spec)
        key2_read_records = records[3:6].web_read(read_spec)

        # Warmup ormcache
        Model.web_read_group_unity(
            [],
            groupby=["key"],
            aggregates=["value:sum"],
            unfolded_group_limit=2,
            unfold_read_specification=read_spec,
        )

        self.env.invalidate_all()

        # One query formatted_read_group
        # One query for multi searching (get records for each column)
        # One query to read records
        with self.assertQueryCount(3):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=2,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__records": key1_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": key2_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        self.env.invalidate_all()

        # One query formatted_read_group
        # One query for multi searching (get records for each column)
        # One query to read records
        with self.assertQueryCount(3):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    unfolded_group_limit=2,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 1)],
                            "key": 1,
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__records": key1_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": key2_read_records,
                        },
                        {
                            "__extra_domain": [("key", "=", False)],
                            "key": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        self.env.invalidate_all()

        # One query formatted_read_group
        # One query to get the number of group (because limit is reached)
        # One query for multi searching (get records for each column)
        # One query to read records
        with self.assertQueryCount(4):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["key"],
                    aggregates=["value:sum"],
                    offset=1,
                    limit=1,
                    unfolded_group_limit=2,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("key", "=", 2)],
                            "key": 2,
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__records": key2_read_records,
                        },
                    ],
                    "length": 3,
                },
            )

    def test_unfolded_specific_groups(self):
        Model = self.env["test_read_group.aggregate"]
        partner_1, partner_2 = self.env["res.partner"].create(
            [
                {"name": "P1"},
                {"name": "P2"},
            ],
        )
        records = Model.create(
            [
                {"partner_id": partner_1.id, "key": 1, "value": 1},
                {"partner_id": partner_1.id, "key": 1, "value": 2},
                {"partner_id": partner_1.id, "key": 1, "value": 3},
                {"partner_id": partner_2.id, "key": 1, "value": 4},
                {"partner_id": partner_2.id, "key": 2},
                {"partner_id": partner_2.id, "value": 5},
                {},
                {"value": 6},
            ],
        )

        read_spec = {"key": {}, "value": {}, "partner_id": {"fields": {"display_name": {}}}}

        # Warmup ormcache
        Model.web_read_group_unity(
            [],
            groupby=["partner_id", "key"],
            aggregates=["value:sum"],
        )

        # Scenario: list view groupby ['partner_id', 'key'] - no group opened by default
        self.env.invalidate_all()

        # One query for the _read_group
        # One query to read the display_name of partner_id
        with self.assertQueryCount(2):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["partner_id", "key"],
                    aggregates=["value:sum"],
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("partner_id", "=", partner_1.id)],
                            "partner_id": (partner_1.id, 'P1'),
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                        },
                        {
                            "__extra_domain": [("partner_id", "=", partner_2.id)],
                            "partner_id": (partner_2.id, 'P2'),
                            "__count": 3,
                            "value:sum": 4 + 5,
                        },
                        {
                            "__extra_domain": [("partner_id", "=", False)],
                            "partner_id": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

        # Scenario:
        # Client opened manually several groups and reload the view (add a filter / change of views / ...).
        # Simulate that DEFAULT_GROUP_LIMIT is 2.
        current_group_info = [
            {
                'value': partner_1.id,
                'folded': False,  # open the partner group (partner=P1)
                'limit': 2,
                'offset': 0,
                'domain': [],
                'groups': [
                    {
                        'value': 1,
                        'folded': False,  # open the subgroup (key=1)
                        'limit': 2,
                        'offset': 2,  # next page of records
                        'extra_domain': [],
                    },
                ],
            },
            {
                'value': partner_2.id,
                'folded': False,  # open the partner group (partner=P2)
                'limit': 2,
                'offset': 2,  # next page of subgroups
                'domain': [],
                'groups': [
                    {
                        'value': False,
                        'folded': False,  # open the subgroup (key=False)
                        'limit': 2,
                        'offset': 0,
                        'extra_domain': [],
                    },
                ],
            },
            {
                'value': False,
                'folded': True,
            },
        ]
        read_record_2 = records[2].web_read(read_spec)
        read_record_5 = records[5].web_read(read_spec)

        self.env.invalidate_all()

        # One query for the main _read_group
        # One query for the to open subgroup partner=P1
        # One query for the to open subgroup partner=P2
        # One query to fetch all records
        # One query to read fields of test_read_group.aggregate fields
        # One query to read display_name of partner
        with self.assertQueryCount(6):
            self.assertEqual(
                Model.web_read_group_unity(
                    [],
                    groupby=["partner_id", "key"],
                    aggregates=["value:sum"],
                    current_group_info=current_group_info,
                    unfold_read_specification=read_spec,
                ),
                {
                    "groups": [
                        {
                            "__extra_domain": [("partner_id", "=", partner_1.id)],
                            "partner_id": (partner_1.id, 'P1'),
                            "__count": 3,
                            "value:sum": 1 + 2 + 3,
                            "__groups": {
                                'groups': [
                                    {
                                        "__extra_domain": [("key", "=", 1)],
                                        "key": 1,
                                        "__count": 3,
                                        "value:sum": 1 + 2 + 3,
                                        "__records": read_record_2,
                                    },
                                ],
                                "length": 1,  # Should be 3 ?
                            }
                        },
                        {
                            "__extra_domain": [("partner_id", "=", partner_2.id)],
                            "partner_id": (partner_2.id, 'P2'),
                            "__count": 3,
                            "value:sum": 4 + 5,
                            "__groups": {
                                "groups": [
                                    {
                                        "key": False,
                                        "__extra_domain": [("key", "=", False)],
                                        "value:sum": 5,
                                        "__count": 1,
                                        "__records": read_record_5,
                                    }
                                ],
                                "length": 3,
                            },
                        },
                        {
                            "__extra_domain": [("partner_id", "=", False)],
                            "partner_id": False,
                            "__count": 2,
                            "value:sum": 6,
                        },
                    ],
                    "length": 3,
                },
            )

    # TODO: test with __fold
    # TODO: test with forced_order
    # TODO: test with groupby_read_specification
