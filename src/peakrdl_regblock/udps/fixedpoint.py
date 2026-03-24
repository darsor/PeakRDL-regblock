from typing import Any

from systemrdl.component import Field
from systemrdl.node import Node, FieldNode
from systemrdl.udp import UDPDefinition


class Int64(int):
    """
    A subclass of int that treats the initialized value as a signed 64-bit integer.
    Values are clamped/wrapped into [-2^63, 2^63 - 1] on construction.

    Examples
    --------
    >>> Int64(0xFFFFFFFFFFFFFFFF)
    Int64(-1)
    """

    def __new__(cls, value=0):
        if isinstance(value, str):
            value = int(value, 0)  # respect 0x / 0b / 0o prefixes
        # Mask to 64 bits, then reinterpret as signed
        value &= (1 << 64) - 1
        if value >= (1 << 63):
            value -= (1 << 64)
        return super().__new__(cls, value)

    def __repr__(self):
        return f"Int64({int(self)})"

    def __str__(self):
        return f"{int(self)}"


class _FixedpointWidth(UDPDefinition):
    valid_components = {Field}
    valid_type = Int64

    def validate(self, node: "Node", value: Any) -> None:
        assert isinstance(node, FieldNode)

        intwidth = node.get_property("intwidth")
        fracwidth = node.get_property("fracwidth")
        assert intwidth is not None
        assert fracwidth is not None
        prop_ref = node.property_src_ref.get(self.name, node.inst_src_ref)

        # incompatible with "counter" fields
        if node.get_property("counter"):
            self.msg.error(
                "Fixed-point representations are not supported for counter fields.",
                prop_ref
            )

        # incompatible with "encode" fields
        if node.get_property("encode") is not None:
            self.msg.error(
                "Fixed-point representations are not supported for fields encoded as an enum.",
                prop_ref
            )

        # ensure node width = fracwidth + intwidth
        if intwidth + fracwidth != node.width:
            self.msg.error(
                f"Number of integer bits ({str(intwidth)}) plus number of fractional "
                f"bits ({str(fracwidth)}) must be equal to the width of the component "
                f"({node.width}).",
                prop_ref
            )


class IntWidth(_FixedpointWidth):
    name = "intwidth"

    def get_unassigned_default(self, node: "Node") -> Any:
        """
        If 'fracwidth' is defined, 'intwidth' is inferred from the node width.
        """
        assert isinstance(node, FieldNode)
        fracwidth = node.get_property("fracwidth", default=None)
        if fracwidth is not None:
            return node.width - fracwidth
        else:
            # not a fixed-point number
            return None


class FracWidth(_FixedpointWidth):
    name = "fracwidth"

    def get_unassigned_default(self, node: "Node") -> Any:
        """
        If 'intwidth' is defined, 'fracwidth' is inferred from the node width.
        """
        assert isinstance(node, FieldNode)
        intwidth = node.get_property("intwidth", default=None)
        if intwidth is not None:
            return node.width - intwidth
        else:
            # not a fixed-point number
            return None
