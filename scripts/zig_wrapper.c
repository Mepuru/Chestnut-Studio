/**
 * Zig wrapper: forces -mcpu=baseline for CPU compatibility.
 *
 * For meta commands (version, help, etc.) passes through directly.
 * For cc commands, adds -mcpu=baseline after "cc".
 */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <windows.h>

/* Check if argv[1] is a meta command that should NOT get -mcpu=baseline */
static int is_meta_command(const char *arg) {
    if (!arg) return 1;
    if (strcmp(arg, "version") == 0) return 1;
    if (strcmp(arg, "--version") == 0) return 1;
    if (strcmp(arg, "--help") == 0) return 1;
    if (strcmp(arg, "help") == 0) return 1;
    if (strcmp(arg, "--print-targets") == 0) return 1;
    if (strcmp(arg, "build") == 0) return 1;
    return 0;
}

int main(int argc, char *argv[]) {
    char zig_dir[MAX_PATH];
    char cmd_line[65536];
    int i;
    size_t pos;
    int is_meta = (argc <= 1) || is_meta_command(argv[1]);

    // Get our own directory (where zig_real.exe lives)
    GetModuleFileNameA(NULL, zig_dir, MAX_PATH);
    char *p = strrchr(zig_dir, '\\');
    if (p) *p = '\0';

    // Build command line
    if (is_meta) {
        // Pass through directly: zig_real.exe [args]
        pos = snprintf(cmd_line, sizeof(cmd_line),
                       "\"%s\\zig_real.exe\"", zig_dir);
        for (i = 1; i < argc; i++) {
            size_t len = strlen(cmd_line);
            snprintf(cmd_line + len, sizeof(cmd_line) - len,
                     " \"%s\"", argv[i]);
        }
    } else {
        // Add -mcpu=baseline: zig_real.exe cc -mcpu=baseline [args]
        // First arg should be "cc" - use it, add -mcpu=baseline after
        pos = snprintf(cmd_line, sizeof(cmd_line),
                       "\"%s\\zig_real.exe\"", zig_dir);
        for (i = 1; i < argc; i++) {
            size_t len = strlen(cmd_line);
            snprintf(cmd_line + len, sizeof(cmd_line) - len,
                     " \"%s\"", argv[i]);
            // Add -mcpu=baseline right after the first arg ("cc")
            if (i == 1) {
                size_t len2 = strlen(cmd_line);
                snprintf(cmd_line + len2, sizeof(cmd_line) - len2,
                         " -mcpu=baseline");
            }
        }
    }

    // Launch
    STARTUPINFOA si = {0};
    PROCESS_INFORMATION pi = {0};
    si.cb = sizeof(si);

    BOOL ok = CreateProcessA(
        NULL, cmd_line, NULL, NULL, FALSE,
        0, NULL, NULL, &si, &pi
    );

    if (!ok) {
        fprintf(stderr, "zig_wrapper: failed to launch zig_real.exe\n");
        fprintf(stderr, "  cmd: %s\n", cmd_line);
        return 1;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exit_code;
    GetExitCodeProcess(pi.hProcess, &exit_code);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return (int)exit_code;
}
