"""Correct CE particle season selection using an existing, same-size code window.

An allocated battle terrain service can be unloaded. Its season is undefined
until map initialization (byte +0x100). In that state use the campaign source.
This generator modifies a private copy only; it never opens a game process.
"""
from pathlib import Path
import argparse,array,hashlib,json,struct,sys

START=0x1b9f164
END=0x1b9f1bb
BATTLE=0x3466658
CAMPAIGN=0x3466660
SEASON=0x3466654
EXPECTED=bytes.fromhex(
 '488b05ed748c014885c0740e8b80a41700008905d8748c01eb3d'
 '488b15db748c014885d27427488b92c00000008b8270010000'
 '488d0c80488b82680100004803c98b4cc830890da5748c01eb0a'
 'c70599748c0100000000')

def replacement():
 code=bytearray();labels={};fixups=[]
 def emit(data):code.extend(bytes.fromhex(data))
 def rip(prefix,target):
  emit(prefix);at=len(code);code.extend(b'\0'*4)
  struct.pack_into('<i',code,at,target-(START+len(code)))
 def jump(op,label):
  emit(op);fixups.append((len(code),label));code.append(0)
 rip('48 8b 05',BATTLE)
 emit('48 85 c0');jump('74','campaign')
 emit('80 b8 00 01 00 00 00');jump('74','campaign')
 emit('8b 80 a4 17 00 00');jump('eb','store')
 labels['campaign']=len(code)
 rip('48 8b 15',CAMPAIGN)
 emit('31 c0 48 85 d2');jump('74','store')
 emit('48 8b 92 c0 00 00 00 8b 82 70 01 00 00')
 emit('48 6b c0 50 48 03 82 68 01 00 00 8b 40 30')
 labels['store']=len(code)
 rip('89 05',SEASON)
 for at,label in fixups:
  distance=labels[label]-(at+1)
  assert -128<=distance<=127
  struct.pack_into('<b',code,at,distance)
 assert len(code)<=END-START
 code.extend(b'\x90'*(END-START-len(code)))
 return bytes(code)

def patch(data:bytes):
 if len(EXPECTED)!=END-START:raise AssertionError('Unexpected code-window length')
 # Resolve an RVA without third-party PE dependencies.
 pe=struct.unpack_from('<I',data,0x3c)[0]
 if data[pe:pe+4]!=b'PE\0\0':raise ValueError('Not a PE image')
 count=struct.unpack_from('<H',data,pe+6)[0];optional=struct.unpack_from('<H',data,pe+20)[0]
 for i in range(count):
  sec=pe+24+optional+i*40
  size,rva,stored,raw=struct.unpack_from('<4I',data,sec+8)
  if rva<=START and END<=rva+stored:
   offset=raw+START-rva;break
 else:raise ValueError('Season code window is not file-backed')
 before=data[offset:offset+END-START]
 if before!=EXPECTED:raise ValueError('Engine bytes differ from the audited baseline')
 output=bytearray(data);output[offset:offset+len(before)]=replacement()
 checksum_at=pe+24+64
 struct.pack_into('<I',output,checksum_at,0)
 words=array.array('H',output if len(output)%2==0 else output+b'\0')
 if sys.byteorder!='little':words.byteswap()
 checksum=sum(words)
 while checksum>>16:checksum=(checksum&0xffff)+(checksum>>16)
 struct.pack_into('<I',output,checksum_at,checksum+len(output))
 assert len(output)==len(data)
 return bytes(output),offset

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.input.resolve()==a.output.resolve():p.error('Input and output must differ')
 original=a.input.read_bytes();updated,offset=patch(original);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(updated)
 receipt=dict(status='CANDIDATE_NOT_INSTALLED',inputSha256=hashlib.sha256(original).hexdigest(),outputSha256=hashlib.sha256(updated).hexdigest(),rva=hex(START),fileOffset=offset,length=END-START,changedBytes=sum(x!=y for x,y in zip(original,updated)),peLayoutUnchanged=True,unwindMetadataUnchanged=True,installed=False,published=False)
 a.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
