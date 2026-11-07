// Native Remastered CE entry: combined UI by default; --direct --wait starts the private game.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>

#define TITLE L"Remastered CE"
#define STEAM_APP_ID L"3846830"

static WCHAR root[MAX_PATH * 4], exe[MAX_PATH * 4], engine[MAX_PATH * 4], data[MAX_PATH * 4], models[MAX_PATH * 4], local_en[MAX_PATH * 4], manager[MAX_PATH * 4], cmd[MAX_PATH * 8];
// Static so no CRT memset is needed to zero them.
static STARTUPINFOW startup;
static PROCESS_INFORMATION process;

static void fail(const WCHAR* text) {
    MessageBoxW(0, text, TITLE, MB_ICONERROR);
    ExitProcess(1);
}

static DWORD join(WCHAR* out, DWORD cap, const WCHAR* a, const WCHAR* b) {
    DWORD n = 0;
    while (*a && n + 1 < cap) out[n++] = *a++;
    while (*b && n + 1 < cap) out[n++] = *b++;
    out[n] = 0;
    return *a || *b ? 0 : n;
}

static int steam_running(void) {
    DWORD pid = 0, size = sizeof(pid);
    if (RegGetValueW(HKEY_CURRENT_USER, L"Software\\Valve\\Steam\\ActiveProcess", L"pid", RRF_RT_REG_DWORD, 0, &pid, &size) != ERROR_SUCCESS || !pid) return 0;
    HANDLE h = OpenProcess(SYNCHRONIZE, FALSE, pid);
    if (!h) return 0;
    DWORD alive = WaitForSingleObject(h, 0) == WAIT_TIMEOUT;
    CloseHandle(h);
    return alive;
}

static int same_name(const WCHAR* a, const WCHAR* b) {
    for (;; ++a, ++b) {
        WCHAR x = *a >= L'A' && *a <= L'Z' ? *a + 32 : *a, y = *b >= L'A' && *b <= L'Z' ? *b + 32 : *b;
        if (x != y) return 0;
        if (!x) return 1;
    }
}

// Starting a second copy of the game makes the running one quit, so never do that.
static int game_running(void) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) fail(L"Unable to check running games. Please retry.");
    PROCESSENTRY32W entry;
    entry.dwSize = sizeof(entry);
    int found = 0;
    for (BOOL ok = Process32FirstW(snap, &entry); ok && !found; ok = Process32NextW(snap, &entry))
        found = same_name(entry.szExeFile, L"shogun2_complete_edition.exe") || same_name(entry.szExeFile, L"RemasteredCE_Bootstrap.exe") || same_name(entry.szExeFile, L"RemasteredCE_Sim8.exe");
    CloseHandle(snap);
    return found;
}

// Everything after argv[0] in our own command line, so extra arguments reach the game.
static const WCHAR* forwarded_args(void) {
    const WCHAR* p = GetCommandLineW();
    if (*p == L'"') { ++p; while (*p && *p != L'"') ++p; if (*p) ++p; }
    else while (*p && *p != L' ' && *p != L'\t') ++p;
    while (*p == L' ' || *p == L'\t') ++p;
    return p;
}

static const WCHAR* take_arg(const WCHAR* p, const WCHAR* word) {
    const WCHAR* s = p;
    while (*word && *s == *word) { ++s; ++word; }
    if (*word || (*s && *s != L' ' && *s != L'\t')) return 0;
    while (*s == L' ' || *s == L'\t') ++s;
    return s;
}

static const WCHAR* direct_options(const WCHAR* args, int* wait_game, int* sim_turns) {
    for (;;) {
        const WCHAR* waiting = take_arg(args, L"--wait");
        if (waiting) { *wait_game = 1; args = waiting; continue; }
        const WCHAR* simultaneous = take_arg(args, L"--sim-turns");
        if (simultaneous) { *sim_turns = 1; args = simultaneous; continue; }
        return args;
    }
}

void entry(void) {
    DWORD n = GetModuleFileNameW(0, root, MAX_PATH * 4);
    if (!n || n >= MAX_PATH * 4 - 1) fail(L"Unable to locate the launcher folder.");
    while (n && root[n - 1] != L'\\') --n;
    root[n] = 0;
    // The installer keeps a second launcher next to UltimatePatch/mods.
    // Its bootstrap must still run from the game's root.
    if (!join(engine, MAX_PATH * 4, root, L"RemasteredCE\\CE.dll")) fail(L"The game folder path is too long.");
    if (n) {
        root[n - 1] = 0;
        DWORD folder = n - 1;
        while (folder && root[folder - 1] != L'\\') --folder;
        int managed = same_name(root + folder, L"RemasteredCE");
        root[n - 1] = L'\\';
        if (managed) { root[folder] = 0; }
    }
    if (!join(exe, MAX_PATH * 4, root, L"RemasteredCE\\shogun2_complete_edition.exe") || !join(engine, MAX_PATH * 4, root, L"RemasteredCE\\CE.dll") ||
        !join(data, MAX_PATH * 4, root, L"RemasteredCE\\data\\data.pack") ||
        !join(models, MAX_PATH * 4, root, L"RemasteredCE\\data\\models.pack") ||
        !join(local_en, MAX_PATH * 4, root, L"RemasteredCE\\data\\local_global.pack"))
        fail(L"The game folder path is too long.");
    const WCHAR* args = forwarded_args();
    const WCHAR* direct = take_arg(args, L"--direct");
    int wait_game = 0;
    int sim_turns = 0;
    if (direct) {
        args = direct;
        args = direct_options(args, &wait_game, &sim_turns);
        if (sim_turns) {
            if (!join(exe, MAX_PATH * 4, root, L"RemasteredCE\\RemasteredCE_Sim8.exe") ||
                !join(engine, MAX_PATH * 4, root, L"RemasteredCE\\CE8.dll") ||
                !join(data, MAX_PATH * 4, root, L"RemasteredCE\\data\\data.sim8"))
                fail(L"The game folder path is too long.");
        }
    } else {
        if (!join(manager, MAX_PATH * 4, root, L"RemasteredCE\\RemasteredCE_Launcher.exe") || GetFileAttributesW(manager) == INVALID_FILE_ATTRIBUTES)
            fail(L"The mod manager is missing. Install the latest Remastered CE setup to add Mods & Launch.");
        DWORD c = 0;
        cmd[c++] = L'"';
        for (const WCHAR* s = manager; *s; ++s) cmd[c++] = *s;
        const WCHAR* option = L"\" --game \"";
        while (*option) cmd[c++] = *option++;
        for (DWORD i = 0; root[i] && root[i + 1]; ++i) cmd[c++] = root[i];
        cmd[c++] = L'"'; cmd[c++] = L' '; cmd[c++] = L'-'; cmd[c++] = L'-';
        if (*args) { cmd[c++] = L' '; while (*args && c + 1 < MAX_PATH * 8) cmd[c++] = *args++; }
        if (*args) fail(L"The launch arguments are too long.");
        cmd[c] = 0;startup.cb = sizeof(startup);
        if (!CreateProcessW(manager, cmd, 0, 0, FALSE, 0, 0, root, &startup, &process)) fail(L"Unable to open Mods & Launch. Install .NET Framework 4.8 and retry.");
        CloseHandle(process.hThread);CloseHandle(process.hProcess);ExitProcess(0);
    }
    if (GetFileAttributesW(exe) == INVALID_FILE_ATTRIBUTES || GetFileAttributesW(engine) == INVALID_FILE_ATTRIBUTES ||
        GetFileAttributesW(data) == INVALID_FILE_ATTRIBUTES || GetFileAttributesW(models) == INVALID_FILE_ATTRIBUTES ||
        GetFileAttributesW(local_en) == INVALID_FILE_ATTRIBUTES)
        fail(L"The Remastered CE is not installed in this folder.\n\nRun the Remastered CE installer and choose Install / Update. "
             L"Keep this launcher in the Total War: SHOGUN 2 folder.");
    if (game_running())
        fail(L"Shogun 2 is already running.\n\nClose it before launching Remastered CE.");
    if (!steam_running())
        fail(L"Steam is not running.\n\nStart Steam, sign in, then launch Remastered CE again.");
    if (!SetEnvironmentVariableW(L"SteamAppId", STEAM_APP_ID) || !SetEnvironmentVariableW(L"SteamGameId", STEAM_APP_ID))
        fail(L"Unable to prepare the Steam environment.");

    DWORD c = 0;
    cmd[c++] = L'"';
    for (const WCHAR* s = exe; *s; ++s) cmd[c++] = *s;
    cmd[c++] = L'"';
    if (*args) { cmd[c++] = L' '; while (*args && c + 1 < MAX_PATH * 8) cmd[c++] = *args++; }
    if (*args) fail(L"The launch arguments are too long.");
    cmd[c] = 0;

    startup.cb = sizeof(startup);
    if (!CreateProcessW(exe, cmd, 0, 0, FALSE, 0, 0, root, &startup, &process))
        fail(L"Unable to start Remastered CE. Make sure the game is installed and Steam is running.");
    CloseHandle(process.hThread);
    if (wait_game) {
        DWORD code = 1;
        WaitForSingleObject(process.hProcess, INFINITE);
        GetExitCodeProcess(process.hProcess, &code);
        CloseHandle(process.hProcess);
        ExitProcess(code);
    }
    CloseHandle(process.hProcess);
    ExitProcess(0);
}
