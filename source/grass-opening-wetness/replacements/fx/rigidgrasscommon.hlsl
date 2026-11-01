#include "util.hlsl"
#include "high_dynamic_range.hlsl"
#include "photoshop_blend_modes.hlsl"
#include "camera.hlsl"
#include "gBuffer.hlsl"
#include "fog.hlsl"
#include "wind.hlsl"
#include "RigidUtil.hlsl"
#include "vaf_byte_4.hlsl"
#include "RigidStandardFragments.hlsl"
////////////////////////////////////////////////////////////////////////////////////////////////////
//	Textures
////////////////////////////////////////////////////////////////////////////////////////////////////


////////////////////////////////////////////////////////////////////////////////////////////////////
//	Inputs/Outputs
////////////////////////////////////////////////////////////////////////////////////////////////////

struct VS_INPUT
{
	half4	position			: POSITION0;
	float2	texture_uv			: TEXCOORD0;
	float4	normal				: NORMAL0;		// Access with VAF_BYTE_4() fn
	float4	face_normal			: NORMAL1;		// Access with VAF_BYTE_4() fn
	float4	colour				: COLOR;		// Access with VAF_BYTE_4() fn

	float4 transform_matrix_row0 : TEXCOORD1;
	float4 transform_matrix_row1 : TEXCOORD2;
	float4 transform_matrix_row2 : TEXCOORD3;
};

struct VS_OUTPUT
{
	float4	position					: POSITION;
	float4	colour						: COLOR0;
	float4	world_position				: TEXCOORD0;
	float2	texture_uv					: TEXCOORD1;
	float3	normal						: TEXCOORD2;
	float4	clip_position				: TEXCOORD3;
	float3	face_normal					: TEXCOORD4;
	float4	camera_direction_distance	: TEXCOORD5;
    float4	prev_world_position			: TEXCOORD6;	//MTB-cyryl.matuszewski: velocity buffer
};

struct VS_OUTPUT_DEPTH
{
	float4	position					: POSITION;
	float4	world_position				: TEXCOORD0; 
	float2	texture_uv					: TEXCOORD1; 
	float3	face_normal					: TEXCOORD2; 
	float4	clip_position				: TEXCOORD3; 
	float4	camera_direction_distance	: TEXCOORD4;
};



////////////////////////////////////////////////////////////////////////////////////////////////////
//	Constants
////////////////////////////////////////////////////////////////////////////////////////////////////

static const float grass_alpha_ref_high = (70.0f/255.0f);
static const float grass_alpha_ref_low = (10.0f/255.0f);

cbuffer grass_PS
{
	const float inv_lod_distance = 1/100.0f;
	// MTB-cyryl.matuszewski: puddles
    const float4 g_puddle_scale_sratio_threshold_smoothness;
    const float2 g_puddle_cull_offset;    
};

// MTB-cyryl.matuszewski: puddles
Texture2D t_puddle_map;
SamplerState s_puddle_map;


////////////////////////////////////////////////////////////////////////////////////////////////////
//	Vertex Shaders
////////////////////////////////////////////////////////////////////////////////////////////////////


//MTB-cyryl.matuszewski: velocity buffer
float4 common_world_pos(in VS_INPUT input, in float time, in float4x4 inv_view_mat, in float3 cam_pos, out float3 wind_normal, uniform SHADER_MODEL shader_model)
{
	float4x4 world = float4x4(input.transform_matrix_row0, input.transform_matrix_row1, input.transform_matrix_row2, 0.0f, 0.0f, 0.0f, 1.0f);
	float4 position = mul(world, input.position);
	
	{
		//MTB-cyryl.matuszewski: copied from 3K
		{
			// We scale grass and push it down to the ground slowly over distance so we will get a nice fadeout on SSAO

			// Distance calculation based on grass center distance
            float3 translation = float3(input.transform_matrix_row0.w, input.transform_matrix_row1.w, input.transform_matrix_row2.w);
            float distance_lerp = saturate((length(translation - cam_pos) * inv_lod_distance));

			// Adjust vertex height
            float3 local_pos = input.position.xyz;
            float lerp_value = lerp(1, 1 - distance_lerp, saturate(input.colour.w));
            local_pos.y = lerp(-0.6f, local_pos.y, lerp_value);
		
			// Offset top of the grass in camera up direction to slightly rotate towards camera
            float3 offset = get_camera_ws_y_axis(inv_view_mat);
			// Make sure the offset doesn't change height
            offset.y = 0;
			// Only offset the top of the grass
            position.xyz += offset * local_pos.y;
        }
		
		float w = (sin(position.x/4 + time) + sin(position.z/4 + time)) * sin(time) * 0.3f;

		const float seed0 = position.z/4;
		const float strengthh = wind_vegetation_hstrength * (0.5f + sin(time + seed0) * sin(time*3)*0.5*wind_vegetation_hstrength);
		const float strengthv = wind_vegetation_vstrength * sin((time+ seed0) * 0.3 ) * cos((time + position.x) * 5);

		float valpha_start = 0.7f;
		float valpha = saturate(1.f-VAF_BYTE_4(input.colour).a - valpha_start) / (1.0f - valpha_start);
        float3 wind_offset = wind_vegetation_multiplier * saturate((1.f-VAF_BYTE_4(input.colour).a)-0.35f) * float3(g_wind_direction.x, 0.0f, g_wind_direction.y) * strengthh * 0.5;
		wind_offset += wind_vegetation_multiplier * valpha * float3( 0.0f, 1.0f, 0.0f) * strengthv*0.7;

		//mtb:mkr- [WAS-923] Distance for wind influence.
        float positionToCameraDist = distance(position, camera_position.xyz);
		//Just to be sure that g_Wind_Influence_offfset is not bigger and different from _distance_value 
        float wind_influence_offset = min(g_wind_influence_max_distance - 1.f, g_wind_influence_offset);
		
        float wind_influence = saturate((positionToCameraDist - wind_influence_offset) / (g_wind_influence_max_distance - wind_influence_offset));
		wind_offset = lerp(wind_offset, float3(0.f,0.f,0.f), wind_influence);
		//mtb:mkr- [WAS-923] Distance for wind influence.

		position.xyz += wind_offset;

		wind_normal = wind_offset * w;
	}

	return position;
}

VS_OUTPUT vs30_main_grass_common( in VS_INPUT input, uniform SHADER_MODEL shader_model )
{
	VS_OUTPUT output;

	float4x4 world = float4x4(input.transform_matrix_row0, input.transform_matrix_row1, input.transform_matrix_row2, 0.0f, 0.0f, 0.0f, 1.0f);

	float3 wind_normal;
	//MTB-cyryl.matuszewski: velocity buffer
    float4 position = common_world_pos(input, time_in_sec, inv_view, camera_position, wind_normal, shader_model);
    float3 unused_wind_normal;
    float4 prev_position = common_world_pos(input, prev_time_in_sec, prev_inv_view, prev_camera_position, unused_wind_normal, shader_model);

	output.position = mul(position, view_projection);
	output.colour = VAF_BYTE_4(input.colour);
	// MTB-cyryl.matuszewski: BEGIN hack for grass normal from 3K
	// For now we are going to use the rotation of the face normal around the Y axis, slightly pointing upwards
	float3 normal = unpack_normal(VAF_BYTE_4(input.face_normal).xyz);
	normal = normalize(normal.xyz * float3(1, 0, 1) + float3(0, 15.0f, 0));
	output.normal = normalize(mul((float3x3) world, normal) + wind_normal.xyz).xyz;
	//output.normal = normalize(mul((float3x3) world, unpack_normal(VAF_BYTE_4(input.normal).xyz)) + wind_normal);
	// MTB-cyryl.matuszewski: END
	output.texture_uv = input.texture_uv;
	output.world_position = position;
    output.prev_world_position = prev_position;
	output.clip_position = output.position;
	//MTB-cyryl.matuszewski: END
	
	//clip instances that are on puddles
	[branch]
    if (g_puddle_cull_offset.x > 0.0f)
	{		
        float4 worldPos = mul(world, input.position); //no wind or camera offseting
        float2 grid_uv = worldPos.xz / 4096.0f + 0.5f;
        float4 params = g_puddle_scale_sratio_threshold_smoothness + float4(0, 0, g_puddle_cull_offset.y, 0);
        float puddle_factor = calculate_puddle_factor_vs(t_puddle_map, s_puddle_map, grid_uv, params, 1.0f);
        if (puddle_factor >= g_puddle_cull_offset.x)//cull
        {
            float nan = asfloat(int(0xFFC00000u));
            output.position = float4(nan, nan, nan, nan);
        }
    }

	float3 face_normal = mul((float3x3)world, unpack_normal(VAF_BYTE_4(input.face_normal).xyz) ).xyz;

	float3 camera_direction = float3(view[0].z, view[1].z, view[2].z);
	
	output.face_normal = mul(world, float4(normalize((VAF_BYTE_4(input.face_normal).xyz*2-1)), 0)).xyz;
	
	float3 world_to_camera = output.world_position.xyz - camera_position.xyz;
	output.camera_direction_distance = float4(normalize(world_to_camera), length(world_to_camera));
	
	return output;
}

VS_OUTPUT_DEPTH vs30_depth_grass_common( in VS_INPUT input, uniform SHADER_MODEL shader_model )
{
	VS_OUTPUT_DEPTH output;

	float4x4 world = float4x4(input.transform_matrix_row0, input.transform_matrix_row1, input.transform_matrix_row2, 0.0f, 0.0f, 0.0f, 1.0f);

	float3 wind_normal;
	//MTB-cyryl.matuszewski: velocity buffer
    float4 position = common_world_pos(input, time_in_sec, inv_view, camera_position, wind_normal, shader_model);

	output.position = mul(position, view_projection);
	output.texture_uv = input.texture_uv;
	output.world_position = position;
	output.clip_position = output.position;

	float3 face_normal = mul((float3x3)world, unpack_normal(VAF_BYTE_4(input.face_normal).xyz) ).xyz;

	float3 camera_direction = float3(view[0].z, view[1].z, view[2].z);
	
	output.face_normal = mul(world, float4(normalize((VAF_BYTE_4(input.face_normal).xyz*2-1)), 0)).xyz;
	
	float3 world_to_camera = output.world_position.xyz - camera_position.xyz;
	output.camera_direction_distance = float4(normalize(world_to_camera), length(world_to_camera));
	
	return output;
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//	Pixel Shaders
////////////////////////////////////////////////////////////////////////////////////////////////////

// MTB-anton.korzhuk [WAS-107] - use new pipeline

/* Deferred */

//MTB-cyryl.matuszewski: a better jitter sampling (TODO: use Load?)
float load_jitter(const uint2 vpos)
{
    uint2 dither_texture_dims = { 64, 64 };//we are using 64x64 texture
    uint2 dither_load_coords = vpos % dither_texture_dims;
    const float dissolve_value = tex2D(s_dissolve_map, float2(dither_load_coords)/64.0f).x;
	
    return dissolve_value;
}

R2_5_StandardLightingModelMaterial_For_GBuffer common_lighting(
	VS_OUTPUT input, 
	uniform SHADER_MODEL shader_model,
	uniform bool reflection,
    uniform bool u_wet
)
{
	float alpha;
	float3 N;
	float4 base_colour;
	float roughness;
	float metalness;
	float occlusion;

	COMMON_LIGHTING_INPUTS light_ins;
	light_ins.position = input.position;
	light_ins.world_position = input.world_position;
	light_ins.texture_uv = input.texture_uv;
	light_ins.normal = float4(input.normal, input.texture_uv.x);
	light_ins.tangent = float4(0.0, 0.0, 0.0, input.texture_uv.y);
	light_ins.colour = float4(input.colour.rgb, 1.0); // because they for some reason originally packed specular in vertex color alpha
	light_ins.clip_position = input.clip_position;
	light_ins.bitangent = float4(0.0, 0.0, 0.0, 0.0);
	light_ins.mesh_data = float4(0.0, 0.0, 0.0, 1000.0);
	light_ins.proj_uv = float3(0.0, 0.0, 0.0);

	COMMON_LIGHTING_EX_INPUTS ex_inputs;
	ex_inputs.texture_alpha_test = false;
	ex_inputs.apply_shroud = false;
	ex_inputs.disable_normal_map = true;
	ex_inputs.disable_dissolve = true;
	ex_inputs.use_legacy_maps = false;

	common_lighting_ex(light_ins, shader_model, alpha, base_colour, metalness, roughness, occlusion, N, ex_inputs);

	if (reflection)
	{
		N = -N;
	}

    // Matte grass base, before the separately controlled wet coating.
    roughness = max(roughness, 0.9f);
    metalness = 0.0f;
    // Match the immutable opening-ground wetness used by terrain puddles.
    // A later rain/clear shader permutation cannot change the ground policy.
    bool grass_ground_wet = rce_weather_managed()
        ? (g_rce_weather_old_material.w > 0.5f) : u_wet;
    if (grass_ground_wet)
        roughness *= g_rain_vegetation_roughness_multiplier;

	float d0 = 1.0;// dot(normalize(input.face_normal), input.camera_direction_distance.xyz);
	
	//MTB-cyryl.matuszewski: a better jitter sampling
	const float jitter=load_jitter(input.texture_uv*64);
	const float dissolve_factor = (1.0f - saturate(input.camera_direction_distance.w * inv_lod_distance));
	const float clipf_1 = dissolve_factor * jitter;
	const float clipf_2 = alpha * abs(d0) * jitter; 
	clip(step(0.25, clipf_1) * step(0.25,clipf_2) - 0.001f);	// clip if either clipf_1 or clipf_2 is < 0.25
		
    // Store flags
	// MTB-anton.korzhuk [WAS-2421] [WAS-2520]: add IS_FOLIAGE
    const uint bit_flags = LIGHTING_MODEL_STANDARD | TAA_VELOCITY_PIXEL | IS_FOLIAGE;
	
	return R2_5_create_standard_lighting_material_for_gbuffer(base_colour.rgb, N, roughness, metalness, occlusion, bit_flags);
}

//MTB-cyryl.matuszewski: velocity buffer
GBUFFER_VELOCITY_OUTPUT ps30_gbuffer_grass_common(
	VS_OUTPUT input, 
	uniform SHADER_MODEL shader_model,
	uniform bool reflection,
    uniform bool u_wet
)
{
    GBUFFER_VELOCITY_OUTPUT output;

    (GBUFFER_OUTPUT) output = write_gBuffer_standard_lighting_material(common_lighting(input, shader_model, reflection, u_wet));
    output.velocity = calc_motion_vector(input.position.xy, input.prev_world_position.xyz);
    output.reactivity_mask = VAF_BYTE_4(input.colour).a; // MTB-anton.korzhuk [WAS-3257]: reactivity mask for temporal effects

    return output;
}

/* Forward */


float4 ps30_main_grass_common( in VS_OUTPUT input, uniform SHADER_MODEL shader_model, uniform bool reflection, uniform bool u_wet )
{
	float alpha;
	R2_5_StandardLightingModelMaterial_For_GBuffer lighting_material_pre_gbuffer = common_lighting(
		input,
		shader_model,
		reflection,
		u_wet
	);
	R2_5_StandardLightingModelMaterial_For_Lighting lighting_material = R2_5_get_slm_for_lighting(lighting_material_pre_gbuffer);
	float3 colour = standard_lighting_model_directional_light( sun_colour, sun_direction, normalize(input.world_position.xyz - camera_position),
		lighting_material, input.world_position.xyz );

	if (!reflection)
	{
		// Fog
        colour = apply_fog(colour, input.position.xy, input.world_position.xyz, shader_model == SHADER_MODEL_3_LQ);
    }
	
	// H.D.R.
	return float4( encode_hdr( colour ), 1.0f );
}

void ps30_shadow_grass_common( in VS_OUTPUT_DEPTH input, uniform SHADER_MODEL shader_model )
{
	const float Os = tex2D( s_diffuse_map, input.texture_uv.xy ).a;

	// Alpha
	if (shader_model == SHADER_MODEL_3_LQ)
	{
		const float grass_alpha_ref = 0.5f;
		clip( Os - grass_alpha_ref );
	}
	else
	{
		float d0 = 1.0; // dot(normalize(input.face_normal), input.camera_direction_distance.xyz);
		const float jitter = saturate( tex2D( s_dissolve_map, input.texture_uv.xy * 10.0f ) ).x ;
		clip(Os * abs(d0) * jitter - 0.25f);
	}
}
