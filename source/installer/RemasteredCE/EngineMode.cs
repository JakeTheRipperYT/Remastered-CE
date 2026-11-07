using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;

namespace RemasteredCE;

public static class EngineMode
{
    public const string Record = "sim-turns-state.json";
    public const string Engine = "CE8.dll";
    public const string Bootstrap = "RemasteredCE_Sim8.exe";
    public const string Data = "data/data.sim8";

    public static bool Available(string game)
    {
        string root = Path.Combine(game, GameLayout.Folder);
        return File.Exists(Path.Combine(root, Record)) &&
            File.Exists(Path.Combine(root, Engine)) &&
            File.Exists(Path.Combine(root, Bootstrap)) &&
            File.Exists(Path.Combine(root, Data));
    }

    public static string[] Arguments(bool simultaneous)
    {
        return simultaneous ? new[] { "--direct", "--wait", "--sim-turns" }
            : new[] { "--direct", "--wait" };
    }

    public static void Verify(string game, bool simultaneous)
    {
        if (!simultaneous) return;
        if (!Available(game))
            throw new IOException("The 8-player simultaneous-turns files are missing. Install the matching Sim Turns build before selecting this mode.");
        string root = Path.Combine(game, GameLayout.Folder);
        Dictionary<string, object> record = J.Parse(File.ReadAllText(Path.Combine(root, Record)));
        if (J.N(record, "schema") != 1 ||
            Mods.Hash(Path.Combine(root, "CE.dll")) != J.S(record, "normalEngineSha256"))
            throw new IOException("This Sim Turns build does not match the installed Remastered CE engine. Install a matching build before playing.");
        foreach (var item in new[] {
            Tuple.Create(Engine, "engineSha256"),
            Tuple.Create(Bootstrap, "bootstrapSha256"),
            Tuple.Create(Data, "dataSha256") })
        {
            if (Mods.Hash(Path.Combine(root, item.Item1)) != J.S(record, item.Item2))
                throw new IOException("An 8-player simultaneous-turns file differs from the verified build: " + item.Item1);
        }
    }

    public static void Stage(Release release, string stage, Dictionary<string, object> state, CancellationToken cancel, string verifiedDataSource = null)
    {
        if (release.SimTurns == null) return;
        Dictionary<string, object> recipe = release.SimTurns;
        var engine = J.Obj(recipe["engine"]);
        byte[] normal = File.ReadAllBytes(Path.Combine(stage, "CE.dll"));
        if (RemasteredCE.Engine.Hash(normal) != J.S(engine, "sourceSha256"))
            throw new InvalidDataException("Sim Turns recipe does not preserve this normal engine build.");
        int length = checked((int)J.N(engine, "length"));
        if (length < normal.Length || length > 128 * 1024 * 1024)
            throw new InvalidDataException("Invalid alternate engine size.");
        byte[] alternate = new byte[length];
        Buffer.BlockCopy(normal, 0, alternate, 0, normal.Length);
        foreach (object value in J.Arr(engine["writes"]))
        {
            var write = J.Obj(value);
            int offset = checked((int)J.N(write, "offset"));
            byte[] before = J.B(write, "before"), after = J.B(write, "data");
            if (before.Length != after.Length || offset < 0 || offset > normal.Length - before.Length ||
                !normal.Skip(offset).Take(before.Length).SequenceEqual(before))
                throw new InvalidDataException("Alternate engine patch guard failed.");
            Buffer.BlockCopy(after, 0, alternate, offset, after.Length);
        }
        byte[] append = J.B(engine, "append");
        if (normal.Length + append.Length != alternate.Length)
            throw new InvalidDataException("Invalid alternate engine append.");
        Buffer.BlockCopy(append, 0, alternate, normal.Length, append.Length);
        if (RemasteredCE.Engine.Hash(alternate) != J.S(engine, "sha256"))
            throw new InvalidDataException("Alternate engine output verification failed.");
        File.WriteAllBytes(Path.Combine(stage, Engine), alternate);

        var data = J.Obj(recipe["data"]);
        string source = verifiedDataSource ?? Path.Combine(stage, "data/data.pack");
        if (Mods.Hash(source) != J.S(data, "sourceSha256"))
            throw new InvalidDataException("Sim Turns UI recipe does not match the normal data pack.");
        using (var input = File.OpenRead(source))
        using (var output = File.Create(Path.Combine(stage, Data)))
        {
            byte[] prefix = J.B(data, "prefix");
            output.Write(prefix, 0, prefix.Length);
            long offset = J.N(data, "sourcePayloadOffset");
            if (offset < 32 || offset > input.Length) throw new InvalidDataException("Invalid UI recipe source offset.");
            input.Position = offset;
            byte[] buffer = new byte[4 * 1024 * 1024]; int count;
            while ((count = input.Read(buffer, 0, buffer.Length)) != 0)
            {
                cancel.ThrowIfCancellationRequested();
                output.Write(buffer, 0, count);
            }
            byte[] tail = J.B(data, "tail"); output.Write(tail, 0, tail.Length);
            if (output.Length != J.N(data, "length")) throw new InvalidDataException("UI recipe length mismatch.");
            output.Flush(true);
        }
        if (Mods.Hash(Path.Combine(stage, Data)) != J.S(data, "sha256"))
            throw new InvalidDataException("Alternate UI output verification failed.");
        byte[] bootstrap = File.ReadAllBytes(Path.Combine(stage, "shogun2_complete_edition.exe"));
        if (!bootstrap.Skip(58872).Take(7).SequenceEqual(Encoding.ASCII.GetBytes("CE.dll\0")))
            throw new InvalidDataException("Unsupported alternate bootstrap import layout.");
        Array.Clear(bootstrap, 58872, 21);
        byte[] name = Encoding.ASCII.GetBytes("CE8.dll\0");
        Buffer.BlockCopy(name, 0, bootstrap, 58872, name.Length);
        var record = J.Obj(recipe["record"]);
        if (RemasteredCE.Engine.Hash(bootstrap) != J.S(record, "bootstrapSha256"))
            throw new InvalidDataException("Alternate bootstrap verification failed.");
        File.WriteAllBytes(Path.Combine(stage, Bootstrap), bootstrap);
        File.WriteAllText(Path.Combine(stage, Record), J.Json().Serialize(record));
        File.WriteAllText(Path.Combine(stage, "SIM_TURNS_LICENSE.txt"), J.S(recipe, "attribution"));
        state["simTurnsStateSha256"] = Mods.Hash(Path.Combine(stage, Record));
        state["simTurnsLicenseSha256"] = Mods.Hash(Path.Combine(stage, "SIM_TURNS_LICENSE.txt"));
    }

    public static IEnumerable<string> OwnedFiles(string root, Dictionary<string, object> state)
    {
        if (!state.ContainsKey("simTurnsStateSha256")) yield break;
        if (Mods.Hash(Path.Combine(root, Record)) != J.S(state, "simTurnsStateSha256"))
            throw new IOException("The Sim Turns ownership record was edited; nothing was removed.");
        var record = J.Parse(File.ReadAllText(Path.Combine(root, Record)));
        foreach (var item in new[] {
            Tuple.Create(Engine, J.S(record, "engineSha256")),
            Tuple.Create(Bootstrap, J.S(record, "bootstrapSha256")),
            Tuple.Create(Data, J.S(record, "dataSha256")),
            Tuple.Create("SIM_TURNS_LICENSE.txt", J.S(state, "simTurnsLicenseSha256")) })
        {
            string file = RemasteredCE.Engine.Under(root, item.Item1);
            if (Mods.Hash(file) != item.Item2) throw new IOException("A Sim Turns file was edited; nothing was removed: " + item.Item1);
            yield return file;
        }
        yield return Path.Combine(root, Record);
    }
}
