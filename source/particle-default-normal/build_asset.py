"""Repack the unchanged RGB default particle normal for CE's RAB reader."""
from pathlib import Path
import struct,io,json,hashlib,base64
from PIL import Image
import numpy as np
W=Path(__file__).resolve().parent;R=W.parent.parent
source=R/'work/particle-code-investigation/installed/data.pack/effects/textures/default_pfx_packed_normal.dds'
raw=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='63baba1f84b11aba18342f622b00287df5d4019bdbfc3aaf9a5c73353d3f50d2'
assert raw[84:88]==b'DXT5'
height,width=struct.unpack_from('<II',raw,12);mips=struct.unpack_from('<I',raw,28)[0]
header=bytearray(128);header[:4]=b'DDS '
struct.pack_into('<7I',header,4,124,0x2100f,height,width,width*4,0,mips)
# Legacy A8R8G8B8, accepted by the engine's existing DDS loader. Preserve RGB,
# and carry the original green in alpha for CE's red/alpha/blue normal reader.
struct.pack_into('<8I',header,76,32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000)
struct.pack_into('<I',header,108,0x401008)
result=bytearray(header);offset=128;rows=[];mip_arrays=[]
for level in range(mips):
 size=max(1,(width+3)//4)*max(1,(height+3)//4)*16
 old_header=bytearray(raw[:128]);struct.pack_into('<II',old_header,12,height,width);struct.pack_into('<I',old_header,28,1)
 pixels=np.asarray(Image.open(io.BytesIO(old_header+raw[offset:offset+size])).convert('RGBA')).copy()
 assert np.all(pixels[:,:,3]==255)
 original_rgb=pixels[:,:,:3].copy();pixels[:,:,3]=pixels[:,:,1]
 encoded=pixels[:,:,[2,1,0,3]].tobytes();result.extend(encoded)
 probe=bytearray(header);struct.pack_into('<II',probe,12,height,width);struct.pack_into('<I',probe,20,width*4);struct.pack_into('<I',probe,28,1)
 decoded=np.asarray(Image.open(io.BytesIO(probe+encoded)).convert('RGBA'))
 assert np.array_equal(decoded[:,:,:3],original_rgb) and np.array_equal(decoded[:,:,3],original_rgb[:,:,1])
 old_signed=original_rgb.astype(float)/255*4-3
 new_signed=decoded[:,:,[0,3,2]].astype(float)/255*4-3
 assert np.array_equal(old_signed,new_signed)
 mip_arrays.append((width,height,bytes(raw[offset:offset+size]),encoded))
 rows.append(dict(level=level,width=width,height=height,rgbPreservedExactly=True,alphaEqualsOriginalGreenExactly=True,decodedNormalMatchesOGExactly=True))
 offset+=size;width=max(1,width//2);height=max(1,height//2)
assert offset==len(raw)
asset=W/'default_pfx_packed_normal.dds';asset.write_bytes(result)
(W/'asset-operations.json').write_text(json.dumps([dict(data=base64.b64encode(result).decode())],separators=(',',':')))
receipt=dict(status='PASS',sourceSha256=sha(raw),candidateSha256=sha(result),sourceBytes=len(raw),candidateBytes=len(result),mipLevels=mips,mips=rows,scope='Default normal map packing only. RGB preserved at every decoded texel; alpha repurposed for CE RAB normal decoding. Smoke diffuse opacity, shaders, depth, native code and custom normal maps are unchanged. Flashing acceptance remains pending.')
(W/'asset-validation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
