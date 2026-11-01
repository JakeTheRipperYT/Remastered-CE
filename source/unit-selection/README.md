# Unit selection repair (private0.1.58)

CE can clear a clicked unit during rapid cursor movement, and a fast drag box can commit an empty or stale preview list despite containing units. The cumulative repair covers three separate stages:

1.56 records an ordinary friendly-unit press so the earlier empty-ground release branch cannot undo it.
2.57 restores OG's0.03 movement threshold on both axes. CE used zero, allowing tiny diagonal movement to trigger the later box-selection replacement.
3.58 refreshes native box membership immediately before native ID conversion and commit. Final selection no longer depends on whether a preview update ran between movement and release.

The58 wrapper calls the unchanged native rectangle collector with the current input context, then tail-calls the original ID collector with its original arguments. It does not change geometry, ownership filtering, membership append, group-drag handling, minimum drag distance or selection-manager modifier policy. It uses56 bytes of unused executable padding, including stack-unwind metadata; no writable executable section is added. All nine archive recipes and the55 helper payload are unchanged.

## Verification and limits

`test_refresh.py` executes the complete release handler, native rectangle scan, native plane-bound hit tests, native vector append and native ID conversion.136 cases compare57 with58 across no preview, an empty stale preview, a different stale preview and a correct preview; four drag directions; mixed land/naval membership and eligibility filtering; plus click, small-movement, cancellation and group-drag exclusions. The camera supplies a fixture orthographic frustum; world getters, eligibility, allocation and the final selection consumer are fixtures. No live process is inspected or modified.

The test reproduces57 missing contained units with no/stale preview.58 selects the actual contained land/naval IDs regardless of preview timing. `test_refresh_unwind.py` checks Windows RtlVirtualUnwind at27 adapter instruction boundaries across three image bases. `test_drag.py` retains the57 predicate comparison against actual OG code.19 signed package/launcher integration checks and exact signed-setup engine reconstruction also pass. The user confirmed0.1.58 works in-game on2026-10-31 after testing the selection/fast-drag repair.

Earlier validation was incomplete:56's tests stopped before the later box replacement, and57's release tests used an empty fixture box. The current test exercises actual nonempty membership and conversion rather than substituting a prebuilt ID list.

## Reproduction

Apply `apply_patch.py` to the55 pre-injection engine to produce56, then `apply_drag_threshold.py` for57, then `apply_refresh.py` for58, followed by the unchanged standard helper injector. Every step verifies exact input/output hashes. Test scripts accept supplied local engines and an output directory; dependencies are pefile, capstone and unicorn. The unwind test requires Windows. No complete game binaries or private signing keys are included. This source does not publish a GitHub release or change the public updater.
