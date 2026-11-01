using System;
using System.Collections.Generic;
using System.Web.Script.Serialization;

namespace RemasteredCE;

public static class J
{
	public static Dictionary<string, object> Obj(object x)
	{
		return (Dictionary<string, object>)x;
	}

	public static object[] Arr(object x)
	{
		return (object[])x;
	}

	public static string S(Dictionary<string, object> d, string k)
	{
		return Convert.ToString(d[k]);
	}

	public static long N(Dictionary<string, object> d, string k)
	{
		return Convert.ToInt64(d[k]);
	}

	public static byte[] B(Dictionary<string, object> d, string k)
	{
		return Convert.FromBase64String(S(d, k));
	}

	public static JavaScriptSerializer Json()
	{
		return new JavaScriptSerializer
		{
			MaxJsonLength = 33554432,
			RecursionLimit = 100
		};
	}

	public static Dictionary<string, object> Parse(string s)
	{
		return Obj(Json().DeserializeObject(s));
	}
}
