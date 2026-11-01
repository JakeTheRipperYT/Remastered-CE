#ifndef RCE_WEATHER_TRANSITION_HLSL
#define RCE_WEATHER_TRANSITION_HLSL
// Registered through the native shader parameter registry. Zero/default state
// follows CE rendering exactly, including all custom/historical battles.
cbuffer rce_weather_shared {
 float4 g_rce_weather_surface; // enabled, wet fraction, snow fraction, blend
 float4 g_rce_weather_old_shape; // scale, threshold, smoothness, reserved
 float4 g_rce_weather_new_shape;
 float4 g_rce_weather_old_material; // roughness, puddle roughness, metalness, wet
 float4 g_rce_weather_new_material;
 float4 g_rce_weather_old_range; // min distance, max distance, colour burn
 float4 g_rce_weather_new_range;
};
bool rce_weather_managed(){return g_rce_weather_surface.x>0.5f;}
bool rce_weather_fading(){return g_rce_weather_surface.x>0.5f && g_rce_weather_surface.x<1.5f;}
float rce_weather_snow(){return rce_weather_fading()?saturate(g_rce_weather_surface.z):1.0f;}
float3 rce_puddle_material(float3 original){return rce_weather_managed()?g_rce_weather_old_material.xyz:original;}
float3 rce_puddle_range(float3 original){return rce_weather_managed()?g_rce_weather_old_range.xyz:original;}
float rce_puddle_mix(float oldValue,float newValue,float slope,bool grass=false){
 float threshold=g_rce_weather_old_shape.y+(grass?g_rce_weather_old_shape.w:0);
 float soft=max(g_rce_weather_old_shape.z,0.0001f);
 return smoothstep(threshold-soft,threshold+soft,oldValue*pow(slope,8))*g_rce_weather_old_material.w;
}
float rce_precipitation_visibility(float4 seed){
 if(!rce_weather_managed())return 1.0f;
 float coverage=saturate(g_rce_weather_old_range.w);
 float rank=0.05f+0.9f*frac(sin(dot(seed.xy,float2(12.9898f,78.233f)))*43758.5453f);
 return smoothstep(rank-0.05f,rank+0.05f,coverage);
}
#endif
