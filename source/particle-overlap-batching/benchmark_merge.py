"""Time actual merger/native append fast path in isolated, W^X memory."""
from pathlib import Path
import sys,ctypes as C,json,time,statistics
sys.path.insert(0,r'F:/Codex/Shogun2-CE/work/disasm_runtime');import pefile
W=Path(__file__).resolve().parent;p=pefile.PE(str(W/'CE.campaign-night-candidate.dll'));layout=json.loads((W/'layout.json').read_text())
k=C.WinDLL('kernel32',use_last_error=True);nt=C.WinDLL('ntdll')
k.VirtualAlloc.argtypes=[C.c_void_p,C.c_size_t,C.c_ulong,C.c_ulong];k.VirtualAlloc.restype=C.c_void_p
k.VirtualProtect.argtypes=[C.c_void_p,C.c_size_t,C.c_ulong,C.POINTER(C.c_ulong)];k.VirtualFree.argtypes=[C.c_void_p,C.c_size_t,C.c_ulong]
nt.RtlAddFunctionTable.argtypes=[C.c_void_p,C.c_ulong,C.c_ulonglong];nt.RtlDeleteFunctionTable.argtypes=[C.c_void_p]
host=k.VirtualAlloc(None,p.OPTIONAL_HEADER.SizeOfImage,0x3000,4);assert host
table_address=host+p.OPTIONAL_HEADER.DATA_DIRECTORY[3].VirtualAddress;registered=False
class Group(C.Structure):_fields_=[('source',C.c_void_p),('capacity',C.c_uint),('count',C.c_uint),('items',C.c_void_p),('distance',C.c_float),('flags',C.c_uint)]
try:
 image=p.get_memory_mapped_image();C.memmove(host,image,len(image))
 for section in p.sections:
  protection=0x20 if section.Characteristics&0x20000000 else 4 if section.Characteristics&0x80000000 else 2
  previous=C.c_ulong();assert k.VirtualProtect(host+section.VirtualAddress,max(section.Misc_VirtualSize,section.SizeOfRawData),protection,C.byref(previous))
 assert nt.RtlAddFunctionTable(table_address,p.OPTIONAL_HEADER.DATA_DIRECTORY[3].Size//12,host);registered=True
 fn=C.WINFUNCTYPE(C.c_ulonglong,C.c_void_p)(host+layout['exports']['MergeAdjacent'])
 rows=[]
 for count,run_length in [(32,32),(128,128),(1000,1),(1000,8),(1000,1000),(10000,10000)]:
  groups=(Group*count)();items=(C.c_ulonglong*count)(*range(1,count+1));heads=[]
  for i,g in enumerate(groups):
   g.source=1+(i//run_length)%2;g.capacity=1;g.count=1;g.items=C.addressof(items)+i*8
   if i%run_length==0:
    head=(C.c_ulonglong*run_length)();head[0]=i+1;heads.append(head);g.items=C.addressof(head);g.capacity=run_length
  segments=(C.c_ulonglong*64)(*[C.addressof(groups)]*64);vec=(C.c_ulonglong*8)();vec[2]=C.addressof(segments);vec[7]=count
  template=bytes(groups);samples=[]
  for repeat in range(120):
   C.memmove(groups,template,len(template));t=time.perf_counter_ns();runs=fn(C.addressof(vec));elapsed=time.perf_counter_ns()-t
   assert runs==(count+run_length-1)//run_length
   if repeat>=20:samples.append(elapsed/1000)
  rows.append(dict(emitters=count,sourceRunLength=run_length,groupsAfter=runs,medianMicroseconds=statistics.median(samples),maxMicroseconds=max(samples)))
 receipt=dict(status='PASS',nativeWindowsExecution=True,actualCandidateAndNativeAppend=True,writeXorExecute=True,rows=rows,scope='Isolated CPU microbenchmark with head capacity preallocated. Excludes allocation, gathering, sorting, material setup and GPU work; not battle FPS.')
 (W/'merge-benchmark.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
finally:
 if registered:nt.RtlDeleteFunctionTable(table_address)
 k.VirtualFree(host,0,0x8000)
