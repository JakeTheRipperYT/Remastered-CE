using System;
using System.IO;
class Fixture {static int Main(string[] args){File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"resume.txt"),String.Join(" ",args));return 0;}}
