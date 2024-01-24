# Copyright 2024 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, SavepointCase


class TestSaleProductPackContract(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_contract_component = cls.env.ref(
            "sale_product_pack_contract.product_pack_cpu_maintenance_component"
        )
        cls.env["product.pack.line"].create(
            {
                "parent_product_id": cls.env.ref(
                    "product_pack.product_pack_cpu_detailed_components"
                ).id,
                "product_id": cls.product_contract_component.id,
                "quantity": 1,
            }
        )

        cls.sale_order = cls.env["sale.order"].create(
            {
                "company_id": cls.env.company.id,
                "partner_id": cls.env.ref("base.res_partner_12").id,
            }
        )

    def test_confirm_sale_with_component_details_generate_contract(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        pack_sol = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "date_start": "2024-01-05",
                "product_uom_qty": 1,
            }
        )
        for position, contract_sol in enumerate(self.sale_order.order_line):
            if (
                contract_sol.product_id.is_contract
                and contract_sol.pack_parent_line_id == pack_sol
            ):
                with Form(self.sale_order) as order_form:
                    with order_form.order_line.edit(position) as sol_form:
                        sol_form.date_start = "2024-01-05"
                    order_form.save()
                break

        self.sale_order.action_confirm()
        contracts = self.sale_order.order_line.contract_id
        contract_lines = self.sale_order.order_line.contract_id.contract_line_ids
        self.assertEqual(len(contracts), 1)
        self.assertEqual(len(contract_lines), 1)
        self.assertEqual(
            contract_lines.date_start,
            fields.Date.to_date("2024-01-05"),
        )

    def test_update_pack_with_contract_component_type_non_detailed_forbidden(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        with self.assertRaisesRegex(
            UserError,
            (
                r"This pack '"
                + product_cp.name.replace("(", r"\(").replace(")", r"\)")
                + r"' contains components \["
                rf"'{self.product_contract_component.name}'\] "
                r"that are marked to be contract products. "
                r"At the moment contract component support only "
                r"on detailed pack type and detailed component price pack."
            ),
        ):
            product_cp.pack_type = "non_detailed"

    def test_update_pack_with_contract_component_price_totalized_forbidden(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        with self.assertRaisesRegex(
            UserError,
            (
                r"This pack '"
                + product_cp.name.replace("(", r"\(").replace(")", r"\)")
                + r"' contains components \["
                rf"'{self.product_contract_component.name}'\] "
                r"that are marked to be contract products. "
                r"At the moment contract component support only "
                r"on detailed pack type and detailed component price pack."
            ),
        ):
            product_cp.pack_component_price = "totalized"

    def test_update_pack_with_contract_component_price_ignored_forbidden(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        with self.assertRaisesRegex(
            UserError,
            (
                r"This pack '"
                + product_cp.name.replace("(", r"\(").replace(")", r"\)")
                + r"' contains components \["
                rf"'{self.product_contract_component.name}'\] "
                r"that are marked to be contract products. "
                r"At the moment contract component support only "
                r"on detailed pack type and detailed component price pack."
            ),
        ):
            product_cp.pack_component_price = "ignored"

    def test_add_contract_line_in_non_detail_pack_forbidden(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_non_detailed")
        with self.assertRaisesRegex(
            UserError,
            (
                r"This pack '"
                + product_cp.name.replace("(", r"\(").replace(")", r"\)")
                + r"' contains components \["
                rf"'{self.product_contract_component.name}'\] "
                r"that are marked to be contract products. "
                r"At the moment contract component support only "
                r"on detailed pack type and detailed component price pack."
            ),
        ):
            self.env["product.pack.line"].create(
                {
                    "parent_product_id": product_cp.id,
                    "product_id": self.product_contract_component.id,
                    "quantity": 1,
                }
            )
