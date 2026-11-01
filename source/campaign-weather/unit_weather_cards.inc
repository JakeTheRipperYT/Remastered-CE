// Display current native weather modifiers without changing combat or fatigue.
extern "C" void OriginalUnitCardFrame(void*);
extern "C" void OriginalUnitCardStats(void*);
struct CardWeather {float accuracy,reload;};
static CardWeather cardWeather(Q b,void* card){
 CardWeather out={1,0};void* battle=currentBattle(b);
 if(!campaignBattle(battle)||!AT(void*,card,0x70)||AT(U,card,0x2a0)==2)return out;
 void* unit=AT(void*,card,0x1e0);if(!unit||AT(void*,unit,0x28)!=battle)return out;
 void* setup=AT(void*,battle,8);void* model=setup?AT(void*,setup,0x110):0;
 void* climate=model?AT(void*,model,0x2e8):0;void* climateRecord=climate?AT(void*,climate,0x18):0;
 void* weather=climateRecord?AT(void*,climateRecord,0x20):0;if(!weather)return out;
 void* system=AT(void*,battle,0x28068);void* db=system?AT(void*,system,0x20):0;
 void* rules=db?AT(void*,db,0x1448):0;if(!rules)return out;
 // This native read-only adapter has the same setup reference used by the
 // projectile visibility getter. It reads the live climate's bound DB record.
 struct WeatherView {void* battle;B reserved[0x108];void* model;} view={};
 view.battle=battle;view.model=model;void* viewPointer=&view;
 struct {Q unused;void** setup;} context={0,&viewPointer};
 out.accuracy=((float(*)(void*))(b+0x5e9ec0))(&context);
 if(!(out.accuracy>=0&&out.accuracy<=4))out.accuracy=1;
 U precipitation=AT(U,weather,0x1c);
 if(precipitation==1||precipitation==2){
  void* weapon=((void*(*)(void*))(b+0x210350))(unit);
  U kind=weapon?AT(U,weapon,0x24):0;Q offset=0;
  // Match CE's firing/reload path at 180507c9c, including weapon categories.
  if(kind==1)offset=precipitation==1?0x60c8:0x6188;
  else if(kind==13||kind==18||kind==19)offset=precipitation==1?0x6248:0x6308;
  if(offset){out.reload=AT(float,rules,offset);if(!(out.reload>=-10000&&out.reload<=10000))out.reload=0;}
 }
 return out;
}
struct CardWeatherDraw {void* card;void* unit;CardWeather weather;Q bars;};
static CardWeatherDraw cardWeatherDraws[4];static U cardWeatherDrawNext;
static CardWeatherDraw* cardWeatherDraw(void* card){
 for(U i=0;i<4;i++)if(cardWeatherDraws[i].card==card)return &cardWeatherDraws[i];
 CardWeatherDraw* entry=&cardWeatherDraws[cardWeatherDrawNext++%4];*entry={card,0,{1,0},0};return entry;
}
static bool cardStatIs(void* key,const wchar_t* name){
 WidePath* text=(WidePath*)key;if(!text||!text->data||text->size>64)return false;
 U i=0;while(name[i]&&i<text->size&&text->data[i]==name[i])i++;
 return !name[i]&&i==text->size;
}
// Native refreshes can redraw/reset the widgets without changing the combat
// weather. Observe actual bar state/geometry, not only the last weather value.
static Q cardWeatherBars(Q b,void* card){
 void* list=AT(void*,card,0x310);if(!list)return 0;
 U count=AT(U,list,0x134),statCount=AT(U,card,0x284);void** children=AT(void**,list,0x138);
 B* stats=AT(B*,card,0x288);if(!children||!stats||count>64||statCount>64)return 0;
 Q hash=1469598103934665603ull;
 for(U i=0;i<statCount&&i<count;i++){
  void* key=AT(void*,stats,(Q)i*32);
  if(!cardStatIs(key,L"marksmanship")&&!cardStatIs(key,L"reload_skill"))continue;
  void* row=children[i];if(!row)continue;
  const char* names[]={"bar_base","bar_mod"};
  for(U j=0;j<2;j++){
   struct {Q size,capacity;const char* data;} name={j?7ull:8ull,j?7ull:8ull,names[j]};
   void* bar=((void*(*)(void*,void*))(b+0x1476590))(row,&name);
   hash=(hash^(Q)bar)*1099511628211ull;
   if(bar){
    void* state=AT(void*,bar,0x158);hash=(hash^(Q)state)*1099511628211ull;
    hash=(hash^AT(B,bar,0x1c1))*1099511628211ull;
    if(state){hash=(hash^AT(U,state,0x48))*1099511628211ull;hash=(hash^AT(U,state,0x4c))*1099511628211ull;}
   }
  }
 }
 return hash;
}
API void DynamicUnitCardStats(void* card){
 Q b=engine_base();CardWeather weather=cardWeather(b,card);
 struct Saved {void* row;float value;U index;} saved[2]={};U count=0;
 U baseCount=AT(U,card,0x284),modCount=AT(U,card,0x294);
 B* base=AT(B*,card,0x288);B* mods=AT(B*,card,0x298);
 if(base&&mods&&baseCount<=64&&modCount<=64&&(weather.accuracy!=1||weather.reload!=0)){
  for(U i=0;i<baseCount&&count<2;i++){
   void* key=AT(void*,base,(Q)i*32);if(!key)continue;
   B accuracy=cardStatIs(key,L"marksmanship");
   B reload=!accuracy&&cardStatIs(key,L"reload_skill");
   if(!accuracy&&!reload)continue;
   for(U j=0;j<modCount;j++){
    B* row=mods+(Q)j*32;
    if(!((B(*)(void*,void*))(b+0x19b6a0))(key,AT(void*,row,0)))continue;
    float original=AT(float,row,24),value=AT(float,base,(Q)i*32+24)+original;
    if(!(value>=0&&value<100000))break;
    float effective=accuracy?value*weather.accuracy:value+weather.reload;
    if(effective<0)effective=0;
    saved[count++]={row,original,i};AT(float,row,24)=effective-AT(float,base,(Q)i*32+24);break;
   }
  }
 }
 OriginalUnitCardStats(card);
 // UI-owned cached bonuses remain pristine: no stacking across repeated draws,
 // unit switches, ability refreshes or transitions back to clear weather.
 for(U i=0;i<count;i++){
  // CE's negative-modifier branch resizes and recolours bar_mod but does not
  // make it visible again after another refresh has hidden it.
  if(AT(float,saved[i].row,24)<0){
   void* list=AT(void*,card,0x310);U index=saved[i].index;
   if(list&&index<AT(U,list,0x134)&&AT(U,list,0x134)<=64){
    void** children=AT(void**,list,0x138);void* component=children?children[index]:0;
    if(component){
     struct {Q size,capacity;const char* data;} name={7,7,"bar_mod"};
     void* bar=((void*(*)(void*,void*))(b+0x1476590))(component,&name);
     if(bar)((void(*)(void*,B))(b+0x14899c0))(bar,1);
    }
   }
  }
  AT(float,saved[i].row,24)=saved[i].value;
 }
 CardWeatherDraw* drawn=cardWeatherDraw(card);drawn->unit=AT(void*,card,0x1e0);drawn->weather=weather;drawn->bars=cardWeatherBars(b,card);
}
API void DynamicUnitCardFrame(void* card){
 OriginalUnitCardFrame(card);Q b=engine_base();
 if(!campaignBattle(currentBattle(b))||!AT(void*,card,0x70)||!AT(void*,card,0x1e0)||AT(U,card,0x2a0)==2)return;
 void* component=AT(void*,card,8);
 if(!component||!((B(*)(void*,U))(b+0x147a4e0))(component,0))return;
 CardWeather weather=cardWeather(b,card);CardWeatherDraw* drawn=cardWeatherDraw(card);
 bool penalty=weather.accuracy<1||weather.reload<0;
 if(drawn->unit!=AT(void*,card,0x1e0)||drawn->weather.accuracy!=weather.accuracy||drawn->weather.reload!=weather.reload||(penalty&&drawn->bars!=cardWeatherBars(b,card)))DynamicUnitCardStats(card);
}
