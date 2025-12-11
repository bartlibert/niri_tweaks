#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# ---------------------------------------------------------------------------------------------------------------------
# %% Handle script args

from os.path import expanduser
import argparse

parser = argparse.ArgumentParser(
    description="Parse niri keybinds into 'dmenu' friendly format",
    epilog="The results from this script can be piped to a launcher for display, eg. using: '| fuzzel -d'",
)
parser.add_argument("-i", "--keybind_kdl", type=str, default="~/.config/niri/config.kdl", help="Path to keybinds.kdl")
parser.add_argument(
    "-t",
    "--exclude_titles",
    action="store_true",
    help="If set, the 'hotkey-overlay-title' text will not be included in the output",
)
parser.add_argument(
    "-s",
    "--include_spawn_prefix",
    action="store_true",
    help="If set, 'spawn' and 'spawn-sh' will be included in the output",
)
parser.add_argument(
    "-c",
    "--include_command_quotes",
    action="store_true",
    help="If set, aprostrophes & quotation marks will not be removed from commands",
)
parser.add_argument(
    "-p",
    "--separator",
    type=str,
    default=" | ",
    help="Separator used between keybinds/titles/commands (default: ' | ')",
)
parser.add_argument(
    "-e",
    "--output_line_end",
    type=str,
    default="\n",
    help="Line ending (terminating) string when generating output (default: \\n)",
)

# For convenience
args = parser.parse_args()
KEYBIND_KDL_PATH = expanduser(args.keybind_kdl)
INCLUDE_OVERLAY_TITLES = not args.exclude_titles
REMOVE_CMD_QUOTATIONS = not args.include_command_quotes
REMOVE_SPAWN_PREFIX = not args.include_spawn_prefix
OUTPUT_LINE_END = args.output_line_end


# ---------------------------------------------------------------------------------------------------------------------
# %% Parse kdl file

# Read all keybind data
try:
    with open(KEYBIND_KDL_PATH, "r") as infile:
        full_text = infile.read()
except FileNotFoundError:
    import subprocess

    notify_title, notify_explain = "Error parsing keybinds!", f"Not found: {KEYBIND_KDL_PATH}"
    subprocess.run(["notify-send", notify_title, notify_explain])
    raise FileNotFoundError(KEYBIND_KDL_PATH)

# Try to grab only the 'binds {...}' section
if full_text.startswith("binds"):
    # Assume we're dealing with a stand-alone keybinds.kdl file that starts with 'binds {'
    first_line_break_idx = full_text.index("\n")
    kdl_bind_split = full_text[1 + first_line_break_idx :]
else:
    # Assume the 'bind {' line is further into the file
    kdl_binds = full_text.split("\nbinds")
    if len(kdl_binds) != 2:
        import subprocess

        notify_title, notify_explain = "Error parsing keybinds!", "Could not find binds {...} section"
        subprocess.run(["notify-send", notify_title, notify_explain])
        raise IOError(f"Error parsing keybinds: {KEYBIND_KDL_PATH}")

# Filter out comments
filtered_list = []
for full_line in kdl_bind_split.splitlines():

    # Get rid of indents
    line = full_line.strip()

    # Stop when we hit the end of the binds {...} section (assumed to be marked by a single '}')
    if line == "}":
        break

    # Skip comments and other non-bind lines
    if line.startswith("//") or line.startswith("binds") or line in ("{", "}") or len(line) == 0:
        continue

    # Try to separate command (part insided brackets: { spawn ... } from the part before)
    bind_command_split = line.split("{")
    if len(bind_command_split) < 2:
        continue
    elif len(bind_command_split) > 2:
        print("Error parsing keybind! Unexpected double curly bracket:", line, sep="\n", flush=True)
        continue

    # Break apart binding config & command parts
    config, command = bind_command_split
    config_split = config.split(" ")
    command_split = command.split(";")

    # Get the first command (e.g. 'Mod+Q') & command
    keybind_str = config_split[0]
    command_str = command_split[0].strip()

    # Remove 'spawn' or 'spawn-sh' if needed
    if REMOVE_SPAWN_PREFIX and command_str.startswith("spawn"):
        command_str = command_str.removeprefix("spawn-sh " if "spawn-sh" in command_str else "spawn ")
    if REMOVE_CMD_QUOTATIONS:
        command_str = command_str.replace('"', "").replace("'", "")

    # Grab hotkey title if needed
    title_str = ""
    if INCLUDE_OVERLAY_TITLES:
        target_str = "hotkey-overlay-title="
        if target_str in config:
            _, title_split = config.split(target_str)
            if not title_split.startswith("null"):
                str_marker = title_split[0]
                _, title_str, _ = title_split.split(str_marker)

    # Join the keybind + title + command into 1 line for printing
    final_strs = (keybind_str, title_str, command_str) if len(title_str) > 0 else (keybind_str, command_str)
    filtered_line = " | ".join(final_strs)
    filtered_list.append(filtered_line)

# Print results to console (for piping into other programs)
print(OUTPUT_LINE_END.join(filtered_list))
