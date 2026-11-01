#include "weather_plan.h"
#include "weather_catalog.h"
extern "C" void OriginalForecastUI(void*);
extern "C" void OriginalBattleTick(void*,void*,Q);
extern "C" void OriginalWeatherFrame(void*,void*);
extern "C" U OriginalWeatherParticleCount(void*);
extern "C" Q OriginalSkyMaterial(void*);
extern "C" long _InterlockedCompareExchange(volatile long*,long,long);
extern "C" long _InterlockedExchange(volatile long*,long);
#pragma intrinsic(_InterlockedCompareExchange)
#pragma intrinsic(_InterlockedExchange)
#include "fade_parameters.inc"
struct Forecast {
 void* battle;void* specification;Weather::Input input;Weather::Plan plan;
 U assets[4];U visualNight;U generation;float elapsed;U active,stage;
};
static Forecast simulationForecast,publishedForecast;
static volatile long forecastLock;
static U forecastGeneration;
static bool campaignBattle(void* battle){return battle&&AT(B,battle,0x283c9)!=0;}
static void* currentBattle(Q b){void* ui=AT(void*,b,0x3372c28);return ui?AT(void*,ui,0x2b0):0;}
static bool samePath(const WidePath* path,const wchar_t* asset){
 if(!path||!path->data||(path->size&0xffff)>200)return false;
 U n=(U)(path->size&0xffff);
 for(U i=0;i<n;i++){
  wchar_t a=path->data[i],c=asset[i];if(!c)return false;
  if(a==L'/')a=L'\\';if(c==L'/')c=L'\\';
  if(a>=L'A'&&a<=L'Z')a+=32;if(c>=L'A'&&c<=L'Z')c+=32;
  if(a!=c)return false;
 }return !asset[n];
}
static U sceneMask(U season,U night,U naval){
 U mask=0;for(U i=0;i<weatherAssetCount;i++){
  const WeatherAsset& a=weatherAssets[i];if(a.season==season&&a.night==night&&a.naval==naval)mask|=1u<<a.kind;
 }return mask;
}
static U assetFor(U season,U night,U naval,U kind,U random){
 U choices[32],n=0;
 for(U i=0;i<weatherAssetCount;i++){
  const WeatherAsset& a=weatherAssets[i];
  if(a.season==season&&a.night==night&&a.naval==naval&&a.kind==kind&&n<32)choices[n++]=i;
 }
 if(!n&&kind==Weather::Rain)return assetFor(season,night,naval,Weather::HeavyRain,random);
 return n?choices[random%n]:weatherAssetCount;
}
static bool buildForecast(void* battle,Forecast& out){
 // Check origin before touching setup, UI, weather, clocks, or shared state.
 if(!campaignBattle(battle))return false;
 void* setup=AT(void*,battle,8);if(!setup)return false;
 void* spec=AT(void*,setup,0x90);void* model=AT(void*,setup,0x110);
 if(!spec||!model)return false;void* climate=AT(void*,model,0x2e8);if(!climate)return false;
 U initialAsset=weatherAssetCount;
 for(U i=0;i<weatherAssetCount;i++)if(samePath((WidePath*)climate,weatherAssets[i].path)){initialAsset=i;break;}
 if(initialAsset==weatherAssetCount)return false;
 const WeatherAsset& original=weatherAssets[initialAsset];
 U season=AT(U,climate,0x60),actualNight=AT(U,spec,0xbc),naval=AT(B,spec,0x48)?1:0;
 if(season!=original.season||naval!=original.naval||actualNight>1)return false;
 U precip=AT(U,setup,0xc8);U initial=precip==0?Weather::Clear:precip==1?Weather::Rain:precip==2?Weather::Snow:precip==3?Weather::Fog:Weather::KindCount;
 if(Weather::precipitation(original.kind)!=precip)return false;
 void* controller=AT(void*,battle,0x28410);U roll=controller?AT(U,controller,0x18):0;
 // Gameplay plans use actual time of day and an availability set common to
 // both visual modes. A local Always Night preference cannot alter simulation.
 U dayMask=sceneMask(season,0,naval),nightMask=sceneMask(season,1,naval);
 U available=(dayMask&nightMask)|((dayMask|nightMask)&((1u<<Weather::Rain)|(1u<<Weather::HeavyRain))?1u<<Weather::Rain:0);
 Weather::Input input={1,AT(U,spec,0x10),roll,season,actualNight,naval,initial,available};
 Weather::Plan plan={};if(!Weather::make(input,plan))return false;
 out.battle=battle;out.specification=spec;out.input=input;out.plan=plan;out.visualNight=original.night;out.assets[0]=initialAsset;
 U local=input.seed^(roll*0x27d4eb2du);
 for(U i=1;i<plan.count;i++){
  out.assets[i]=assetFor(season,original.night,naval,plan.phases[i].kind,Weather::next(local));
  if(out.assets[i]>=weatherAssetCount)return false;
 }
 return true;
}
API void DynamicForecastUI(void* controller){
 OriginalForecastUI(controller);Q b=engine_base();
 void* context=AT(void*,b,0x3372b90);void* battle=context?AT(void*,context,0x2b0):0;
 if(!campaignBattle(battle))return;Forecast forecast={};if(!buildForecast(battle,forecast))return;
 void* label=AT(void*,controller,0x80);if(!label)return;
 wchar_t text[128];Weather::describe(forecast.plan,forecast.visualNight!=0,text,128);
 WidePath value={};((void(*)(WidePath*,const wchar_t*))(b+0x19a070))(&value,text);
 ((void(*)(void*,WidePath*,U))(b+0x148aab0))(label,&value,0);
 ((void(*)(WidePath*))(b+0x19a3f0))(&value);
}
static void publish(const Forecast& forecast){
 if(_InterlockedCompareExchange(&forecastLock,1,0)!=0)return;
 memcpy(&publishedForecast,&forecast,sizeof(forecast));_InterlockedExchange(&forecastLock,0);
}
API void DynamicBattleTick(void* battle,void* command,Q argument){
 OriginalBattleTick(battle,command,argument);
 if(!campaignBattle(battle)){
  if(simulationForecast.battle){memset(&simulationForecast,0,sizeof(simulationForecast));publish(simulationForecast);}return;
 }
 void* setup=AT(void*,battle,8);if(!setup)return;void* model=AT(void*,setup,0x110);if(!model)return;
 U phase=AT(U,model,0x28);
 if(phase<5||simulationForecast.battle!=battle||simulationForecast.specification!=AT(void*,setup,0x90)){
  Forecast next={};if(!buildForecast(battle,next))return;
  next.generation=++forecastGeneration;simulationForecast=next;
 }
 if(!simulationForecast.plan.count)return;
 float elapsed=AT(float,model,0x38);if(!(elapsed>=0&&elapsed<86400))return;
 simulationForecast.elapsed=elapsed;simulationForecast.active=phase>=5&&phase<=8;simulationForecast.stage=phase;
 if(simulationForecast.active){
  Weather::Cursor current=Weather::cursor(simulationForecast.plan,elapsed);
  U index=current.index;
  // Keep wet-weather gameplay active through a gradual onset/clearance.
  if(current.step&&Weather::progress(simulationForecast.plan,index,elapsed)<.5f)index=(index+simulationForecast.plan.count-1)%simulationForecast.plan.count;
  U precip=Weather::precipitation(simulationForecast.plan.phases[index].kind);
  void* climate=AT(void*,model,0x2e8);
  if(climate&&AT(U,setup,0xc8)!=precip){
   AT(U,setup,0xc8)=precip;AT(U,climate,0x68)=precip;
   void* system=AT(void*,battle,0x28068);void* db=system?AT(void*,system,0x20):0;
   if(db)((void(*)(void*,void*))(engine_base()+0x5d0080))(climate,db);
  }
 }
 publish(simulationForecast);
}
struct OpeningGround {
 void* battle;void* specification;void* owner;U asset,definition;B captured;
 Float4 shape,material,range;float wet,grassCull;
};
static OpeningGround openingGround;
static U openingDefinition(void* node,U kind){
 U native=AT(U,node,0xe8);
 if(kind==Weather::Rain)return 3;if(kind==Weather::HeavyRain)return 4;
 if(kind==Weather::Snow)return 5;if(kind==Weather::HeavySnow)return 6;
 return native<=2?native:0;
}
static bool captureOpeningGround(void* node,const Forecast& forecast){
 bool sameBattle=openingGround.battle==forecast.battle;
 bool sameWorld=openingGround.owner==AT(void*,node,0x50);
 if(openingGround.captured&&openingGround.asset==forecast.assets[0]&&
    ((sameBattle&&openingGround.specification==forecast.specification)||(forecast.stage>=5&&(sameBattle||sameWorld))))return true;
 if(!samePath((WidePath*)((B*)node+0xd48),weatherAssets[forecast.assets[0]].path))return false;
 U definition=openingDefinition(node,weatherAssets[forecast.assets[0]].kind);
 Float4 sh=shape(node,definition),ra=puddleRange(node,definition);
 bool wet=definition==3||definition==4;
 if(wet&&(!(sh.x>0)||!(ra.y>ra.x)))return false;
 OpeningGround value={};value.battle=forecast.battle;value.specification=forecast.specification;
 value.owner=AT(void*,node,0x50);value.asset=forecast.assets[0];value.definition=definition;value.captured=1;
 value.shape=sh;value.material=material(node,definition,wet);value.range=ra;
 value.wet=wet?1.0f:0.0f;value.grassCull=AT(float,node,0xe24+(Q)definition*0x168);
 openingGround=value;return true;
}
struct WeatherRender {
 void* battle;void* node;void* manager;void* snapshot;void* incomingEnvironment;U generation,index,step,definition,targetDefinition;
 U oldCounts[2],newCounts[2];float lastProgress,densityProgress,surfaceProgress,startSeconds;B blending,waitingForTextures,stormActive;
 void* oldSky;void* oldSun;void* incomingSkyHold;float oldSkyValues[10],newSkyValues[10],oldSunValues[6],newSunValues[6];
 float oldParticle[2][8],newParticle[2][8];
 Float4 oldShape,newShape,oldMaterial,newMaterial,oldRange,newRange;
 Float4 startingShape,startingMaterial,startingRange;float startingWet,startingGrassCull;float startingSunEuler[3];
 float oldWet,newWet,oldSnow,newSnow,oldVegetation,newVegetation,oldStormStrength;
 B oldAmbientNames[4][16],oldAmbientRuntime[0x80];B ambientCaptured;
};
static WeatherRender weatherRender;
static void startingGround(Q b){
 Float4 surface={2,weatherRender.startingWet,0,1};setFade(b,Surface,surface);
 setFade(b,OldShape,weatherRender.startingShape);setFade(b,NewShape,weatherRender.startingShape);
 setFade(b,OldMaterial,weatherRender.startingMaterial);setFade(b,NewMaterial,weatherRender.startingMaterial);
 Float4 rainRange=weatherRender.startingRange,grassRange=weatherRender.startingRange;
 rainRange.w=weatherRender.newCounts[0]?1.0f:0.0f;grassRange.w=weatherRender.startingGrassCull;
 setFade(b,OldRange,rainRange);setFade(b,NewRange,grassRange);
}
static void endFade(Q b,bool keepGround=false){
 if(keepGround)startingGround(b);else {Float4 disabled={};setFade(b,Surface,disabled);}
 releaseTexture(b,weatherRender.oldSky,previousSkyParameter);
 releaseTexture(b,weatherRender.oldSun,previousSunParameter);
 releaseTexture(b,weatherRender.incomingSkyHold,0);
 if(weatherRender.ambientCaptured){
  for(U i=0;i<4;i++)((void(*)(void*))(b+0x19a3a0))(weatherRender.oldAmbientNames[i]);
  weatherRender.ambientCaptured=0;
 }
 weatherRender.blending=0;
}
static float rainStorm(U definition){return definition==4?1.0f:definition==3?.65f:0.0f;}
static void stormWeather(Q b,void* node){
 float strength=weatherRender.blending?mix(weatherRender.oldStormStrength,rainStorm(weatherRender.targetDefinition),weatherRender.densityProgress):rainStorm(weatherRender.targetDefinition);
 void* sky=(B*)node+0x348;
 if(strength>.02f){
  if(!weatherRender.stormActive){
   void* owner=AT(void*,node,0x50);
   float now=((float(*)(void*))AT(Q,AT(void*,owner,0),0x1c8))(owner);
   AT(float,sky,0x7f8)=now+30;AT(float,sky,0x7fc)=now+12;
   weatherRender.stormActive=1;
  }
  // Fork lightning changes the native environment for its short flash. Let
  // sheet lightning/thunder build during a fade; enable forks after it finishes
  // so that the engine's flash envelope never replaces our weather envelope.
  AT(float,node,0xd0)=weatherRender.blending&&weatherRender.densityProgress<1?0:90.0f/strength;
  AT(float,node,0xd4)=45.0f/strength;
  AT(float,node,0xd8)=.65f*strength;AT(float,node,0xdc)=.35f*strength;
 }else{
  AT(float,node,0xd0)=AT(float,node,0xd4)=0;
  AT(float,node,0xd8)=AT(float,node,0xdc)=0;weatherRender.stormActive=0;
 }
}
static bool copyPublished(Forecast& out){
 if(_InterlockedCompareExchange(&forecastLock,1,0)!=0)return false;
 memcpy(&out,&publishedForecast,sizeof(out));_InterlockedExchange(&forecastLock,0);return true;
}
API void DynamicWeatherFrame(void* node,void* wind){
 Q b=engine_base();Forecast forecast={};
 if(!copyPublished(forecast)||!forecast.plan.count||forecast.battle!=currentBattle(b)||!campaignBattle(forecast.battle)){
  if(weatherRender.node==node)endFade(b);
  OriginalWeatherFrame(node,wind);return;
 }
 if(!forecast.active){
  if(weatherRender.node==node)endFade(b);
  OriginalWeatherFrame(node,wind);
  // Capture visible opening terrain during deployment, before Start Battle can
  // rebuild weather materials or temporarily reset the native weather enum.
  if(forecast.stage<5)captureOpeningGround(node,forecast);
  return;
 }
 if(!captureOpeningGround(node,forecast)){OriginalWeatherFrame(node,wind);return;}
 if(weatherRender.battle!=forecast.battle||weatherRender.generation!=forecast.generation||weatherRender.node!=node){
  if(!samePath((WidePath*)((B*)node+0xd48),weatherAssets[forecast.assets[0]].path)){
   OriginalWeatherFrame(node,wind);return;
  }
  // Previous managers own and dispose their scratch environments. Never follow
  // an old renderer pointer across battle destruction or a native weather roll.
  endFade(b);memset(&weatherRender,0,sizeof(weatherRender));weatherRender.battle=forecast.battle;
  weatherRender.node=node;weatherRender.generation=forecast.generation;
  void* owner=AT(void*,node,0x50);weatherRender.manager=owner?(B*)owner+0xf88:0;
  if(weatherRender.manager){
   ((void(*)(void*))(b+0x1a9a9b0))(weatherRender.manager);
   memcpy(weatherRender.startingSunEuler,(B*)weatherRender.manager+0xfa0+0x130,12);
  }
  U initialType=openingGround.definition;
  if(initialType<=6){
   weatherRender.startingWet=openingGround.wet;
   weatherRender.startingShape=openingGround.shape;
   weatherRender.startingMaterial=openingGround.material;
   weatherRender.startingRange=openingGround.range;
   weatherRender.startingGrassCull=openingGround.grassCull;
   weatherRender.definition=weatherRender.targetDefinition=initialType;
   for(U layer=0;layer<2;layer++)weatherRender.newCounts[layer]=AT(U,node,0xe80+(Q)initialType*0x168+(Q)layer*0x68);
   startingGround(b);
  }
 }
 if(weatherRender.node!=node||!weatherRender.manager){OriginalWeatherFrame(node,wind);return;}
 Weather::Cursor current=Weather::cursor(forecast.plan,forecast.elapsed);
 U index=current.index,step=current.step;void* manager=weatherRender.manager;
 if(step!=weatherRender.step){
  if(weatherRender.blending)endFade(b,true);
  if(!weatherRender.snapshot){
   const wchar_t* path=L"campaign_maps\\sho_japan\\display\\environment\\rce_night_spring.lighting";
   WidePath value={};((void(*)(WidePath*,const wchar_t*))(b+0x19a070))(&value,path);
   weatherRender.snapshot=((void*(*)(void*,WidePath*))(b+0x1a75030))(manager,&value);
   ((void(*)(WidePath*))(b+0x19a3f0))(&value);
  }
  if(weatherRender.snapshot&&!weatherRender.incomingEnvironment){
   const wchar_t* path=L"campaign_maps\\sho_japan\\display\\environment\\rce_night_summer.lighting";
   WidePath value={};((void(*)(WidePath*,const wchar_t*))(b+0x19a070))(&value,path);
   weatherRender.incomingEnvironment=((void*(*)(void*,WidePath*))(b+0x1a75030))(manager,&value);
   ((void(*)(WidePath*))(b+0x19a3f0))(&value);
  }
  if(weatherRender.snapshot&&weatherRender.incomingEnvironment&&weatherRender.snapshot!=weatherRender.incomingEnvironment){
   ((void(*)(void*))(b+0x1a9a9b0))(manager);
   ((void(*)(void*,void*))(b+0x1a4b990))(weatherRender.snapshot,(B*)manager+0xfa0);
   U oldType=AT(U,node,0xe8);if(oldType>6){OriginalWeatherFrame(node,wind);return;}
   void* sky=(B*)node+0x348;
   if(!weatherRender.oldSky)weatherRender.oldSky=retainSkyTexture(b,sky,false);
   if(!weatherRender.oldSun)weatherRender.oldSun=retainSkyTexture(b,sky,true);
   // Never replace the live scene until its outgoing textures are retained and
   // ready. A cache miss must not turn the beginning of a fade into a flash.
   if((weatherRender.oldSky&&!((B(*)(void*))(b+0x19dbcd0))(weatherRender.oldSky))||
      (weatherRender.oldSun&&!((B(*)(void*))(b+0x19dbcd0))(weatherRender.oldSun))){OriginalWeatherFrame(node,wind);return;}
   memcpy(weatherRender.oldSkyValues,(B*)sky+0x8b8,sizeof(weatherRender.oldSkyValues));
   memcpy(weatherRender.oldSunValues,(B*)sky+0x268+0x150,sizeof(weatherRender.oldSunValues));
   weatherRender.oldWet=oldType==3||oldType==4?1.0f:0.0f;
   weatherRender.oldStormStrength=rainStorm(oldType);
   weatherRender.oldSnow=oldType==5||oldType==6?1.0f:0.0f;
   weatherRender.oldShape=shape(node,oldType);weatherRender.oldMaterial=material(node,oldType,weatherRender.oldWet>0);
   weatherRender.oldRange=puddleRange(node,oldType);weatherRender.oldVegetation=AT(float,node,0xe38+(Q)oldType*0x168);
   void* ambient=(B*)node+0xc30;
   memcpy(weatherRender.oldAmbientRuntime,(B*)ambient+0x40,0x80);
   for(U i=0;i<4;i++)((void(*)(void*,void*))(b+0x199b70))(weatherRender.oldAmbientNames[i],(B*)ambient+0xc0+i*16);
   weatherRender.ambientCaptured=1;
   for(U i=0;i<2;i++)memcpy(weatherRender.oldParticle[i],(B*)node+0xe84+(Q)oldType*0x168+(Q)i*0x68,32);
   for(U i=0;i<2;i++)weatherRender.oldCounts[i]=AT(U,node,0xe80+(Q)oldType*0x168+(Q)i*0x68);
   const wchar_t* path=weatherAssets[forecast.assets[index]].path;U length=0;while(path[length])length++;
   WidePath value={length,length,(wchar_t*)path};
   ((void(*)(void*,WidePath*))(b+0x1b82850))(node,&value);
   // Sky/probe regeneration recreates its native texture job. Keep the incoming
   // asset referenced too, preventing eviction/reloading during that regeneration.
   weatherRender.incomingSkyHold=retainSkyTexture(b,sky,false);
   U targetType=AT(U,node,0xe8);if(targetType>6){OriginalWeatherFrame(node,wind);return;}
   // Native ambient groups cache their resolved definition. Start a separate
   // incoming stream while retaining the old stream's timers and names.
   memset((B*)ambient+0x40,0,0x80);
   weatherRender.targetDefinition=targetType;
   memcpy(weatherRender.newSkyValues,(B*)sky+0x8b8,sizeof(weatherRender.newSkyValues));
   // Crossfade weather textures without rotating the sky between scene headings.
   weatherRender.newSkyValues[4]=weatherRender.oldSkyValues[4];
   AT(float,sky,0x8c8)=weatherRender.oldSkyValues[4];
   memcpy(weatherRender.newSunValues,(B*)sky+0x268+0x150,sizeof(weatherRender.newSunValues));
   weatherRender.newWet=targetType==3||targetType==4?1.0f:0.0f;
   weatherRender.newSnow=targetType==5||targetType==6?1.0f:0.0f;
   weatherRender.newShape=shape(node,targetType);weatherRender.newMaterial=material(node,targetType,weatherRender.newWet>0);
   weatherRender.newRange=puddleRange(node,targetType);weatherRender.newVegetation=AT(float,node,0xe38+(Q)targetType*0x168);
   for(U i=0;i<2;i++)memcpy(weatherRender.newParticle[i],(B*)node+0xe84+(Q)targetType*0x168+(Q)i*0x68,32);
   // Ground appearance is captured once from the opening scene. Later weather
   // changes must neither remove those puddles nor create new ones.
   weatherRender.oldShape=weatherRender.newShape=weatherRender.startingShape;
   weatherRender.oldMaterial=weatherRender.newMaterial=weatherRender.startingMaterial;
   weatherRender.oldRange=weatherRender.newRange=weatherRender.startingRange;
   setFade(b,OldShape,weatherRender.oldShape);setFade(b,NewShape,weatherRender.newShape);
   setFade(b,OldMaterial,weatherRender.oldMaterial);setFade(b,NewMaterial,weatherRender.newMaterial);
   setFade(b,OldRange,weatherRender.oldRange);setFade(b,NewRange,weatherRender.newRange);
   for(U i=0;i<2;i++)weatherRender.newCounts[i]=AT(U,node,0xe80+(Q)targetType*0x168+(Q)i*0x68);
   weatherRender.definition=(weatherRender.newCounts[0]||weatherRender.newCounts[1])?targetType:oldType;
   // Fade out the outgoing rain/snow before selecting a dry definition.
   AT(U,node,0xe8)=weatherRender.definition;
   // The sky shader derives its orientation from the environment sun Euler
   // angles (Environment+0x130), not just SkyDome's extra rotation. Weather
   // changes brightness/colour, not time of day: retain the outgoing direction
   // in the target as well, so it stays fixed during AND after interpolation.
   memcpy((B*)manager+0x80+0x130,(B*)weatherRender.snapshot+0x130,12);
   ((void(*)(void*,void*))(b+0x1a4b990))(weatherRender.incomingEnvironment,(B*)manager+0x80);
   ((void(*)(void*,void*))(b+0x1a87bd0))(manager,weatherRender.snapshot);
   weatherRender.index=index;weatherRender.step=step;weatherRender.lastProgress=-1;weatherRender.blending=1;
   weatherRender.startSeconds=forecast.elapsed;weatherRender.waitingForTextures=1;
  }
 }
 if(step&&step==weatherRender.step&&weatherRender.snapshot&&weatherRender.blending){
  float elapsed=weatherRender.waitingForTextures?0:forecast.elapsed-weatherRender.startSeconds;
  float skyDuration=(float)forecast.plan.phases[index].blendSeconds;
  float available=current.startSeconds+(float)forecast.plan.phases[1].startSeconds-weatherRender.startSeconds-1;
  if(available<1)available=1;
  float rainDuration=skyDuration,surfaceDuration=skyDuration;
  if(rainDuration>available)rainDuration=available;if(surfaceDuration>available)surfaceDuration=available;
  float progress=elapsed/skyDuration;
  float rainProgress=elapsed/rainDuration,surfaceProgress=elapsed/surfaceDuration;
  if(rainProgress<0)rainProgress=0;if(rainProgress>1)rainProgress=1;
  if(surfaceProgress<0)surfaceProgress=0;if(surfaceProgress>1)surfaceProgress=1;
  weatherRender.surfaceProgress=surfaceProgress;
  if(progress<0)progress=0;if(progress>1)progress=1;
  // Feed every scene consumer the same interpolated input, including paths
  // that read the target environment directly instead of the lazy output.
  // The immutable endpoint snapshots avoid cumulative interpolation drift.
  ((void(*)(void*,void*,void*,float))(b+0x1a73fd0))((B*)manager+0x80,weatherRender.incomingEnvironment,weatherRender.snapshot,1-progress);
  AT(float,manager,0x38)=0;AT(B,manager,0x68)=1;
  weatherRender.densityProgress=rainProgress;
  Float4 surface={1,weatherRender.startingWet,mix(weatherRender.oldSnow,weatherRender.newSnow,surfaceProgress),progress};
  setFade(b,Surface,surface);
  // Rain and sky share exactly one duration. Reserved range components carry
  // precipitation coverage and the immutable opening grass-cull threshold.
  U peak=weatherRender.oldCounts[0]>weatherRender.newCounts[0]?weatherRender.oldCounts[0]:weatherRender.newCounts[0];
  weatherRender.oldRange.w=peak?mix((float)weatherRender.oldCounts[0],(float)weatherRender.newCounts[0],rainProgress)/(float)peak:0;
  weatherRender.newRange.w=weatherRender.startingGrassCull;
  setFade(b,OldRange,weatherRender.oldRange);setFade(b,NewRange,weatherRender.newRange);
  if(parametersRegistered){
   if(weatherRender.oldSky)((void(*)(void*,void*))(b+0x1ab6470))(previousSkyParameter,weatherRender.oldSky);
   if(weatherRender.oldSun)((void(*)(void*,void*))(b+0x1ab6470))(previousSunParameter,weatherRender.oldSun);
  }
  void* sky=(B*)node+0x348;
  for(U i=0;i<10;i++){
   float a=weatherRender.oldSkyValues[i],z=weatherRender.newSkyValues[i];
   AT(float,sky,0x8b8+i*4)=mix(a,z,progress);
  }
  for(U i=0;i<6;i++)AT(float,sky,0x268+0x150+i*4)=mix(weatherRender.oldSunValues[i],weatherRender.newSunValues[i],progress);
  // Scene loading already requests the one necessary sky generation. Repeating
  // it during a fade destroys/recreates the native sky texture job and rebinds
  // reflection inputs, producing transient flashes. Per-draw material setters
  // already read the interpolated environment/HDR values without that rebuild.
  weatherRender.lastProgress=progress;
  if(surfaceProgress>=1){
   AT(U,node,0xe8)=weatherRender.targetDefinition;
  }
 }
 // Keep the selected precipitation definition live after its fade completes.
 AT(U,node,0xe8)=weatherRender.blending&&weatherRender.surfaceProgress<1?weatherRender.definition:weatherRender.targetDefinition;
 // Native grass materials also consult these definition values independently
 // of the terrain puddle shader. Preserve the opening geometry/culling policy.
 for(U i=0;i<7;i++){
  AT(float,node,0xe08+(Q)i*0x168)=weatherRender.startingMaterial.x;
  AT(float,node,0xe14+(Q)i*0x168)=weatherRender.startingMaterial.y;
  AT(float,node,0xe18+(Q)i*0x168)=weatherRender.startingMaterial.z;
  AT(float,node,0xe2c+(Q)i*0x168)=weatherRender.startingRange.x;
  AT(float,node,0xe30+(Q)i*0x168)=weatherRender.startingRange.y;
  AT(float,node,0xe34+(Q)i*0x168)=weatherRender.startingRange.z;
  AT(float,node,0xe0c+(Q)i*0x168)=weatherRender.startingShape.x;
  AT(float,node,0xe1c+(Q)i*0x168)=weatherRender.startingShape.y;
  AT(float,node,0xe20+(Q)i*0x168)=weatherRender.startingShape.z;
  AT(float,node,0xe24+(Q)i*0x168)=weatherRender.startingGrassCull;
  AT(float,node,0xe28+(Q)i*0x168)=weatherRender.startingShape.w;
 }
 stormWeather(b,node);
 OriginalWeatherFrame(node,wind);
 // Start Battle can rebuild shader resources independently of weather changes.
 // Reassert the full opening-ground buffer in every steady frame as well.
 if(!weatherRender.blending)startingGround(b);
 // Keep the native surface-water renderer enabled exactly as it began, including
 // steady phases after sky/rain fading has completed.
 AT(float,AT(void*,node,0x50),0x1fc0)=weatherRender.startingWet;
 if(weatherRender.blending){
  if(weatherRender.waitingForTextures){
   void* sky=(B*)node+0x348;void* incomingSky=AT(void*,sky,0x798);void* incomingSun=AT(void*,sky,0x268+0xf8);
   if((!incomingSky||((B(*)(void*))(b+0x19dbcd0))(incomingSky))&&(!incomingSun||((B(*)(void*))(b+0x19dbcd0))(incomingSun))&&(!weatherRender.incomingSkyHold||((B(*)(void*))(b+0x19dbcd0))(weatherRender.incomingSkyHold))){weatherRender.startSeconds=forecast.elapsed;weatherRender.waitingForTextures=0;}
  }
  // Native frame derives surface water from the discrete particle count. Replace
  // that result after it runs, so wetness shares the continuous weather clock.
  void* owner=AT(void*,node,0x50);
  AT(float,owner,0x1fc0)=weatherRender.startingWet;
  void* globals=((void*(*)(void*))(b+0x19f80d0))(AT(void*,b,0x3457888));
  void* vegetation=globals?AT(void*,globals,0x2ae8):0;
  if(vegetation){AT(float,vegetation,0)=mix(weatherRender.oldVegetation,weatherRender.newVegetation,weatherRender.densityProgress);((void(*)(void*))(b+0x1aeed70))((B*)globals+0x2ac0);}
  if(weatherRender.surfaceProgress>=1)endFade(b,true);
 }
}
API U DynamicWeatherParticleCount(void* material){
 U original=OriginalWeatherParticleCount(material);
 // Scale this battle's draw count, leaving all stock weather definitions intact.
 if(AT(void*,material,0xe0)!=weatherRender.node||!campaignBattle(currentBattle(engine_base())))return original;
 U layer=AT(U,material,0xe8);if(layer>1)return original;
 float progress=weatherRender.densityProgress;
 // Keep a stable draw set; the weather vertex shader thins particles with a
 // deterministic per-particle mask, so a cached draw count cannot force a cut.
 U count=(weatherRender.blending?(weatherRender.oldCounts[layer]>weatherRender.newCounts[layer]?weatherRender.oldCounts[layer]:weatherRender.newCounts[layer]):weatherRender.newCounts[layer])*6;
 U capacity=AT(U,material,0x98);return count<capacity?count:capacity;
}
API Q DynamicParticleMaterial(void* material){
 if(!weatherRender.blending||AT(void*,material,0xe0)!=weatherRender.node)return OriginalParticleMaterial(material);
 U layer=AT(U,material,0xe8);if(layer>1)return OriginalParticleMaterial(material);
 void* node=weatherRender.node;U definition=AT(U,node,0xe8);if(definition>6)return OriginalParticleMaterial(material);
 B* profile=(B*)node+0xe84+(Q)definition*0x168+(Q)layer*0x68;float saved[8];memcpy(saved,profile,32);
 bool from=weatherRender.oldCounts[layer]!=0,to=weatherRender.newCounts[layer]!=0;
 for(U i=0;i<8;i++){
  float a=weatherRender.oldParticle[layer][i],z=weatherRender.newParticle[layer][i];
  AT(float,profile,i*4)=from&&to?mix(a,z,weatherRender.densityProgress):from?a:z;
 }
 Q result=OriginalParticleMaterial(material);memcpy(profile,saved,32);return result;
}
API Q DynamicSkyMaterial(void* material){
 Q result=OriginalSkyMaterial(material);Q b=engine_base();
 if(!weatherRender.node||AT(void*,material,0xd8)!=(B*)weatherRender.node+0x348||!campaignBattle(currentBattle(b)))return result;
 float direction[3],sn,cs;
 ((void*(*)(const float*,float*))(b+0x1990b80))(weatherRender.startingSunEuler,direction);
 ((void(*)(float,float*,float*))(b+0x21d710))(AT(float,(B*)weatherRender.node+0x348,0x8c8),&sn,&cs);
 float fixed[3]={-cs*direction[0]-sn*direction[2],-direction[1],-cs*direction[2]+sn*direction[0]};
 void* globals=((void*(*)(void*))(b+0x19f80d0))(AT(void*,b,0x3457888));
 void* data=globals?AT(void*,globals,0x23b8):0;
 if(data){memcpy(data,fixed,12);((void(*)(void*))(b+0x1aeed70))((B*)globals+0x2390);}
 return result;
}
API void DynamicSkyDestroy(void* sky){
 if(weatherRender.node&&(B*)weatherRender.node+0x348==sky){endFade(engine_base());memset(&weatherRender,0,sizeof(weatherRender));}
 OriginalSkyDestroy(sky);
}
API void DynamicAmbientFrame(void* ambient,float time,float dt,void* wind){
 typedef void(*Update)(void*,float,float,void*);Update original=(Update)(engine_base()+0x1b4db80);
 if(!weatherRender.blending||!weatherRender.ambientCaptured||(B*)weatherRender.node+0xc30!=ambient){original(ambient,time,dt,wind);return;}
 B incomingRuntime[0x80],incomingNames[0x40];
 memcpy(incomingRuntime,(B*)ambient+0x40,0x80);memcpy(incomingNames,(B*)ambient+0xc0,0x40);
 memcpy((B*)ambient+0x40,weatherRender.oldAmbientRuntime,0x80);memcpy((B*)ambient+0xc0,weatherRender.oldAmbientNames,0x40);
 original(ambient,time,dt*(1-weatherRender.densityProgress),wind);
 memcpy(weatherRender.oldAmbientRuntime,(B*)ambient+0x40,0x80);
 memcpy((B*)ambient+0x40,incomingRuntime,0x80);memcpy((B*)ambient+0xc0,incomingNames,0x40);
 original(ambient,time,dt*weatherRender.densityProgress,wind);
}

#include "unit_weather_cards.inc"
