using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;

namespace RemasteredCE;

public static class InstallerLauncher
{
    // Only the signed 0.1.25 package this launcher was built and tested with
    // receives this installer-side launcher update. Future packages retain
    // their own authenticated launcher payload.
    public const string PackageHash = "2f24997b7ddd4bb266f8a4f2e65b48084b09852ef51f9f3b3399bcc62f3f0c52";
    public const string OriginalLauncherHash = "ff77839ebb0495bb7e0906364aa078ae882d593eeb03abd60a2bed4ee89f023e";

    public static byte[] Select(Release release)
    {
        if (release.ModManager == null) return null;
        if (release.PackageHash != PackageHash || J.S(release.Manifest, "version") != "0.1.25-preview")
            return release.ModManager;
        if (Engine.Hash(release.ModManager) != OriginalLauncherHash)
            throw new InvalidDataException("Unexpected launcher in the pinned 0.1.25 package.");
        return File.ReadAllBytes(Assembly.GetExecutingAssembly().Location);
    }

    public static bool NeedsUpdate(string game, string installedVersion, string availableVersion)
    {
        if (installedVersion != "0.1.25-preview" || availableVersion != installedVersion) return false;
        string record = Engine.Under(game, "RemasteredCE/install-state.json");
        string target = Engine.Under(game, "RemasteredCE/RemasteredCE_Launcher.exe");
        if (!File.Exists(record) || !File.Exists(target)) return false;
        var state = J.Parse(File.ReadAllText(record));
        if (J.S(state, "packageSha256") != PackageHash) return false;
        string owned = J.S(state, "unifiedLauncherSha256");
        if (owned != OriginalLauncherHash && owned != "5257987fc7884a0f514c416a7920f44f807a523fdec1ed2d13a1837828c1ecd0")
            return false;
        if (Engine.FileHash(target) != owned)
            throw new InvalidDataException("The installed launcher differs from its ownership record. Nothing was replaced.");
        return true;
    }

    private static void CheckFile(string path)
    {
        if (File.Exists(path) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("Linked launcher/state files are not supported.");
    }

    private static void Replace(string target, byte[] bytes)
    {
        string temp = target + ".modfix-" + Guid.NewGuid().ToString("N");
        try
        {
            File.WriteAllBytes(temp, bytes);
            File.Replace(temp, target, null);
        }
        finally { if (File.Exists(temp)) File.Delete(temp); }
    }

    public static bool Repair(string game)
    {
        Engine.NoLinks(game);
        Engine.NoLinks(Engine.Under(game, "RemasteredCE"));
        string target = Engine.Under(game, "RemasteredCE/RemasteredCE_Launcher.exe");
        string record = Engine.Under(game, "RemasteredCE/install-state.json");
        string lockPath = Engine.Under(game, ".remastered-install.lock");
        CheckFile(target); CheckFile(record); CheckFile(lockPath);
        Engine.GameClosed();
        using (var installationLock = File.Open(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
        {
            if (!NeedsUpdate(game, "0.1.25-preview", "0.1.25-preview")) return false;
            byte[] previous = File.ReadAllBytes(target);
            byte[] previousState = File.ReadAllBytes(record);
            byte[] updated = File.ReadAllBytes(Assembly.GetExecutingAssembly().Location);
            var state = J.Parse(Encoding.UTF8.GetString(previousState).TrimStart('﻿'));
            if (J.S(state, "version") != "0.1.25-preview") return false;
            state["unifiedLauncherSha256"] = Engine.Hash(updated);
            state["unifiedLauncherBuild"] = "0.1.25-modfix2";
            string backup = Engine.Under(game, "RemasteredCE.launcher-modfix-backup-" + DateTime.UtcNow.ToString("yyyyMMddHHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0,8));
            Directory.CreateDirectory(backup);
            File.WriteAllBytes(Engine.Under(backup, "RemasteredCE_Launcher.exe"), previous);
            File.WriteAllBytes(Engine.Under(backup, "install-state.json"), previousState);
            bool replaced = false;
            try
            {
                Replace(target, updated); replaced = true;
                Replace(record, Encoding.UTF8.GetBytes(J.Json().Serialize(state)));
            }
            catch
            {
                if (replaced) Replace(target, previous);
                throw;
            }
            return true;
        }
    }

    public static void Stage(Release release, string stage, Dictionary<string, object> state)
    {
        byte[] manager = Select(release);
        if (manager == null) return;
        File.WriteAllBytes(Engine.Under(stage, "RemasteredCE_Launcher.exe"), manager);
        File.WriteAllBytes(Engine.Under(stage, "release.rce"), release.PackageBytes);
        state["unifiedLauncherSha256"] = Engine.Hash(manager);
        state["offlineReleaseSha256"] = Engine.Hash(release.PackageBytes);
        if (release.PackageHash == PackageHash)
            state["unifiedLauncherBuild"] = "0.1.25-modfix2";
    }
}
