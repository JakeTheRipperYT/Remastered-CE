"""Run shipped bucket creation for fixed overlapping emitters and camera strafes."""
from pathlib import Path
import json,struct,math
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_group_construction.py')}
source=(W/'test_group_construction.py').read_text().split('\ndistance=')[0]
source=source.replace("elif addr==getcp:u.mem_write(b,bytes(12));ret(b)","elif addr==getcp:u.mem_write(b,struct.pack('<3f',*camera_position));ret(b)")
exec(compile(source,str(W/'group_fixture.py'),'exec'),scope)
u=scope['u'];H=scope['H'];base=scope['base'];q=scope['q'];d=scope['d'];rq=scope['rq'];rd=scope['rd'];run=scope['run']
positions={'A':(0,0,3),'B':(2,0,3),'C':(0,0,4)}
effects={n:H+0x10000+i*0x1000 for i,n in enumerate(positions)};reverse={v:k for k,v in effects.items()}
sources=[H+0x1000,H+0x20000]
for i,s in enumerate(sources):
 q(s+0x90,scope['world']);d(s+0x38,16);q(s+0x40,H+0x30000+i*0x10000)
for n,e in effects.items():q(e,scope['ev']);q(e+0x10,sources[int(n=='C')]+8)
branch=base+0x1abff30;original=bytes(u.mem_read(branch,6))
assert original==bytes.fromhex('0f84c7000000')
candidate=b'\xe9'+struct.pack('<i',0x1abfffd-0x1abff30-5)+b'\x90'
def frame(x,strict):
 scope['camera_position']=(x,0,0);u.mem_write(branch,candidate if strict else original)
 u.ctl_remove_cache(base+0x1abfe80,base+0x1ac0550)
 groups=[]
 for s,names in zip(sources,[['B','A'],['C']]):
  d(s+0x3c,0)
  for n in names:
   e=effects[n];u.mem_write(e+0x60,struct.pack('<3f',*positions[n]));run(base+0x1abfe80,s,e)
  for j in range(rd(s+0x3c)):
   g=rq(s+0x40)+j*32;vec=rq(g+16);n=rd(g+12)
   run(base+0x1a9cec0,vec,vec+n*8,n)
   groups.append(dict(key=struct.unpack('<f',u.mem_read(g+24,4))[0],members=[reverse[rq(vec+i*8)] for i in range(n)]))
 groups.sort(key=lambda g:g['key'],reverse=True)
 return dict(cameraX=x,groups=groups,drawOrder=[n for g in groups for n in g['members']],expectedDistanceOrder=sorted(positions,key=lambda n:sum((a-b)**2 for a,b in zip(positions[n],(x,0,0))),reverse=True))
old=[frame(x,False) for x in [-.01,.01]];fixed=[frame(x,True) for x in [-.01,.01]]
assert old[0]['drawOrder']!=old[1]['drawOrder']
assert old[0]['expectedDistanceOrder']==old[1]['expectedDistanceOrder']==['C','B','A']
assert fixed[0]['drawOrder']==fixed[1]['drawOrder']==['C','B','A']
# Source-alpha blending is noncommutative even when only luminance differs.
def blend(order):
 c=0;brightness={'A':.15,'B':.35,'C':.85}
 for n in order:c=brightness[n]*.65+c*.35
 return c
rows=[]
for x in [i/100 for i in range(-10,11)]:
 f=frame(x,True);assert f['drawOrder']==f['expectedDistanceOrder'];rows.append(f)
import random
rng=random.Random(6364);random_frames=0;far_frames=0;max_groups=0
for case in range(128):
 scope['heap']=H+0x100000;scope['camera_position']=(rng.uniform(-20,20),rng.uniform(0,5),rng.uniform(-20,20))
 expected=[];groups=[]
 for source_index,s in enumerate(sources):
  d(s+0x38,16);d(s+0x3c,0);q(s+0x40,H+0x30000+source_index*0x10000)
  for i in range(1+case%31):
   e=H+0x50000+(source_index*32+i)*0x1000;q(e,scope['ev']);q(e+0x10,s+8)
   radius=1000 if case%2 else 20
   position=(rng.uniform(-radius,radius),rng.uniform(0,10),rng.uniform(-radius,radius))
   u.mem_write(e+0x60,struct.pack('<3f',*position));run(base+0x1abfe80,s,e)
   key=struct.unpack('<f',u.mem_read(e+0xb8,4))[0];expected.append((key,e))
  for j in range(rd(s+0x3c)):
   g=rq(s+0x40)+j*32;assert rd(g+12)==1
   groups.append((struct.unpack('<f',u.mem_read(g+24,4))[0],rq(rq(g+16))))
 assert sorted(groups,reverse=True)==sorted(expected,reverse=True)
 random_frames+=1;far_frames+=int(case%2!=0);max_groups=max(max_groups,len(groups))
receipt=dict(status='REPRODUCED_CAMERA_STRAFE_ORDER_JUMP',fixedEmitterWorldPositions=positions,cameraMovementMetres=.02,original=old,candidate=fixed,originalCompositeBrightness=[blend(f['drawOrder']) for f in old],candidateCompositeBrightness=[blend(f['drawOrder']) for f in fixed],additionalCandidateFrames=len(rows),patch=dict(rva=hex(branch-base),before=original.hex(),after=candidate.hex()),scope='Actual native CE bucket creation and member sort. Global group ordering represented by its native descending mean-distance key. Scalar source-alpha blend demonstration, not live game evidence or GPU capture. Candidate disables bucket coalescing only; may increase material submissions. Live acceptance pending.')
receipt.update(randomCandidateFrames=random_frames,randomFarCandidateFrames=far_frames,maximumGroups=max_groups,nativeCapacityGrowthExercised=max_groups>32)
(W/'overlap-order-reproduction.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
