// Private CE prototype. Installed only after native, asset and installer validation.
typedef unsigned char B;
typedef unsigned int U;
typedef unsigned long long Q;
#define AT(T,p,o) (*(T*)((B*)(p)+(o)))
#define API extern "C" __declspec(dllexport)
#include "controller_layout.h"
extern "C" Q engine_base();
extern "C" int OriginalLoad(void*,void*,void*,U);
extern "C" void OriginalSelect(void*,U,B);
extern "C" void OriginalFrame(void*,void*);
extern "C" void OriginalCheckboxInit(void*,void*);
extern "C" void* OriginalBattleClimate(void*,void*);
extern "C" int _fltused=0;
extern "C" void* memcpy(void* d,const void* s,Q n){B* a=(B*)d;const B* b=(const B*)s;while(n--)*a++=*b++;return d;}
extern "C" void* memset(void* d,int v,Q n){B* a=(B*)d;while(n--)*a++=(B)v;return d;}
struct String {Q size,capacity;void* allocator;wchar_t* data;};
struct State {void* terrain;void* day[4];void* night[4];void* snapshot;B seen[4];B selected;B selectedNight;};
static State state;
static Q settingsKey;
static const wchar_t alwaysKey[]=L"RCE_AlwaysNightCampaign";
static const wchar_t previewKey[]=L"RCE_NightBattlePreview";
static bool contains(const String* s,const wchar_t* word){
 U count=(U)(s->size&0xffff);if(!s->data||count>240)return false;
 for(U i=0;i<count;i++){U j=0;while(word[j]&&i+j<count&&s->data[i+j]==word[j])j++;if(!word[j])return true;}return false;
}
static bool mainTerrain(void* terrain){return terrain&&contains((String*)((B*)terrain+0x60),L"sho_japan");}
static Q key(Q b){
 if(settingsKey)return settingsKey;
 void* preferences=((void*(*)())(b+0xe7fc50))();if(!preferences)return 0;
 String path={};
 ((void*(*)(void*,String*,U))AT(Q,AT(Q,preferences,0),0x68))(preferences,&path,4);
 ((void*(*)(Q*,String*))(b+0x185b290))(&settingsKey,&path);
 ((void(*)(String*))(b+0x19a3f0))(&path);return settingsKey;
}
static bool flag(Q b,const wchar_t* name){
 Q h=key(b);if(!h)return false;U bytes=4;int value=-1;
 typedef long(*Read)(Q,const wchar_t*,void*,void*,void*,U*);
 long result=((Read)AT(Q,b,IAT_REG_QUERY))(h,name,0,0,&value,&bytes);
 return result==0&&bytes==4&&value>0;
}
static void writeFlag(Q b,const wchar_t* name,bool enabled){
 Q h=key(b);if(!h)return;int value=enabled?1:-1;
 typedef long(*Write)(Q,const wchar_t*,U,U,const void*,U);
 ((Write)AT(Q,b,IAT_REG_SET))(h,name,0,4,&value,4);
}
static void preview(Q b,bool enabled){writeFlag(b,previewKey,enabled);}
static bool desired(Q b){return flag(b,alwaysKey)||flag(b,previewKey);}
static bool slotsReady(){for(U i=0;i<4;i++)if(!state.seen[i]||!state.day[i]||!state.night[i])return false;return true;}
static bool ready(){return slotsReady()&&state.snapshot;}
static void* environmentManager(void* terrain){return (B*)AT(void*,terrain,0x40)+0xf88;}
static void* loadNight(Q b,void* terrain,U season){
 String* root=(String*)((B*)terrain+0x60);wchar_t buffer[300];U n=(U)(root->size&0xffff);
 if(n>220)return 0;for(U i=0;i<n;i++)buffer[i]=root->data[i];
 const wchar_t* suffix=season==0?L"\\environment\\rce_night_spring.lighting":season==1?L"\\environment\\rce_night_summer.lighting":season==2?L"\\environment\\rce_night_autumn.lighting":L"\\environment\\rce_night_winter.lighting";
 if(n && (buffer[n-1]==L'\\' || buffer[n-1]==L'/'))n--;
 U j=0;do{buffer[n+j]=suffix[j];}while(suffix[j++]);
 String path={};((void(*)(String*,const wchar_t*))(b+0x19a070))(&path,buffer);
 void* result=((void*(*)(void*,String*))(b+0x1a75030))(environmentManager(terrain),&path);
 ((void(*)(String*))(b+0x19a3f0))(&path);return result;
}
API int NightMapLoad(void* terrain,void* code,void* display,U season){
 Q b=engine_base();int index=OriginalLoad(terrain,code,display,season);
 if(index<0||index>3||season>3||!mainTerrain(terrain))return index;
 if(state.terrain!=terrain||index==0){memset(&state,0,sizeof(state));state.terrain=terrain;preview(b,false);}
 void* records=AT(void*,terrain,0x168);state.day[index]=AT(void*,records,(Q)index*0x50);
 state.night[index]=loadNight(b,terrain,season);state.seen[index]=1;
 if(slotsReady()&&!state.snapshot)state.snapshot=loadNight(b,terrain,0);
 return index;
}
API void NightMapSelect(void* terrain,U index,B fade){
 Q b=engine_base();
 if(terrain!=state.terrain||index>3||!ready()){OriginalSelect(terrain,index,fade);return;}
 bool night=desired(b);void* records=AT(void*,terrain,0x168);void* record=(B*)records+(Q)index*0x50;
 void* manager=environmentManager(terrain);
 // Snapshot the rendered intermediate state before a reversal, preventing a jump.
 void* previous=state.selected?((void*(*)(void*))(b+0x1a6e5f0))(manager):0;
 if(previous)((void(*)(void*,void*))(b+0x1a4b990))(state.snapshot,previous);
 AT(void*,record,0)=night?state.night[index]:state.day[index];
 OriginalSelect(terrain,index,state.selected?fade:0);
 AT(void*,record,0)=state.day[index];
 if(previous&&fade)((void(*)(void*,void*))(b+0x1a87bd0))(manager,state.snapshot);
 state.selected=1;state.selectedNight=night?1:0;
}
API void NightMapFrame(void* terrain,void* renderContext){
 Q b=engine_base();
 if(terrain==state.terrain&&state.selected&&ready()){
  bool target=desired(b);
  if(target!=(state.selectedNight!=0))NightMapSelect(terrain,AT(U,terrain,0x170),1);
 }
 OriginalFrame(terrain,renderContext);
}
API void NightMapBattleSet(void* pending,void* faction,Q enabled){
 Q b=engine_base();
 // Retain the existing reinforcement/vote repair in its entirety.
 ((void(*)(void*,void*,Q))(b+PARENT_NIGHT_SET))(pending,faction,enabled);
 void* context=AT(void*,pending,0x60);void* game=context?AT(void*,context,8):0;
 if(game&&AT(B,game,0x25e0)==0)preview(b,AT(B,pending,0x198)!=0);
}

// CE's Checkbox callback is a native script component. Its Lua template is not
// the persistence path. Only the owned option enters these additional branches.
struct Narrow {Q size,capacity;const char* data;};
static bool equals(const Narrow* s,const char* value){
 if(!s||!s->data)return false;U n=(U)(s->size&0xffff);if(n>100)return false;
 for(U i=0;i<n;i++)if(!value[i]||s->data[i]!=value[i])return false;
 return value[n]==0;
}
static bool ownCheckbox(void* component){
 return component&&equals((Narrow*)((B*)component+0x110),"rce_campaign_always_night");
}
API void NightCheckboxInit(void* component,void* context){
 OriginalCheckboxInit(component,context);
 // UI layout creation precedes state loading. Restore only after full init.
 if(ownCheckbox(component)&&AT(void*,component,0x158)){
  bool selected=flag(engine_base(),alwaysKey);
  Narrow target={selected?8ull:6ull,selected?8ull:6ull,selected?"selected":"normal"};
  ((Q(*)(void*,Narrow*))(engine_base()+0x1489540))(component,&target);
 }
}
API void NightCheckboxCommit(void* signal,void* event){
 void* component=AT(void*,event,0);bool selected=AT(B,event,8)!=0;
 // This is CE's actual changed-value event, independent of pressed/hover state.
 ((void(*)(void*,void*))(engine_base()+0x138d640))(signal,event);
 if(ownCheckbox(component))writeFlag(engine_base(),alwaysKey,selected);
}

struct WidePath {Q size,capacity;wchar_t* data;};
API void* NightBattleClimate(void* climate,void* context){
 Q b=engine_base();void* result=OriginalBattleClimate(climate,context);
 if(!flag(b,alwaysKey)||!context)return result;
 void* battle=AT(void*,context,0);if(!battle)return result;
 void* setup=AT(void*,battle,8);if(!setup)return result;
 void* specification=AT(void*,setup,0x90);if(!specification)return result;
 // Preserve the real battle metadata. Only the environment filename is replaced.
 B visual[0x50];memcpy(visual,(B*)climate+0x20,sizeof(visual));AT(U,visual,0x44)=1;
 U localSeed=AT(U,specification,0x10);WidePath prefix={},night={};
 ((void(*)(WidePath*,void*))(b+0x199df0))(&prefix,(B*)specification+0x18);
 ((void*(*)(U*,WidePath*,Q,void*,WidePath*))(b+0xf18320))(&localSeed,&night,AT(B,specification,0x48)?1:0,visual,&prefix);
 if(night.size&&night.data)((void*(*)(void*,WidePath*))(b+0x19a990))(climate,&night);
 ((void(*)(WidePath*))(b+0x19a3f0))(&night);
 ((void(*)(WidePath*))(b+0x19a3f0))(&prefix);
 return result;
}

#include "dynamic_controller.inc"
