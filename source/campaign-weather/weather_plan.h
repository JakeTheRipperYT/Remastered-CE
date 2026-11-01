// Campaign battle forecast policy. No engine calls, allocations, or shared RNG.
#pragma once
namespace Weather {
typedef unsigned int U;
enum Kind { Clear, Rain, HeavyRain, Fog, Snow, HeavySnow, KindCount };
struct Input {
 U campaign, seed, waitRoll, season, night, naval, initial, available;
};
struct Phase { U kind, startSeconds, blendSeconds; };
struct Plan { U count; Phase phases[4]; };
static U next(U& seed) {
 seed += 0x9e3779b9u;
 U z=seed; z=(z^(z>>16))*0x85ebca6bu; z=(z^(z>>13))*0xc2b2ae35u;
 return z^(z>>16);
}
static U precipitation(U kind) {
 return kind==Rain||kind==HeavyRain?1:kind==Snow||kind==HeavySnow?2:kind==Fog?3:0;
}
// Restrict to seasonally sensible native states. Storms ease through lighter
// precipitation when that state exists in the stock scene set.
static U neighbours(U kind) {
 switch(kind) {
 case Clear:return (1u<<Rain)|(1u<<Fog)|(1u<<Snow)|(1u<<HeavyRain)|(1u<<HeavySnow);
 case Rain:return (1u<<Clear)|(1u<<HeavyRain)|(1u<<Fog);
 case HeavyRain:return (1u<<Rain)|(1u<<Clear)|(1u<<Fog);
 case Fog:return (1u<<Clear)|(1u<<Rain)|(1u<<Snow)|(1u<<HeavyRain)|(1u<<HeavySnow);
 case Snow:return (1u<<Clear)|(1u<<HeavySnow)|(1u<<Fog);
 case HeavySnow:return (1u<<Snow)|(1u<<Clear)|(1u<<Fog);
 default:return 0;
 }
}
static bool make(const Input& input, Plan& plan) {
 plan.count=0;
 if(!input.campaign||input.season>3||input.night>1||input.naval>1||input.initial>=KindCount)return false;
 U mask=input.available&((1u<<KindCount)-1);
 mask &= input.season==3?~((1u<<Rain)|(1u<<HeavyRain)):~((1u<<Snow)|(1u<<HeavySnow));
 if(!(mask&(1u<<input.initial)))return false;
 U seed=input.seed^(input.waitRoll*0x27d4eb2du)^(input.season*0x165667b1u)
       ^(input.night*0xd3a2646cu)^(input.naval*0xfd7046c5u)^(input.initial*0xb55a4f09u);
 plan.count=1; plan.phases[0]={input.initial,0,0};
 if(next(seed)%100<30)return true;
 U desired=2+next(seed)%3;
 U slot=180+next(seed)%61,used=1u<<input.initial;
 plan.phases[0].blendSeconds=30+next(seed)%31;
 for(U i=1;i<desired;i++) {
  U previous=plan.phases[i-1].kind;
  U choices=neighbours(previous)&mask&~used;
  if(!choices)break;
  // Prefer a gentle easing from a storm, but allow other credible paths.
  U easing=previous==HeavyRain?Rain:previous==HeavySnow?Snow:KindCount;
  U kind=KindCount;
  if(easing<KindCount&&(choices&(1u<<easing))&&next(seed)%4!=0)kind=easing;
  if(kind==KindCount) {
   U count=0;for(U k=0;k<KindCount;k++)if(choices&(1u<<k))count++;
   U pick=next(seed)%count;
   for(U k=0;k<KindCount;k++)if(choices&(1u<<k)){if(!pick--){kind=k;break;}}
  }
  U start=i*slot;used|=1u<<kind;
  plan.phases[i]={kind,start,30+next(seed)%31};plan.count++;
 }
 return true;
}
struct Cursor { U step,index;float startSeconds; };
static Cursor cursor(const Plan& plan,float elapsed){
 if(plan.count<2||!plan.phases[1].startSeconds||!(elapsed>=0))return {0,0,0};
 U slot=plan.phases[1].startSeconds;
 U step=(U)(elapsed/(float)slot);
 return {step,step%plan.count,(float)step*(float)slot};
}
static U phaseAt(const Plan& plan,float elapsed){return cursor(plan,elapsed).index;}
static float progress(const Plan& plan,U index,float elapsed){
 Cursor current=cursor(plan,elapsed);
 if(!current.step||index>=plan.count||!plan.phases[index].blendSeconds)return 1.0f;
 float p=(elapsed-current.startSeconds)/(float)plan.phases[index].blendSeconds;
 return p<0?0:p>1?1:p;
}
static const wchar_t* name(U kind) {
 switch(kind){case Clear:return L"clear";case Rain:return L"rain";
 case HeavyRain:return L"heavy rain";case Fog:return L"fog";case Snow:return L"snow";
 case HeavySnow:return L"heavy snow";default:return L"unknown";}
}
static void append(wchar_t* text,U capacity,U& length,const wchar_t* part) {
 while(*part&&length+1<capacity)text[length++]=*part++;
 if(capacity)text[length]=0;
}
static void describe(const Plan& plan,bool night,wchar_t* text,U capacity) {
 U length=0;if(!capacity)return;text[0]=0;if(!plan.count)return;
 if(plan.count==1) {
  append(text,capacity,length,name(plan.phases[0].kind));
  append(text,capacity,length,night?L" all night.":L" all day.");
 } else {
  U first=0;
  if(plan.phases[0].kind==Clear){append(text,capacity,length,L"Clear skies with intermittent ");first=1;}
  else append(text,capacity,length,L"Intermittent ");
  for(U i=first;i<plan.count;i++){
   if(i>first)append(text,capacity,length,i+1==plan.count?L" and ":L", ");
   append(text,capacity,length,plan.phases[i].kind==Clear?L"clear skies":name(plan.phases[i].kind));
  }
  append(text,capacity,length,L".");
 }

 if(text[0]>=L'a'&&text[0]<=L'z')text[0]-=L'a'-L'A';
}
}
