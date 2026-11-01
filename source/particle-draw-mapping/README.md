# CE grouped particle draw index repair (private 0.1.62)

Live result: the user reported 0.1.62 DID NOT fix close-camera smoke flashing. The native index defect remains independently reproduced/corrected; it is not established as the reported flashing cause.

CE adds distance-bucket particle submission. Native `181abfe80` builds buckets using shipped squared-distance thresholds 128 and 150000. `181aea3f0` sorts each bucket by emitter distance, then independently sorts the global emitter list at source+0x58. Group submission sorts bucket mean distances (`181aff420`). Those orders can interleave.

`181a9df80` and the two inlined loops in `181ac0550` test the actual bucket emitter renderer for live particles, but submit source+0x48 (a running bucket cursor) as the emitter index. `181b76670` forwards the source to `181b76850`, whose native vertex upload indexes source+0x58 with the submitted index. The check and upload can therefore address different emitters. OG uses global-list traversal (`1142a620`), with no corresponding bucket-order cursor mismatch.

Reproduction executes shipped native bucket construction and emitter sorts with camera/emitter-origin fixtures. Insertion A,C,B,D,E,F,G at squared distances 1000,1230,1120,940,900,870,1110 yields global order C,B,G,A,D,E,F and bucket order C,G,B,A,D,E,F. With G inactive, the original dispatcher submits 0,2,3,4,5,6; the real native upload copies C,A,A,D,E,F, omitting B and duplicating A. Camera movement changes the distance orders, providing a mechanism for smoke disappearing/reappearing. This is a proven native defect; confirming that it resolves the reported live flashing remains necessary.

## Fix

Replace the six-byte virtual calls at RVAs 0x1a9dfec, 0x1ac0609 and 0x1ac0735 with calls to a 73-byte leaf adapter. Match the actual bucket emitter against the source vector, starting with the existing index and adjacent slots, then a bounded scan on mismatch. Tail-dispatch the unchanged mesh callback with the matching index. Preserve the material-change flag, source running cursor, all nonvolatile registers and RSP. No allocations or shared mutable state. A stale absent entry safely skips the callback.

The adapter occupies explicit unused alignment padding at helper offset 0x4890, between the preserved 0.1.32 prefix ending 0x4884 and the controller beginning 0x5000. It is mapped RX, not writable. It changes no stack/nonvolatile state and uses ordinary Windows x64 leaf unwinding. Existing PE sections and unwind tables remain identical. The only engine binary differences from installed 0.1.61 are the three call sites, adapter bytes and recomputed PE checksum (91 bytes differ). All nine archive recipes are identical; selection and performance changes remain cumulative.

## Verification

5,057 offline native checks pass: all three patched call sites; same/previous/next/fallback/absent matches; 257 whole-dispatcher fixtures with active/inactive emitters and material transitions; actual shipped vertex upload using tagged 40-byte particle records; register and stack preservation; RX mapping. Exact reconstruction through the signed 0.1.62 setup matches the tested engine SHA-256 `d3d228794bdd05c892184a7110504449bd591ae9b6f86e30451f4c5c4a2ab1d7`.

Tests use Unicorn with native PE code and controlled inputs. The upload test fixtures only memcpy; grouping fixtures allocation/vector helpers and camera origins. These are not live game captures. Builds and fixtures remain under F:/Codex/Remastered-CE-Port/work/particle-code-investigation and work/release-062. No public release or update feed was changed.
