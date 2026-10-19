"""Build an independent Hell difficulty, preserving the seven-pack patch.

Hell is campaign ID 4 (human handicap -4, AI handicap +4), UI index 5.
Its modifier rows are separate copies of Legendary rows, never an ID alias.
"""
from pathlib import Path
import base64
import copy
import hashlib
import json
import struct
import sys

import argparse
import pefile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--engine',type=Path,required=True,help='Local unmodified empire.retail.x64.dll')
parser.add_argument('--manifest',type=Path,required=True,help='manifest.json extracted from the signed release package')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
SOURCE=Path(__file__).resolve().parent
W=args.output
W.mkdir(parents=True,exist_ok=True)
vanilla=args.engine.read_bytes()
r=json.loads(args.manifest.read_text())
assert hashlib.sha256(vanilla).hexdigest()==r['engineSourceSha256']
r.update(json.loads((SOURCE/'baseline-engine.json').read_text()))
h=json.loads((SOURCE/'baseline-helper.json').read_text())
edited = bytearray(vanilla)
for op in r['enginePatches']:
    data = base64.b64decode(op['data'])
    edited[op['offset']:op['offset'] + len(data)] = data
assert hashlib.sha256(edited).hexdigest() == r['engineEditedSha256']
p = pefile.PE(data=edited, fast_load=True)
payload = bytearray(base64.b64decode(h['payload']))
preserved_payload = bytes(payload)
payload.extend(b'\x90' * (-len(payload) % 16))
start = h['rva'] + len(payload)
flag = 55959248 + 160
obj = 55959376
code = bytearray()
labels = {}
fixes = []
patches = []

def emit(hex_bytes):
    code.extend(bytes.fromhex(hex_bytes))

def label(name):
    code.extend(b'\x90' * (-len(code) % 16))
    labels[name] = start + len(code)

def rel(op, target, tail=b''):
    emit(op)
    at = len(code)
    code.extend(b'\0' * 4)
    code.extend(tail)
    fixes.append((at, target, len(tail)))

def patch(rva, replacement, reason, expected=None):
    off = p.get_offset_from_rva(rva)
    old = bytes(edited[off:off + len(replacement)])
    if expected is not None:
        assert old == bytes.fromhex(expected), (hex(rva), old.hex(), expected)
    edited[off:off + len(replacement)] = replacement
    patches.append(dict(rva=rva, before=old.hex(), after=replacement.hex(), reason=reason))

def hook(rva, name, op=0xe8):
    patch(rva, bytes([op]) + struct.pack('<i', labels[name] - rva - 5), name)

# Human settings retain Hell's actual -4. These are copied rule values, not
# a call to a Legendary mode: battle=-2, realm=-2, realism=true.
label('human')
emit('83fafc')
rel('0f85', 'human-ordinary')
emit('41b8feffffff 4533c9 c7442428feffffff c644243001')
rel('c605', flag, b'\x04')
rel('e9', 0x6d8ff0)
label('human-ordinary')
rel('c605', flag, b'\x00')
rel('e9', 0x6d8ff0)

# AI handicap +4 must reach its own copied database rows unchanged.
label('ai')
rel('e9', 0x6d8ff0)

def setup_rules(prefix):
    # Preserve RCX/RDX/R9 and all nonvolatile registers. Detect the persisted
    # difficulty ID itself; a UI flag or legacy Realm Divide marker is not ID.
    emit('4c8b5120 448b591c 4533c0 4585db')
    rel('0f84', prefix + '-end')
    label(prefix + '-loop')
    emit('4180baf000000000')
    rel('0f84', prefix + '-next')
    emit('4183baf4000000fc')
    rel('0f85', prefix + '-next')
    emit('41c782f8000000feffffff 41c782fc00000000000000')
    emit('41c78200010000feffffff 41c6820501000001 41b004')
    label(prefix + '-next')
    emit('4981c210010000 41ffcb')
    rel('0f85', prefix + '-loop')
    label(prefix + '-end')
    rel('448805', flag)
    emit('4584c0')
    rel('0f84', prefix + '-done')
    # Campaign mode remains 4 throughout startup, copies and save/load.
    emit('c7414804000000 c6414601 c6415c01')
    label(prefix + '-done')

label('setup')
setup_rules('setup')
rel('e9', 0x78fc40)
label('loaded-setup')
emit('4989c9 4c89e9')
setup_rules('loaded')
emit('4c89c9')
rel('e9', 0xe9a550)

# This constructor carries the camera/minimap realism flag into battles.
label('battle-rules')
rel('803d', flag, b'\x04')
rel('0f85', 'battle-original')
emit('c644246001')
label('battle-original')
rel('e9', 0x6db3c0)

label('threshold')
emit('81fa95000000')
rel('0f85', 'threshold-original')
rel('803d', flag, b'\x04')
rel('0f85', 'threshold-original')
emit('b8ffffffff c3')
label('threshold-original')
emit('89d0 f30f108481a01d0000')
rel('e9', 0x866d1b)

label('save-name')
rel('803d', flag, b'\x04')
rel('0f85', 'name-original')
emit('81fa80040000')
rel('0f85', 'name-original')
rel('48c705', obj, struct.pack('<I', 14))
rel('48c705', obj + 8, struct.pack('<I', 14))
rel('4c8d15', 'hell-text')
rel('488d05', obj)
emit('4c895010c3')
label('name-original')
emit('48895c2408')
rel('e9', 0xf99325)
label('hell-text')
code.extend('auto_save_hell\0'.encode('utf-16le'))

for at, target, tail in fixes:
    if isinstance(target, str):
        target = labels[target]
    struct.pack_into('<i', code, at, target - (start + at + 4 + tail))

# Allocate the mode cache beyond the previous .data extent, in its existing
# committed page. Old label/UI/reset helpers cannot write to this new slot.
data_section = next(s for s in p.sections if s.Name.rstrip(b'\0') == b'.data')
assert data_section.VirtualAddress + data_section.Misc_VirtualSize <= flag
align_page = lambda x: (x + 4095) & ~4095
assert align_page(flag + 1) == align_page(data_section.VirtualAddress + data_section.Misc_VirtualSize)
patch(data_section.get_file_offset() + 8, struct.pack('<I', flag + 1 - data_section.VirtualAddress), 'allocate independent Hell mode cache')

# Remove both upstream ID-alias hooks from the previous implementation.
patch(0x14cdb56, bytes.fromhex('8918488b1f'), 'preserve selected Hell ID')
patch(0x156b040, bytes.fromhex('48895c2410'), 'remove shared UI-mode capture')
for site in [0x136098, 0x12a547a, 0x137ff87, 0x16a438c, 0x1779bd9]:
    hook(site, 'human')
for site in [0x1360ca, 0x12a54b0, 0x1380111]:
    hook(site, 'ai')
for site in [0x6db20c, 0x6db2de]:
    hook(site, 'setup')
hook(0x7747e6, 'setup', 0xe9)
hook(0x6db215, 'loaded-setup')
for site in [0x136339, 0x8d5e5e, 0x12a56a8, 0x16a4469, 0x1779cdd]:
    hook(site, 'battle-rules')
hook(0x866d10, 'threshold', 0xe9)
patch(0x866d15, b'\x90' * 6, 'threshold stolen-instruction padding')
hook(0xf99320, 'save-name', 0xe9)

# Extend startup rule predicates to the new supported hardest mode. No mode
# ID is rewritten: -4 still reaches human settings and +4 reaches AI settings.
patch(0x12a538a, bytes.fromhex('0f9e85c0020000'), 'Hell ironman startup predicate', '0f9485c0020000')
patch(0x12a53b1, bytes.fromhex('0f4f10'), 'Hell locked realm control', '0f4510')
patch(0x12a53b6, bytes.fromhex('0f4fc3'), 'Hell locked battle difficulty', '0f45c3')

# The actual database lookup clamps IDs before matching. Expand its domain
# so the independent -4/+4 rows can be selected, rather than aliasing -3/+3.
patch(0x11b6c23, struct.pack('<i', -4), 'extend handicap lower bound', 'fdffffff')
patch(0x11b6c39, struct.pack('<i', 4), 'extend handicap upper bound', '03000000')

# This difficulty-derived gameplay category uses copied hardest-mode value 4
# for the new human/AI IDs, without changing their stored difficulty identity.
patch(0xc671c0, b'\x7e', 'Hell human gameplay category', '74')
patch(0xc67216, bytes.fromhex('410f4cc6'), 'Hell AI gameplay category', '410f45c6')

payload.extend(code)
assert payload[:len(preserved_payload)] == preserved_payload
h['payload'] = base64.b64encode(payload).decode()
# Leaf/tail-jump helpers change no nonvolatile register or stack allocation.
(W / 'helper.json').write_text(json.dumps(h, separators=(',', ':')))

# Serialize the full source-relative engine recipe, retaining unrelated edits.
ops = []
i = 0
while i < len(vanilla):
    if edited[i] == vanilla[i]:
        i += 1
        continue
    begin = i
    i += 1
    while i < len(vanilla) and edited[i] != vanilla[i]:
        i += 1
    ops.append(dict(offset=begin, data=base64.b64encode(edited[begin:i]).decode()))
r['enginePatches'] = ops
r['engineEditedSha256'] = hashlib.sha256(edited).hexdigest()
(W / 'engine-edited.bin').write_bytes(edited)
(W / 'manifest.json').write_text(json.dumps(r, separators=(',', ':')))
(W / 'build.json').write_text(json.dumps(dict(helpers=labels, flag=flag, object=obj, patches=patches, modeId=4, humanHandicap=-4, aiHandicap=4, uiIndex=5, realmDivideThreshold=-1, savePrefix='auto_save_hell', originalHelperBytesPreserved=len(preserved_payload)), indent=2))
print('Built distinct Hell source: ID 4, human -4, AI +4; removed Legendary alias hooks; retained original helpers and all seven pack recipes.')
