To use this module, you need to:

1.  Go to *Sales \> Products \> Products*, create a product and set "Is
    Pack?".
2.  Set *Pack Type* and *Pack component price*.
3.  Then choose the products to include in the pack.

Product pack is a base module for sale_product_pack and other modules
that needs to use packs. Pack type and Pack component price are used to
define the behavior that the packs will have when it is selected in the
sales order lines (if sale_product_pack module is installed). The
options of this field are the followings:

\`Pack type\`:

> - Detailed: It allows you to select an option defined in Pack
>   component price field.
> - Non Detailed: Will not show the components information, only the
>   pack product and the price will be the its price plus the sum of all
>   the components prices.

\`Pack component price\`:

> - Detailed per component: will show each components and its prices,
>   including the pack product itself with its price.
> - Totalized in main product: will show each component but will not
>   show components prices. The pack product will be the only one that
>   has price and this one will be its price plus the sum of all the
>   components prices.
> - Ignored: will show each components but will not show components
>   prices. The pack product will be the only one that has price and
>   this one will be the price set in the pack product.
