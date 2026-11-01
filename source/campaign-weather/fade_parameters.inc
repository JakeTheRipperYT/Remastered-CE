// Native registered shader parameters. No private D3D calls or borrowed slots.
extern "C" void* OriginalWeatherParameters(void*);
extern "C" Q OriginalParticleMaterial(void*);
extern "C" void OriginalSkyDestroy(void*);
extern "C" void OriginalWeatherProgram(void*,void*);
struct Float4 {float x,y,z,w;};
enum FadeField {Surface,OldShape,NewShape,OldMaterial,NewMaterial,OldRange,NewRange,FadeFields};
static __declspec(align(16)) B fadeBuffer[0x48];
static __declspec(align(16)) B fadeFields[FadeFields][0x48];
static __declspec(align(16)) B previousSkyParameter[0x40],previousSunParameter[0x40];
static B parametersRegistered;
static void bindProgramParameter(Q b,void* list,void* parameter){
 U count=AT(U,list,4);void** values=AT(void**,list,8);
 for(U i=0;i<count;i++)if(values[i]==parameter)return;
 ((void(*)(void*,void**))(b+0x132d60))(list,&parameter);
}
API void DynamicWeatherProgram(void* library,void* program){
 OriginalWeatherProgram(library,program);
 if(!parametersRegistered)return;Q b=engine_base();
 // Resource lifecycle registration is separate from shader-program bindings.
 // Lists intentionally contain supersets: reflection selects only resources
 // used by each compiled shader, just as CE's shared camera/environment helpers do.
 for(U i=0;i<6;i++){
  bindProgramParameter(b,(B*)program+0x190+i*16,fadeBuffer);
  bindProgramParameter(b,(B*)program+0x250+i*16,previousSkyParameter);
  bindProgramParameter(b,(B*)program+0x250+i*16,previousSunParameter);
 }
}
static void setFade(Q b,U index,const Float4& value){
 if(!parametersRegistered||index>=FadeFields)return;
 void* data=AT(void*,fadeFields[index],0x28);if(!data)return;
 // Match CE terrain material 181b498c0: XML burn is strength, not multiplier.
 Float4 shader=value;
 if(index==OldRange||index==NewRange)shader.z=1.0f-value.z*0.2f;
 memcpy(data,&shader,16);((void(*)(void*))(b+0x1aeed70))(fadeFields[index]);
}
static void initTexture(Q b,B* output,void* source,const char* name){
 ((void*(*)(void*,U))(b+0x19cd060))(output,2);
 AT(Q,output,0)=AT(Q,source,0);AT(const char*,output,0x28)=name;
 AT(void*,output,0x30)=AT(void*,source,0x30);
}
API void* DynamicWeatherParameters(void* environment){
 void* result=OriginalWeatherParameters(environment);Q b=engine_base();
 if(!parametersRegistered){
  ((void*(*)(void*,U))(b+0x19cd060))(fadeBuffer,1);
  AT(Q,fadeBuffer,0)=AT(Q,environment,0);AT(const char*,fadeBuffer,0x40)="rce_weather_shared";
  for(U i=0;i<FadeFields;i++){
   B* field=fadeFields[i];AT(Q,field,0)=AT(Q,environment,0x90);AT(void*,field,0x18)=fadeBuffer;AT(U,field,0x44)=16;
   const char* name=i==Surface?"g_rce_weather_surface":i==OldShape?"g_rce_weather_old_shape":i==NewShape?"g_rce_weather_new_shape":i==OldMaterial?"g_rce_weather_old_material":i==NewMaterial?"g_rce_weather_new_material":i==OldRange?"g_rce_weather_old_range":"g_rce_weather_new_range";
   AT(const char*,field,0x10)=name;
   ((void(*)(void*,void*))(b+0x19d1d30))(fadeBuffer,field);
  }
  ((void(*)(void*))(b+0x19e9540))(fadeBuffer);
  initTexture(b,previousSkyParameter,(B*)environment+0x3a8,"t_rce_weather_previous_sky");
  initTexture(b,previousSunParameter,(B*)environment+0x3a8,"t_rce_weather_previous_sun");
  parametersRegistered=1;
  // Stock buffers are dirtied by their setters before first use. This buffer
  // must upload an explicit disabled state even before a campaign battle exists.
  Float4 disabled={};setFade(b,Surface,disabled);
 }
 // A graphics reset can recreate the native sampler while our descriptors live.
 AT(void*,previousSkyParameter,0x30)=(B*)environment+0x528;
 AT(void*,previousSunParameter,0x30)=(B*)environment+0x528;
 return result;
}
static void* retainSkyTexture(Q b,void* sky,bool sun){
 WidePath path={},name={};
 if(sun){
  ((void(*)(WidePath*,const char*))(b+0x199e70))(&path,"RigidModels/Skybox/");
  ((void*(*)(void*,WidePath*))(b+0x19bd00))((B*)sky+0x268+0x140,&name);
  ((void(*)(WidePath*,WidePath*))(b+0x19ad60))(&path,&name);
  ((void(*)(WidePath*))(b+0x19a3f0))(&name);
 }else ((void*(*)(void*,WidePath*))(b+0x19bd00))((B*)sky+0x8a8,&path);
 void* job=0;
 if(path.size&&path.data){
  void* storage=((void*(*)(Q))(b+0x18abb0))(0x68);
  if(storage)job=((void*(*)(void*,U,WidePath*,U,Q,B))(b+0x19cb160))(storage,sun?0x71:0x6f,&path,sun?0x2100:0x102,0,1);
 }
 ((void(*)(WidePath*))(b+0x19a3f0))(&path);return job;
}
static void releaseTexture(Q b,void*& job,B* parameter){
 if(parametersRegistered&&parameter)((void(*)(void*,void*))(b+0x1ab6470))(parameter,0);
 if(job){void* old=job;job=0;((void(*)(void*,U))AT(Q,AT(void*,old,0),0))(old,1);}
}
static float mix(float a,float z,float p){return a+(z-a)*p;}
static Float4 shape(void* node,U definition){
 Q o=(Q)definition*0x168;return {AT(float,node,0xe0c+o),AT(float,node,0xe1c+o),AT(float,node,0xe20+o),AT(float,node,0xe28+o)};
}
static Float4 material(void* node,U definition,bool wet){
 Q o=(Q)definition*0x168;return {wet?AT(float,node,0xe08+o):1.0f,AT(float,node,0xe14+o),AT(float,node,0xe18+o),wet?1.0f:0.0f};
}
static Float4 puddleRange(void* node,U definition){
 Q o=(Q)definition*0x168;return {AT(float,node,0xe2c+o),AT(float,node,0xe30+o),AT(float,node,0xe34+o),0};
}
