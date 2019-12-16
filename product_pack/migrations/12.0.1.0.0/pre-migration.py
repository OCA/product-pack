# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


to_install = [
    'sale_product_pack',
    'stock_product_pack',
]


def install_new_modules(cr):
    sql = """
    UPDATE ir_module_module
    SET state='to install'
    WHERE name in %s AND state='uninstalled'
    """ % (tuple(to_install),)
    openupgrade.logged_query(cr, sql)


@openupgrade.migrate()
def migrate(env, version):
    install_new_modules(env.cr)
    openupgrade.rename_fields(env, [
        ('product.template', 'product_template', 'pack', 'pack_ok'),
        ('product.pack.line', 'product_pack_line', 'discount', 'sale_discount')
    ])
    openupgrade.add_fields(env, [
        ('pack_type', 'product.template',
         'product_template', 'selection', False, 'product_template'),
        ('pack_component_price', 'product.template',
         'product_template', 'selection', False, 'product_template'),
        ('pack_modifiable', 'product.template',
         'product_template', 'boolean', False, 'product_template'),
    ])
    openupgrade.logged_query(
        env.cr, """
            UPDATE product_template
            SET pack_type = (
                    CASE
                        WHEN pack_price_type in ('components_price',
                                                'fixed_price',
                                                'totalice_price')
                            THEN 'detailed'
                        WHEN pack_price_type = 'none_detailed_totaliced_price'
                            THEN 'non_detailed'
                        ELSE
                            'assisted'
                    END
                ),
                pack_component_price = (
                    CASE
                        WHEN pack_price_type = 'components_price'
                            THEN 'detailed'
                        WHEN pack_price_type = 'totalice_price'
                            THEN 'totalized'
                        WHEN pack_price_type = 'fixed_price'
                            THEN 'ignored'
                        ELSE
                            NULL
                    END
                ),
                pack_modifiable = (
                    CASE
                        WHEN allow_modify_pack in ('only_backend',
                                                  'frontend_backend')
                            THEN TRUE
                        ELSE
                            FALSE
                    END
                )
            WHERE pack_ok
            """,
    )
