"""
ccmin wizard — pure stdlib, zero dependencies.
ANSI colors (monokai palette), ASCII box UI, works on any terminal.
"""

import os
import shutil
import sys
from pathlib import Path

# ── ANSI ──────────────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[92m"   # #a6e22e  monokai green
_CYAN   = "\033[38;5;81m"    # #66d9e8  monokai cyan
_WHITE  = "\033[97m"          # bright white — labels
_MUTED  = "\033[38;5;250m"   # light grey (readable on dark bg)

def _g(s):     return f"{_GREEN}{_BOLD}{s}{_RESET}"
def _c(s):     return f"{_CYAN}{s}{_RESET}"
def _w(s):     return f"{_WHITE}{s}{_RESET}"
def _muted(s): return f"{_MUTED}{s}{_RESET}"


# ── Logo ───────────────────────────────────────────────────────────────────────

def _logo():
    G = f"{_GREEN}{_BOLD}"
    R = _RESET
    return [
        f"      {G}██{R}      ",
        f"  {G}██{R}      {G}██{R}  ",
        f"    {G}██{R}  {G}██{R}    ",
        f"  {G}██{R}      {G}██{R}  ",
        f"      {G}██{R}      ",
    ]


# ── Primitives ─────────────────────────────────────────────────────────────────

def _input(prompt=""):
    try:
        return input(prompt)
    except (KeyboardInterrupt, EOFError):
        print()
        print(_muted("  cancelled"))
        sys.exit(0)


def _confirm(question, default=True):
    hint = _muted("Y/n" if default else "y/N")
    while True:
        raw = _input(f"  {_g('›')} {_BOLD}{question}{_RESET}  {hint}  ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print(_muted("    enter y or n"))


def _select(question, choices):
    print(f"  {_g('›')} {_BOLD}{question}{_RESET}")
    print()
    for i, (label, _) in enumerate(choices, 1):
        print(f"    {_muted(str(i) + '.')}  {label}")
    print()
    while True:
        raw = _input(f"  {_muted('enter number')}  [{_g('1')}]  ").strip()
        if raw == "":
            return choices[0][1]
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(choices):
                return choices[idx - 1][1]
        print(_muted(f"    enter a number between 1 and {len(choices)}"))


def _text(question, default="", hint=""):
    hint_str    = f"  {_muted(hint)}" if hint else ""
    default_str = f"  [{_g(default)}]" if default else ""
    raw = _input(f"  {_g('›')} {_BOLD}{question}{_RESET}{hint_str}{default_str}  ").strip()
    return raw if raw else default


# ── Layout ─────────────────────────────────────────────────────────────────────

_W = 45

def _box_top(title=""):
    if title:
        pad = _W - len(title) - 2
        return f"  ╭─ {_BOLD}{title}{_RESET} {'─' * pad}╮"
    return f"  ╭{'─' * (_W + 2)}╮"

def _box_row(left, right="", right_len=None):
    col1 = 12
    col2 = _W - col1 - 2
    rlen = right_len if right_len is not None else len(right)
    pad  = max(0, col2 - rlen)
    return f"  │  {_muted(left):<{col1}}  {right}{' ' * pad}│"

def _box_sep():
    return f"  ├{'─' * (_W + 2)}┤"

def _box_bot():
    return f"  ╰{'─' * (_W + 2)}╯"

def _step(n, total, title):
    label = f"step {n}/{total}  {title}"
    dashes = _muted('─' * max(0, _W - len(label) - 3))
    print(f"  {_muted('───')}  {_c(label)}  {dashes}")
    print()


def _banner():
    logo = _logo()
    title_lines = [
        "",
        f"  {_g('ccmin')}  {_muted('·')}  {_BOLD}setup wizard{_RESET}",
        f"  {_muted('token-minimal launcher for Claude Code')}",
        "",
        "",
    ]
    for i in range(5):
        l = logo[i]
        t = title_lines[i]
        print(f"  {l}  {t}")
    print()


# ── Main wizard ────────────────────────────────────────────────────────────────

def run(config_exists, detect_launcher_fn, detect_claude_version_fn):
    """
    Run the interactive init wizard.
    Returns a dict with all user choices, or None if cancelled.
    """
    _banner()

    if config_exists:
        if not _confirm("ccmin is already initialized. Reinitialize?", default=False):
            print(_muted("  nothing changed"))
            return None
        print()

    # ── Step 1: Launcher ───────────────────────────────────────────────────────
    _step(1, 6, "launcher")
    launcher_type = _select("Which launcher?", [
        (f"claude          {_muted('Claude Code official')}",              "claude"),
        (f"custom          {_muted('e.g. ccr code, cursor, claude-dev')}", "custom"),
    ])

    if launcher_type == "custom":
        print()
        while True:
            custom = _text("Binary name or command", default="claude",
                           hint="e.g. 'ccr code' or 'claude-dev'")
            binary = custom.split()[0]
            if shutil.which(binary):
                launcher = custom
                break
            print(f"  {_w('!')} '{binary}' not found in PATH — try again")
            print()
    else:
        launcher = "claude"
    print()

    # ── Step 2: Scope ──────────────────────────────────────────────────────────
    _step(2, 6, "scope")
    scope = _select("Where should settings apply?", [
        (f"local           {_muted('this project only  (recommended)')}",  "local"),
        (f"global          {_muted('user-wide, all projects')}",           "global"),
    ])
    print()

    # ── Step 3: Project path ───────────────────────────────────────────────────
    cwd = os.getcwd()
    print(f"  {_w('current directory')}  {_c(cwd)}")
    print()
    if not _confirm("Use this as project path?", default=True):
        print()
        cwd = _text("Project path", default=cwd)
    print()

    # ── Step 4: Mode ───────────────────────────────────────────────────────────
    _step(3, 6, "permission mode")
    selected_mode = _select("How strict should Claude's tool access be?", [
        (f"very-strict     {_muted('Read (needs approval), Write, Edit  · no git')}", "very-strict"),
        (f"minimal         {_muted('Read, Write, Edit, MultiEdit        · no git')}", "minimal"),
        (f"standard        {_muted('Read, Write, Edit, MultiEdit, Bash(git *)    ')}", "standard"),
        (f"custom          {_muted('define your own tool list')}",                    "custom"),
    ])

    custom_allow = None
    if selected_mode == "custom":
        print()
        raw = _text("Tools to allow", hint="comma-separated, e.g. Read,Write,Bash(git *)")
        custom_allow = [t.strip() for t in raw.split(",") if t.strip()]
        bad = [t for t in custom_allow if t == t.lower() and "(" not in t]
        if bad:
            print(f"  {_w('!')} these look wrong (lowercase, no pattern): {', '.join(bad)}")
    print()

    # ── Step 5: Token optimizations ────────────────────────────────────────────
    _step(4, 6, "token optimizations")
    print(f"  {_w('fast tools')}  fast_read / fast_edit / fast_multi_edit")
    print(f"             {_muted('udiff patches + session hash tracking')}")
    print()
    fast_tools_enabled = _confirm("Enable fast tools?", default=False)

    sr_fallback = True
    if fast_tools_enabled:
        print()
        sr_fallback = _confirm("Enable search-replace fallback if udiff fails?", default=True)
    print()

    print(f"  {_w('repo map')}    injects project file structure into system prompt")
    print(f"             {_muted('costs a few tokens at session start, saves tokens overall')}")
    print()
    repo_map_enabled = _confirm("Enable repo map?", default=False)

    repo_map_max_tokens = 1024
    if repo_map_enabled:
        print()
        raw_tok = _text("Max tokens for repo map", default="1024",
                        hint="lower = cheaper start  higher = more context")
        repo_map_max_tokens = int(raw_tok) if raw_tok.isdigit() and int(raw_tok) > 0 else 1024
    print()

    # ── Step 6: Install method ─────────────────────────────────────────────────
    _step(5, 6, "install method")
    install_method = _select("How to install the ccmin command?", [
        (f"symlink         {_muted('/usr/local/bin/ccmin  (recommended)')}", "symlink"),
        (f"bashrc          {_muted('alias in ~/.bashrc')}",                  "bashrc"),
        (f"skip            {_muted('I will handle it manually')}",           "skip"),
    ])
    print()

    # ── Summary ────────────────────────────────────────────────────────────────
    _step(6, 6, "review")

    if fast_tools_enabled:
        sr_label  = "on  SR fallback " + ("on" if sr_fallback else "off")
        fast_disp = _g("on") + _muted("  SR fallback " + ("on" if sr_fallback else "off"))
        fast_len  = len(sr_label)
    else:
        fast_disp = _muted("off")
        fast_len  = 3

    if repo_map_enabled:
        rm_label  = f"on  cap {repo_map_max_tokens} tokens"
        repo_disp = _g("on") + _muted(f"  cap {repo_map_max_tokens} tokens")
        repo_len  = len(rm_label)
    else:
        repo_disp = _muted("off")
        repo_len  = 3

    inst_str = {
        "symlink": "/usr/local/bin/ccmin",
        "bashrc":  "~/.bashrc alias",
        "skip":    "manual",
    }.get(install_method, install_method)

    path_display = cwd if len(cwd) <= 30 else "…" + cwd[-29:]

    print(_box_top("summary"))
    print(_box_row("launcher",   launcher,      len(launcher)))
    print(_box_row("scope",      scope,          len(scope)))
    print(_box_row("path",       path_display,   len(path_display)))
    print(_box_row("mode",       selected_mode,  len(selected_mode)))
    print(_box_row("install",    inst_str,       len(inst_str)))
    print(_box_sep())
    print(_box_row("fast tools", fast_disp, fast_len))
    print(_box_row("repo map",   repo_disp, repo_len))
    print(_box_bot())
    print()

    if not _confirm("Apply this configuration?", default=True):
        print(_muted("  cancelled — nothing was written"))
        return None

    print()

    return {
        "launcher":            launcher,
        "scope":               scope,
        "project_path":        cwd,
        "selected_mode":       selected_mode,
        "custom_allow":        custom_allow,
        "install_method":      install_method,
        "fast_tools_enabled":  fast_tools_enabled,
        "sr_fallback":         sr_fallback,
        "repo_map_enabled":    repo_map_enabled,
        "repo_map_max_tokens": repo_map_max_tokens,
    }

