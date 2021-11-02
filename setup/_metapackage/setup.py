import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-product-pack",
    description="Meta package for oca-product-pack Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-product_pack',
        'odoo13-addon-sale_product_pack',
        'odoo13-addon-sale_stock_product_pack',
        'odoo13-addon-stock_product_pack',
        'odoo13-addon-website_sale_product_pack',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
