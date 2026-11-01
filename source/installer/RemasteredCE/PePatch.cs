using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

namespace RemasteredCE;

public sealed class PePatch
{
	private sealed class Info
	{
		public int Nt;

		public int Opt;

		public int Count;

		public int Table;

		public int FileAlign;

		public int SectionAlign;

		public int[] Sections;

		public Info(byte[] b)
		{
			Nt = (int)U32(b, 60);
			Opt = Nt + 24;
			Count = U16(b, Nt + 6);
			Table = Opt + U16(b, Nt + 20);
			FileAlign = (int)U32(b, Opt + 36);
			SectionAlign = (int)U32(b, Opt + 32);
			Sections = (from i in Enumerable.Range(0, Count)
				select Table + i * 40).ToArray();
		}

		public int Offset(byte[] b, int rva)
		{
			int[] sections = Sections;
			foreach (int num in sections)
			{
				int num2 = (int)U32(b, num + 12);
				int num3 = Math.Max((int)U32(b, num + 8), (int)U32(b, num + 16));
				if (rva >= num2 && rva < num2 + num3)
				{
					return checked((int)U32(b, num + 20) + rva - num2);
				}
			}
			if (rva < (int)U32(b, Opt + 60))
			{
				return rva;
			}
			throw new InvalidDataException("Invalid PE address.");
		}
	}

	private static ushort U16(byte[] b, int o)
	{
		return BitConverter.ToUInt16(b, o);
	}

	private static uint U32(byte[] b, int o)
	{
		return BitConverter.ToUInt32(b, o);
	}

	private static void W16(byte[] b, int o, int v)
	{
		Buffer.BlockCopy(BitConverter.GetBytes((ushort)v), 0, b, o, 2);
	}

	private static void W32(byte[] b, int o, long v)
	{
		Buffer.BlockCopy(BitConverter.GetBytes((uint)v), 0, b, o, 4);
	}

	private static int Align(int v, int a)
	{
		checked
		{
			return unchecked(checked(v + a - 1) / a) * a;
		}
	}

	public static byte[] Inject(byte[] input, Dictionary<string, object> helper)
	{
		byte[] b = (byte[])input.Clone();
		Info info = new Info(b);
		int num = (int)J.N(helper, "rva");
		int num2 = Align(info.Sections.Max((int s) => checked((int)U32(b, s + 12) + (int)U32(b, s + 8))), info.SectionAlign);
		int num3 = num2 - num;
		byte[] array = J.B(helper, "payload");
		object[] array2 = J.Arr(helper["fixups"]);
		for (int num4 = 0; num4 < array2.Length; num4++)
		{
			int o = Convert.ToInt32(array2[num4]);
			W32(array, o, (int)U32(array, o) - num3);
		}
		int num5 = info.Opt + 112 + 24;
		int rva = (int)U32(b, num5);
		int num6 = (int)U32(b, num5 + 4);
		int srcOffset = info.Offset(b, rva);
		int num7 = Align(array.Length, 4);
		object[] array3 = J.Arr(helper["unwind"]);
		byte[] array4 = new byte[num7 + num6 + array3.Length * 12];
		Buffer.BlockCopy(array, 0, array4, 0, array.Length);
		Buffer.BlockCopy(b, srcOffset, array4, num7, num6);
		int num8 = num7 + num6;
		array2 = array3;
		for (int num4 = 0; num4 < array2.Length; num4++)
		{
			object[] array5 = J.Arr(array2[num4]);
			for (int num9 = 0; num9 < 3; num9++)
			{
				W32(array4, num8 + num9 * 4, Convert.ToInt32(array5[num9]) + num3);
			}
			num8 += 12;
		}
		int writable = helper.ContainsKey("writableDataOffset") ? (int)J.N(helper, "writableDataOffset") : 0;
        if (writable != 0 && (writable <= 0 || writable >= array.Length || writable % info.SectionAlign != 0))
            throw new InvalidDataException("Invalid writable helper data boundary.");
        int addedSections = writable == 0 ? 1 : 2;
        int num10 = info.Table + info.Count * 40;
		int num11 = info.Sections.Min((int s) => (int)U32(b, s + 20));
		if (num10 + 40 * addedSections > num11)
		{
			int fileAlign = info.FileAlign;
			byte[] array6 = new byte[b.Length + fileAlign];
			Buffer.BlockCopy(b, 0, array6, 0, num11);
			Buffer.BlockCopy(b, num11, array6, num11 + fileAlign, b.Length - num11);
			int num12 = info.Opt + 112 + 48;
			int num13 = (int)U32(b, num12);
			int num14 = (int)U32(b, num12 + 4);
			if (num13 != 0)
			{
				int num15 = info.Offset(b, num13);
				for (int num16 = 0; num16 + 28 <= num14; num16 += 28)
				{
					if (U32(b, num15 + num16 + 24) != 0)
					{
						W32(array6, num15 + num16 + 24 + fileAlign, U32(b, num15 + num16 + 24) + fileAlign);
					}
				}
			}
			int[] sections = info.Sections;
			foreach (int num17 in sections)
			{
				W32(array6, num17 + 20, U32(b, num17 + 20) + fileAlign);
			}
			int o2 = info.Opt + 112 + 32;
			if (U32(b, o2) != 0)
			{
				W32(array6, o2, U32(b, o2) + fileAlign);
			}
			W32(array6, info.Opt + 60, U32(b, info.Opt + 60) + fileAlign);
			b = array6;
		}
		info = new Info(b);
		int num18 = info.Sections.First((int s) => Encoding.ASCII.GetString(b, s, 5) == ".text");
		int num19 = (int)U32(b, num18 + 20);
		int num20 = (int)U32(b, num18 + 12);
		int num21 = (int)U32(b, num18 + 16);
		int num22 = num2 + (int)J.N(helper, "entry") - num;
		int num23 = 0;
		for (int num24 = 0; num24 + 6 < num21; num24++)
		{
			int num25 = num19 + num24;
			if (b[num25] == byte.MaxValue && b[num25 + 1] == 21)
			{
				int num26 = num20 + num24;
				if (num26 + 6 + (int)U32(b, num25 + 2) == 34972976)
				{
					b[num25] = 232;
					W32(b, num25 + 1, num22 - (num26 + 5));
					b[num25 + 5] = 144;
					num23++;
				}
			}
		}
		if (num23 != 25)
		{
			throw new InvalidDataException("Unsupported engine file-open layout.");
		}
		int num27 = Align(b.Length, info.FileAlign);
		int num28 = Align(array4.Length, info.FileAlign);
		Array.Resize(ref b, num27 + num28);
		Buffer.BlockCopy(array4, 0, b, num27, array4.Length);
		byte[] bytes = Encoding.ASCII.GetBytes(".cepath\0");
		Buffer.BlockCopy(bytes, 0, b, num10, bytes.Length);
		W32(b, num10 + 8, writable == 0 ? array4.Length : writable);
		W32(b, num10 + 12, num2);
		W32(b, num10 + 16, writable == 0 ? num28 : writable);
		W32(b, num10 + 20, num27);
		W32(b, num10 + 36, 1610612768L);
		if (writable != 0) {
            int dataHeader = num10 + 40;
            Buffer.BlockCopy(Encoding.ASCII.GetBytes(".rcedata"), 0, b, dataHeader, 8);
            W32(b, dataHeader + 8, array4.Length - writable);
            W32(b, dataHeader + 12, num2 + writable);
            W32(b, dataHeader + 16, num28 - writable);
            W32(b, dataHeader + 20, num27 + writable);
            W32(b, dataHeader + 36, 0xc0000040L);
            W32(b, info.Opt + 8, U32(b, info.Opt + 8) + num28 - writable);
        }
        W16(b, info.Nt + 6, info.Count + addedSections);
		W32(b, info.Opt + 56, Align(num2 + array4.Length, info.SectionAlign));
		W32(b, info.Opt + 4, U32(b, info.Opt + 4) + (writable == 0 ? num28 : writable));
		W32(b, num5, num2 + num7);
		W32(b, num5 + 4, num6 + array3.Length * 12);
		int o3 = info.Opt + 64;
		W32(b, o3, 0L);
		ulong num29 = 0uL;
		for (int num30 = 0; num30 < b.Length; num30 += 2)
		{
			num29 += (uint)(b[num30] | (((num30 + 1 < b.Length) ? b[num30 + 1] : 0) << 8));
			num29 = (num29 & 0xFFFF) + (num29 >> 16);
		}
		num29 = (num29 & 0xFFFF) + (num29 >> 16);
		W32(b, o3, (long)(num29 & 0xFFFF) + (long)b.Length);
		return b;
	}
}
