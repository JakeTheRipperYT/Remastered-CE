"""Apply the unit-selection edits before the retained PE helper injector."""
from pathlib import Path
import json,hashlib,sys
if len(sys.argv)!=3:raise SystemExit('Usage: apply_patch.py ENGINE_EDITED_057.bin OUTPUT.bin')
p=json.loads(Path(__file__).with_name('refresh-patch.json').read_text());b=bytearray(Path(sys.argv[1]).read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(b)==p['beforeEditedSha256'],'Expected pre-injection cumulative57 engine'
for o in p['writes']:
 at=o['offset'];before=bytes.fromhex(o['before']);after=bytes.fromhex(o['data'])
 assert len(before)==len(after) and b[at:at+len(before)]==before
 b[at:at+len(after)]=after
assert sha(b)==p['afterEditedSha256']
Path(sys.argv[2]).write_bytes(b)
print('PASS: exact58 pre-injection engine; retain55 helper and use the standard injector')
