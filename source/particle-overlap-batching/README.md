# Batch adjacent emitters after the global sort (private 0.1.65)

Live result: user confirmed0.1.64 removes flashing but produces a huge FPS drop.0.1.65 FPS recovery and flashing retention are pending.

The strict-order candidate creates one group per emitter. The native group draw loop181a9df80 (and inline variants in181ac0550) initializes its previous-material pointer to zero for every group. Consequently every singleton requests material setup, even for consecutive emitters with the same source/material. Native deferred draw records store this state-change flag.

Keep0.1.64's exact global sorted sequence. Once native181aff420 returns in181b0e980, merge only adjacent groups owned by the same source. Append member pointers in their existing order with native180132d60. Null the consumed group's owner so the native iteration skips its draw callback; leave its vector allocated for native181b1b0e0 cleanup. Another source or empty entry ends the run. The original draw loop now spans the complete adjacent run, so its existing material comparison can reuse state within the run. No source is moved past another, and the original averaged-distance coalescing remains disabled.

One six-byte call replaces `mov rdi,r15; mov rsi,r15` at RVA0x1b0ebc0 after the global sort. BatchAdapter receives the completed concurrent_vector at caller RSP+0x20, invokes MergeAdjacent, replays those instructions and returns. Code and compiler-generated unwind data occupy324 bytes of proven unused RX helper alignment padding at offset0x4900, after the preserved original payload and prior draw-index adapter, before the existing controller at0x5000. No new mutable global state, texture/shader changes or worker concurrency are introduced; all gather workers have completed before sorting/merging. Existing helper bytes, fixups and unwind entries are preserved; new chained unwind records are relocated and registered.

## Verification

145 native cases execute the compiled merger, actual native vector append/growth, the actual native draw dispatcher and native TBB destructor. Cases cover segment boundaries, up to1000 emitters, randomized source/material interleaving, inactive entries and empty boundaries. Exact0.1.64 draw sequence and membership are preserved. Every allocation is freed once. Actual native material-setup flags fall1000->1 for1000 visible same-source/same-material emitters. Separate5057 retained draw-index checks pass.

Actual Windows RtlVirtualUnwind passes1158 executed instruction boundaries across3image bases, including chained compiler records, early exits, loops, epilogs and adapter instruction replay. Nonvolatile GPRs and XMM6-XMM15 are checked.

An isolated native Windows microbenchmark executes the emitted merger and native append fast path from W^X-protected memory with registered unwind metadata. Median is5.2microseconds for1000 same-source emitters with preallocated capacity;10000 take20.6microseconds. This excludes native allocation, gathering, sorting, material setup and GPU work. It is not a battle FPS measurement.

Signed installer reconstruction matches native-tested engine SHA-256 `7b09f73bdf745118517c8a1762747d60811a763c2b7984d4389cc8f94f90e615`. All nine archive recipes are unchanged from0.1.64. The preexisting per-emitter allocation/sort work remains; live performance may require further optimization if it is still material.

Work/receipt roots: F:/Codex/Remastered-CE-Port/work/particle-overlap-batching and work/release-065. No GitHub push, public release or update feed changes.
