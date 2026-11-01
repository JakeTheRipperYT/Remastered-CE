using U=unsigned int;using Q=unsigned long long;using B=unsigned char;
extern "C" int _fltused=0;
struct Group{void* source;U capacity,count;void** items;float distance;U flags;};
struct Cursor{void* source;void** next;void** end;};
extern "C" void* Allocate(U);extern "C" void Release(void*);
extern "C" void Clear(void*);extern "C" void Sort(void**,void**,Q,Q);
static Q address(void* p){return reinterpret_cast<Q>(p);}
static Q size(void* p,U offset){return *reinterpret_cast<Q*>(static_cast<B*>(p)+offset);}
static U count(void* p,U offset){return *reinterpret_cast<U*>(static_cast<B*>(p)+offset);}
static Group* group(void* raw,Q i){U segment=0;for(Q n=(i|1);n>1;n>>=1)++segment;auto table=*reinterpret_cast<B***>(static_cast<B*>(raw)+0x10);return reinterpret_cast<Group*>(table[segment]+i*32);}
static U key(const Cursor& c){return *reinterpret_cast<U*>(static_cast<B*>(*c.next)+0xb8);}
static bool less(const Cursor& a,const Cursor& b){U x=key(a),y=key(b);return x!=y?x<y:address(a.source)<address(b.source);}
static void sift(Cursor* heap,Q n,Q root){
 for(;;){Q child=root*2+1;if(child>=n)return;if(child+1<n&&less(heap[child],heap[child+1]))++child;if(!less(heap[root],heap[child]))return;Cursor t=heap[root];heap[root]=heap[child];heap[child]=t;root=child;}
}
static void draw(void* source,void* pass,void** items,U n){
 Group g={source,0,n,items,0,0};auto v=*reinterpret_cast<void***>(source);
 reinterpret_cast<void(*)(void*,void*,Group*)>(v[20])(source,pass,&g);
}
extern "C" void PrepareSource(void* raw){
 auto source=static_cast<B*>(raw);Clear(source+0x38);U n=count(raw,0x54);if(!n)return;
 void* world=*reinterpret_cast<void**>(source+0x90);auto wv=*reinterpret_cast<void***>(world);
 void* camera=reinterpret_cast<void*(*)(void*)>(wv[9])(world);auto cv=*reinterpret_cast<void***>(camera);float position[4];
 reinterpret_cast<void(*)(void*,float*)>(cv[15])(camera,position);
 auto items=*reinterpret_cast<void***>(source+0x58);
 for(U i=0;i<n;++i){float scratch[4];void* e=items[i];auto ev=*reinterpret_cast<void***>(e);float* p=reinterpret_cast<float*(*)(void*,float*)>(ev[10])(e,scratch);float x=p[0]-position[0],y=p[1]-position[1],z=p[2]-position[2];*reinterpret_cast<float*>(static_cast<B*>(e)+0xb8)=y*y+x*x+z*z;}
 Sort(items,items+n,n,0);
 if(!count(raw,0x38)){void* storage=Allocate(32);if(!storage)return;*reinterpret_cast<void**>(source+0x40)=storage;*reinterpret_cast<U*>(source+0x38)=1;}
 auto marker=*reinterpret_cast<Group**>(source+0x40);Group g={raw,0,0,nullptr,0,0};*marker=g;*reinterpret_cast<U*>(source+0x3c)=1;
}
extern "C" Q RenderStream(void* raw,void* pass){
 Q markers=size(raw,0x38),total=0;
 for(Q i=0;i<markers;++i){Group* g=group(raw,i);if(g->source)total+=count(g->source,0x54);}
 if(!total||markers>0x100000||total>(0xffffffffull-markers*sizeof(Cursor))/8)return 0;
 auto heap=static_cast<Cursor*>(Allocate(static_cast<U>(markers*sizeof(Cursor)+total*8)));if(!heap)return 0;
 auto output=reinterpret_cast<void**>(reinterpret_cast<B*>(heap)+markers*sizeof(Cursor));Q n=0;
 for(Q i=0;i<markers;++i){Group* g=group(raw,i);void* owner=g->source;g->source=nullptr;if(!owner||!count(owner,0x54))continue;bool duplicate=false;for(Q j=0;j<n;++j)if(heap[j].source==owner)duplicate=true;if(duplicate)continue;void** items=*reinterpret_cast<void***>(static_cast<B*>(owner)+0x58);heap[n++]={owner,items,items+count(owner,0x54)};}
 for(Q i=n/2;i>0;--i)sift(heap,n,i-1);
 Q written=0,start=0,runs=0;void* owner=nullptr;
 while(n){Cursor& c=heap[0];if(c.source!=owner){if(owner){draw(owner,pass,output+start,static_cast<U>(written-start));++runs;}owner=c.source;start=written;}output[written++]=*c.next++;if(c.next==c.end)heap[0]=heap[--n];if(n)sift(heap,n,0);}
 if(owner){draw(owner,pass,output+start,static_cast<U>(written-start));++runs;}Release(heap);return runs;
}
