import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-product-pack",
    description="Meta package for oca-product-pack Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-product_pack>=16.0dev,<16.1dev',
        'odoo-addon-sale_product_pack>=16.0dev,<16.1dev',
        'odoo-addon-stock_product_pack>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
