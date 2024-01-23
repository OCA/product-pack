This module is glue module between *Sale Product Pack* and *Contract*'s modules.

At the moment it mainly prevent to configure pack with weird
configuration that would let user in unexpected situations.

Currently this module support following situation:

* Pack is not a contract with at least one line of the pack is a
  contract line, pack must be configured as `pack_type=detailed` and
  `pack_component_price=detailed`.
