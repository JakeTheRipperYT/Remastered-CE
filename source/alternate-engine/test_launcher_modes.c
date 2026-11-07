// Tests the actual launcher parser without creating a game process.
#define entry launcher_entry
#include "launcher.c"
#undef entry

static void check(const WCHAR* text, int waiting, int simultaneous, const WCHAR* rest, DWORD error) {
    int actual_wait = 0, actual_sim = 0;
    const WCHAR* actual_rest = direct_options(text, &actual_wait, &actual_sim);
    if (actual_wait != waiting || actual_sim != simultaneous || !same_name(actual_rest, rest)) ExitProcess(error);
}

void test_entry(void) {
    check(L"", 0, 0, L"", 1);
    check(L"--wait", 1, 0, L"", 2);
    check(L"--sim-turns", 0, 1, L"", 3);
    check(L"--wait --sim-turns -foo", 1, 1, L"-foo", 4);
    check(L"--sim-turns --wait -foo", 1, 1, L"-foo", 5);
    check(L"--sim-turnsx", 0, 0, L"--sim-turnsx", 6);
    if (take_arg(L"--directly", L"--direct")) ExitProcess(7);
    ExitProcess(0);
}
