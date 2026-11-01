# Sorted source streams (private 0.1.66)

User results:0.1.64 fixes close-camera flashing but causes a huge FPS drop;0.1.65 adjacent-run batching still has a big FPS hit (screenshot about44FPS). Live0.1.66 FPS and flashing retention are pending.

0.1.65 still constructs a native bucket for each emitter, allocates its member vector, deep-copies each vector twice during parallel gathering, globally sorts all bucket records and frees all those temporaries. Merging after the sort does not remove that preparation work.

## Replacement

PrepareSource replaces181aea3f0 at its function entry. It calls native181ac35a0 to clear prior groups, gets camera position once per source, computes the same float distance-squared key at emitter+0xb8 and invokes native181a9d1f0 on the source emitter vector. It reuses one32-byte marker group per nonempty source. The marker owns no member vector, so native gather copies zero elements. Existing source arrays and object lifetimes remain owned by the engine.

After native gathering, RenderStream heap-merges the sorted source vectors. Its heap contains one cursor per source; its output holds emitter pointers. One native allocation holds both and is released after all immediate source callbacks complete. Each adjacent source run is submitted through the original source virtual+a0 callback using a temporary group. That callback reads group members immediately and queues source indices; it does not retain the temporary group or pointer array. The earlier index-identity fix is retained. Original marker owners are nulled in the gathered copy so the native outer iterator does not draw twice; native cleanup releases only its own temporary segment storage.

This preserves distance ordering and pointer membership. Unique-distance output matches strict0.1.64. Equal-distance emitters use deterministic source priority rather than arbitrary parallel bucket order; within-source order remains the native sort's order. No shaders, smoke lifetimes, counts, colours, textures or archive recipes change. Required material changes between interleaved effects and GPU overdraw remain possible costs.

Code/unwind information uses1304 bytes of proven executable alignment padding at helper offset0x9300. Existing controller.text ends at helper0x9245, and its.rdata begins at0xa000. Existing helper bytes/fixups/unwind entries are preserved. The two native changes are a source-preparation entry jump and updating the post-gather call to the streaming adapter. Original instructions at that call are replayed. New code is RX and has no persistent mutable globals.

## Validation

43 native fixtures cover1000 emitters, multiple sources, random cameras, ties and empty sources. They execute native sort, clear, empty-vector gather copy, draw and destructor paths. All pointers are drawn once in descending distance order; no leaks or double frees occur. One1000-emitter source uses one camera lookup per preparation and one scratch allocation per streamed pass; its marker storage is reused. The test's simplified gather does not count the native worker's small per-source temporary record allocation.

6669 actual Windows RtlVirtualUnwind checks pass across3image bases for the new code, including chained metadata, caller registers and XMM registers.5057 retained draw-index checks pass. The signed installer reconstructs native-tested engine SHA-256 `c59a7f6be8202cbc65ff3ecb2d1bc6b9192d3073cec4f116f84ddd62c20633d1`. All nine archive recipes are identical to0.1.65. Live battle performance remains unmeasured.

## Smoke layer audit

MusketFire contains both light musket_1 and darker musket_2 smoke in installed/vanillaCE/OG definitions. Colours can also change over an existing puff's life. The installed musket_1 lifetime is6.5 plus/minus2 seconds versus4 plus/minus2 in vanillaCE/OG; the installed group also includes musket_4/5 layers. These preexisting composition choices increase overlap but were not added by64/65/66 and are retained here. No claim is made that the screenshot alone identifies the CPU/GPU bottleneck.

Work/receipt roots: F:/Codex/Remastered-CE-Port/work/particle-sorted-stream and work/release-066. No GitHub push/public release/update feed change.
