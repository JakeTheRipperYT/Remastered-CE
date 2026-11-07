# CE agent landing and FOTS farm hover-card fixes — 0.1.78

The user requested the accepted original-game behaviors in both CE.dll and the
optional CE8.dll Sim Turns engine. This is a new x64 trace and byte implementation;
no x86 routine or structure offset is transplanted into CE.

## Fleet agents

The `navy_disembark` constructor at 180A660E0 selects the action vtable 182216698.
Its action callback 180AED390 calls native bulk unload 180788C30 at 180AED407.
Immediately before that call, RCX is the actual fleet container returned through
180873AF0. Native unload reads its carried army through the handle at +160h,
unlinks the pair and updates remaining passengers. It does not transfer agents
from the fleet to the army first.

The original CE relationship setup (including 180768920/18076AAF0) links fleet
+160h to the army's embedded handle at +190h, and army +198h back to fleet +158h.
Both containers' agent counts are at +D4h and agent arrays at +D8h.

The existing native transfer at 1807997A0 takes RCX=destination army and
RDX=source fleet. It removes each agent from the old container, attaches it to
the destination and invokes native location/notification routines. The new
adapter checks null/self links and the existing three-agent total capacity,
calls that transfer, then tail-calls the unchanged unload with original RCX.

The adapter preserves all volatile GPR and XMM inputs around the additional
native call, leaves nonvolatile registers untouched, provides 32-byte shadow
space and maintains 16-byte call alignment. It uses a 200-byte frame. Incoming
arithmetic flags are volatile across the original native call; its first branch
uses its own TEST, so they are not treated as an input contract.

## Farm cards

Formatter 1807441B0 checks `gdp_farm` at 1807443A8 through native string comparison
18019B6D0. It omits `bos_gdp_farm`, although CE's building-effects table contains
four entries for that key. Recognized farm effects use existing contextual wealth
query 180AAAF60; the FOTS key instead falls through with its raw effect value.

The new wrapper calls the original comparison first. Only if it fails does it
compare the same key with `bos_gdp_farm`. It preserves the first comparison's
volatile output context around the second call, changing only the boolean AL
result. Existing main-campaign matching and the no-building-context branch are
unchanged. The wealth calculation itself is unmodified.

Direct formatter callers are 18084AC60 and UI binding 1816C0650. The former feeds
building information models including 180849360 and 18167FE40, whose native
records explicitly contain `IconFilename` and `Description`; other callers are
building-info models 181811A60/181812040/181812800. No campaign income routine or
data-pack effect value is changed.

## Placement, preservation and verification

The adapters occupy 648 previously zero bytes at RVA 03776980 in the existing
RX .cepath section. Both source engines have identical unused padding there.
Two sorted RUNTIME_FUNCTION entries and allocation-only unwind records are added
after the existing exception table in unused .rcedata padding. Existing rows are
retained; two native CALLs, bounded padding and the necessary PE metadata/checksum
are the only changed ranges. No engine compiler or new engine dependency is used.

The byte interpreter executes the actual generated instructions with native ABI
stubs that overwrite volatile GPRs, XMM state and shadow space. 1,200 agent cases
and 84 farm cases pass across both modes and three image bases. Full-image diffs,
stack contracts and unwind records are checked. These are native-contract
emulation tests, not gameplay tests.

The signed 0.1.78 installer reconstructs the original .76/.77 normal engine via
its unchanged original recipes/helper, applies guarded `enginePostPatches`, then
builds the rebased Sim Turns variant. Its actual C# reconstruction paths reproduce
both candidate hashes. All 36 application self-tests pass. Existing nine normal
pack recipes, data/data.sim8, alternate bootstrap and Sim Turns behavior are
preserved. Future builds use Build-Current.ps1/current-installer.json.

Normal engine SHA256:
071249e2fa79f21646e0da6d8070ff89f26bc3c85906798a6af09d650633c044.

Sim Turns engine SHA256:
5dd028577255ece4acb2e666960b111aba8f791749ffcd83723665292a38762d.

Evidence: work/agent-farm-ce and outputs/release-0.1.78. User gameplay validation
is pending in both modes. Sim Turns' previously recorded upstream limitations
remain unchanged; no publication is authorized by this task.
