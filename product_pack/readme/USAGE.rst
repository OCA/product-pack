To use this module, you need to:

#. Go to *Sales > Products > Products*, create a product and set "Is Pack?".
#. Set *Pack Type* and *Pack component price*.
#. Then choose the products to include in the pack.

`Product pack` is a base module for `sale_product_pack` and other modules that
needs to use packs. `Pack type` and `Pack component price` are used to define
the behavior that the packs will have when it is selected in the sales order
lines (if `sale_product_pack` module is installed).
The options of this field are the followings:

`Pack type`:

  * Detailed: It allows you to select an option defined in
    `Pack component price` field.
  * Non Detailed: Will not show the components information,
    only the pack product and the price will be the its price plus the sum of
    all the components prices.

`Pack component price`:

  * Detailed per component: will show each components and its prices,
    including the pack product itself with its price.
  * Totalized in main product: will show each component but will not show
    components prices. The pack product will be the only one that has price
    and this one will be its price plus the sum of all the components prices.
  * Ignored: will show each components but will not show
    components prices. The pack product will be the only one that has price
    and this one will be the price set in the pack product.

+-----------------------------+-----------------------------+---------------------------------+-----------------------------------------+----------------------+
| **Pack type**               | **Show components on SO?**  | **Sale price**                  | **Discount**                            | **Can be modified?** |
+=============================+=============================+=================================+=========================================+======================+
| **Detailed per components** | Yes, with their prices      | Components + Pack               | Applies to the price of the pack and    | Yes, configurable    |
|                             |                             |                                 | the components                          |                      |
+-----------------------------+-----------------------------+---------------------------------+-----------------------------------------+----------------------+
| **Detailed - Totalized**    | Yes, with their prices at 0 | Components                      | Applies to the total (pack + components)| No                   |
+-----------------------------+-----------------------------+---------------------------------+-----------------------------------------+----------------------+
| **Detailed - Ignored**      | Yes, with their prices at 0 | Only Pack                       | Applies to the pack                     | No                   |
+-----------------------------+-----------------------------+---------------------------------+-----------------------------------------+----------------------+
| **No detailed**             | No                          | Components                      | Applies to the total (pack + components)| No                   |
+-----------------------------+-----------------------------+---------------------------------+-----------------------------------------+----------------------+

**Note:** If pricelist enabled, Odoo will display the price according to the corresponding pricelist. In the case of a pricelist with discount policy "Show public price & discount to the customer" keep in mind that the "Non Detailed" and "Detailed - Totalized in main product" packs do not display the discount.
