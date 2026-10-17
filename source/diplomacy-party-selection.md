# Diplomacy demand-list correction

By JakeTheRipper.

0.1.8 explicitly shows the offer/demand list_box components when the stance is break_alliance. The Lua change is limited to this menu state. Runtime capture showed a valid Murakami row (220 by 24 pixels) inside an invisible demand list_box. The local correction was confirmed across multiple clans.

The confirmed local alliance-only query uses the requested faction's actual allies and retains the existing faction exclusions and negotiating-party removal. It is relocated into the existing .cepath helper, with its unwind data, for compatibility with existing installers. Only the two alliance UI call operands change from 0.1.7. Trade UI calls and original engine functions remain unchanged.

Temporary native/Lua diagnostic hooks are excluded. Release construction checks the helper instructions and branch destinations against the confirmed local candidate and checks the exact UI compression through the production installer implementation.
