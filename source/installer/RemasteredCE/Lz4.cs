using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace RemasteredCE;

public static class Lz4
{
	private static bool ready;

	[DllImport("kernel32", CharSet = CharSet.Unicode, SetLastError = true)]
	private static extern IntPtr LoadLibraryW(string p);

	[DllImport("lz4.dll", CallingConvention = CallingConvention.Cdecl)]
	private static extern int LZ4_decompress_safe(byte[] src, byte[] dst, int count, int capacity);

	[DllImport("lz4.dll", CallingConvention = CallingConvention.Cdecl)]
	private static extern int LZ4_compressBound(int n);

	[DllImport("lz4.dll", CallingConvention = CallingConvention.Cdecl)]
	private static extern int LZ4_compress_default(byte[] src, byte[] dst, int n, int capacity);

	[DllImport("lz4.dll", CallingConvention = CallingConvention.Cdecl)]
	private static extern int LZ4_compress_HC(byte[] src, byte[] dst, int n, int capacity, int level);

	public static void Init()
	{
		if (!ready)
		{
			byte[] array = Release.Resource("lz4");
			string text = Path.Combine(Path.GetTempPath(), "RemasteredCE-tools-" + Engine.Hash(array).Substring(0, 16));
			Directory.CreateDirectory(text);
			string text2 = Path.Combine(text, "lz4.dll");
			if (!File.Exists(text2) || Engine.FileHash(text2) != Engine.Hash(array))
			{
				File.WriteAllBytes(text2, array);
			}
			if (LoadLibraryW(text2) == IntPtr.Zero)
			{
				throw new Win32Exception(Marshal.GetLastWin32Error());
			}
			ready = true;
		}
	}

	public static byte[] Decode(byte[] src, int size)
	{
		Init();
		if (size < 0 || size > 268435456)
		{
			throw new InvalidDataException("Asset size exceeds limit.");
		}
		byte[] array = new byte[size];
		if (LZ4_decompress_safe(src, array, src.Length, size) != size)
		{
			throw new InvalidDataException("Asset decompression failed.");
		}
		return array;
	}

	public static byte[] Encode(byte[] data, string codec, int level)
	{
		if (codec == "raw")
		{
			return data;
		}
		Init();
		byte[] array = new byte[LZ4_compressBound(data.Length)];
		int num = ((codec == "fast") ? LZ4_compress_default(data, array, data.Length, array.Length) : LZ4_compress_HC(data, array, data.Length, array.Length, level));
		if (num <= 0)
		{
			throw new InvalidDataException("Asset compression failed.");
		}
		Array.Resize(ref array, num);
		return array;
	}
}
