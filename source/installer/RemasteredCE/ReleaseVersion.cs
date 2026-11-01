using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace RemasteredCE;

public sealed class ReleaseVersion : IComparable<ReleaseVersion>
{
	private readonly int[] numbers;

	private readonly string suffix;

	private ReleaseVersion(int[] n, string s)
	{
		numbers = n;
		suffix = s;
	}

	public static ReleaseVersion Parse(string value)
	{
		Match match = Regex.Match(value ?? "", "^v?(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*))?$");
		if (!match.Success || !int.TryParse(match.Groups[1].Value, out var result) || !int.TryParse(match.Groups[2].Value, out var result2) || !int.TryParse(match.Groups[3].Value, out var result3))
		{
			throw new InvalidDataException("Unrecognized release version: " + value);
		}
		return new ReleaseVersion(new int[3] { result, result2, result3 }, match.Groups[4].Value);
	}

	public int CompareTo(ReleaseVersion other)
	{
		for (int i = 0; i < 3; i++)
		{
			int num = numbers[i].CompareTo(other.numbers[i]);
			if (num != 0)
			{
				return num;
			}
		}
		if (suffix == other.suffix)
		{
			return 0;
		}
		if (suffix.Length == 0)
		{
			return 1;
		}
		if (other.suffix.Length == 0)
		{
			return -1;
		}
		string[] array = suffix.Split('.');
		string[] array2 = other.suffix.Split('.');
		for (int j = 0; j < Math.Min(array.Length, array2.Length); j++)
		{
			if (array[j] == array2[j])
			{
				continue;
			}
			bool flag = array[j].All(char.IsDigit);
			bool flag2 = array2[j].All(char.IsDigit);
			if (flag != flag2)
			{
				if (!flag)
				{
					return 1;
				}
				return -1;
			}
			if (flag)
			{
				int num2 = array[j].Length.CompareTo(array2[j].Length);
				if (num2 != 0)
				{
					return num2;
				}
			}
			return string.CompareOrdinal(array[j], array2[j]);
		}
		return array.Length.CompareTo(array2.Length);
	}
}
