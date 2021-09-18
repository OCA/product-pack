import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-product-pack",
    description="Meta package for oca-product-pack Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-product_pack',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
