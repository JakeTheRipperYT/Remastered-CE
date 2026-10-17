# Diplomacy demand-list correction

By JakeTheRipper.

Four CE UI call sites select the appropriate first/second negotiating-party mode before querying trade partners or alliances. The eligibility functions themselves remain unchanged.

Trade call RVAs: `0x1686d86`, `0x1686df0`; alliance call RVAs: `0x1686ee3`, `0x1686f4d`.

Each leaf wrapper executes `cmp r8, [rcx+0x28]`, `sete r9b`, then tail-jumps to the original trade (`0xccf210`) or alliance (`0xc3cde0`) function. This matches the confirmed installed fix. Wrappers are appended to the existing redirection-helper payload; no additional engine section or installer schema is required. Existing path-redirection helper code and all native text bytes outside these four calls remain unchanged.
