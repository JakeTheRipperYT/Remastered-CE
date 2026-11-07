using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace RemasteredCE;

internal static class EngineModeTests
{
    public static void Run(List<string> results)
    {
        string game = Path.Combine(Path.GetTempPath(), "RCE-mode-test-" + Guid.NewGuid().ToString("N"));
        string root = Path.Combine(game, GameLayout.Folder);
        Directory.CreateDirectory(Path.Combine(root, "data"));
        EngineMode.Verify(game, false);
        if (EngineMode.Available(game)) throw new Exception("Missing Sim Turns mode reported available.");
        bool refused = false;
        try { EngineMode.Verify(game, true); } catch (IOException) { refused = true; }
        if (!refused) throw new Exception("Missing alternate engine silently accepted.");
        if (EngineMode.Arguments(false).Contains("--sim-turns") || !EngineMode.Arguments(true).Contains("--sim-turns"))
            throw new Exception("Engine checkbox argument routing failed.");
        results.Add("PASS: normal mode needs no alternate files; Sim Turns requires its own bundle and flag");
        File.WriteAllText(Path.Combine(root, "CE.dll"), "normal engine");
        File.WriteAllText(Path.Combine(root, EngineMode.Engine), "alternate engine");
        File.WriteAllText(Path.Combine(root, EngineMode.Bootstrap), "alternate bootstrap");
        File.WriteAllText(Path.Combine(root, EngineMode.Data), "alternate UI");
        var record = new Dictionary<string, object> {
            { "schema", 1 }, { "normalEngineSha256", Mods.Hash(Path.Combine(root, "CE.dll")) },
            { "engineSha256", Mods.Hash(Path.Combine(root, EngineMode.Engine)) },
            { "bootstrapSha256", Mods.Hash(Path.Combine(root, EngineMode.Bootstrap)) },
            { "dataSha256", Mods.Hash(Path.Combine(root, EngineMode.Data)) } };
        File.WriteAllText(Path.Combine(root, EngineMode.Record), J.Json().Serialize(record));
        EngineMode.Verify(game, true);
        foreach (string file in new[] { "CE.dll", EngineMode.Engine, EngineMode.Bootstrap, EngineMode.Data })
        {
            string path = Path.Combine(root, file); byte[] original = File.ReadAllBytes(path);
            File.AppendAllText(path, "edited"); refused = false;
            try { EngineMode.Verify(game, true); } catch (IOException) { refused = true; }
            File.WriteAllBytes(path, original);
            if (!refused) throw new Exception("Mismatched mode file accepted: " + file);
        }
        results.Add("PASS: Sim Turns rejects edited alternate files and a different normal-engine baseline");
        var profile = new ModProfile { UseSimTurns = true, UseExistingScript = true };
        var restored = J.Json().Deserialize<ModProfile>(J.Json().Serialize(profile));
        if (!restored.UseSimTurns || !restored.UseExistingScript)
            throw new Exception("Engine mode did not round-trip with existing script preference.");
        results.Add("PASS: engine selection persists independently of the existing-script option");
    }
}
