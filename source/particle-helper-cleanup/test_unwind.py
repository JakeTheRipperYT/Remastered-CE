from pathlib import Path
import sys,json,ctypes as C
sys.path.insert(0,r'F:/Codex/Shogun2-CE/work/disasm_runtime');import capstone
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent
prefix=(W/'test_stream.py').read_text().split('\nrows=[]')[0]
prefix=prefix.replace('nonvol','fixture_nonvol')
prefix=prefix.replace('base=p.OPTIONAL_HEADER.ImageBase','base=selected_base').replace('q(imp.address,dealloc)','q(base+imp.address-p.OPTIONAL_HEADER.ImageBase,dealloc)')
wind=Path('F:/Codex/Remastered-CE-Port/source/test_night_unwind.py').read_text();wind=wind[wind.index('k=C.WinDLL'):wind.index('for base in [')]
wind=wind.replace('stack=0x710000000;ssize=0x20000','stack=S;ssize=0x10000')
results=[]
for selected_base in [0x180000000,0x230000000,0x7ff600000000]:
 exec(compile(prefix,str(W/'stream_fixture.py'),'exec'),globals())
 exec(compile(wind,str(W/'wind_functions.py'),'exec'),globals())
 stop=H+0x5000
 host=k.VirtualAlloc(base,0x4000000,0x3000,4);hs=k.VirtualAlloc(stack,ssize,0x3000,4);assert host==base and hs==stack
 try:
  C.memmove(base,p.get_memory_mapped_image(),len(p.get_memory_mapped_image()))
  rows=layout['unwind'];frame_expected={};boundaries=[0];replays={}
  for ins in md.disasm(p.get_data(layout['exports']['BatchAdapter'],64),base+layout['exports']['BatchAdapter']):
   if ins.mnemonic=='mov' and ins.op_str in ['rdi, r15','rsi, r15']:replays[ins.address+ins.size]=UC_X86_REG_RDI if ins.op_str.startswith('rdi') else UC_X86_REG_RSI
  def root_of(row):
   begin,end,info=row;data=p.get_data(info,4)
   if data[0]>>3&4:
    offset=info+4+((data[2]+1)&~1)*2;parent=struct.unpack('<III',p.get_data(offset,12));return root_of(parent)
   return begin
  def verify(uc,address,size,user):
   row=next((r for r in rows if base+r[0]<=address<base+r[1]),None)
   if row is None:return
   root=root_of(row)
   if address==base+root:
    entry_sp=uc.reg_read(UC_X86_REG_RSP)
    frame_expected[root]=[uc.reg_read(r) if r not in (UC_X86_REG_RSP,UC_X86_REG_RIP) else entry_sp+8 if r==UC_X86_REG_RSP else rq(entry_sp) for r in nonvol]+[uc.reg_read(xmm[i]).to_bytes(16,'little') for i in range(6,16)]
   expected=frame_expected[root]
   if address in replays:expected[nonvol.index(replays[address])]=uc.reg_read(UC_X86_REG_R15)
   actual=unwind(uc,base,address,row)
   assert actual==expected,(hex(address),hex(root),[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b])
   boundaries[0]+=1
  u.hook_add(unicorn.UC_HOOK_CODE,verify)
  for counts in [[],[0],[1],[3,2],[1,1,1]]:fixture(counts,adapter=True)
  results.append(dict(base=hex(base),boundaries=boundaries[0]))
 finally:k.VirtualFree(host,0,0x8000);k.VirtualFree(hs,0,0x8000)
result=dict(status='PASS',windowsRtlVirtualUnwind=True,nonvolatileGPRAndXMMVerified=True,bases=results,boundaries=sum(r['boundaries'] for r in results),chainedMetadataVerified=True)
(W/'unwind-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
