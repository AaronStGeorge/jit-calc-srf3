#!/usr/bin/env python3
"""Compile HIP C++ or gfx assembly to a HSACO code object, or decompile one back.

The direction is chosen from the input file extension (override with --mode):

    *.hip.cpp / *.hip / *.cpp / *.cc  -> HIP C++    -> .hsaco   (amdclang++)
    *.asm / *.s                       -> assembly   -> .hsaco   (amdclang)
    *.hsaco / *.co / *.o              -> HSACO      -> .asm     (llvm-objdump)

The ROCm/LLVM toolchain (amdclang, amdclang++, llvm-objdump) is expected on PATH --
this is what .envrc wires up. If a tool is missing the run fails with a clear error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_ARCH = "gfx1201"

# input extension -> mode. Longest suffix wins (".hip.cpp" before ".cpp").
HIP_EXTS = (".hip.cpp", ".hip", ".cpp", ".cc")
ASM_EXTS = (".asm", ".s")
HSACO_EXTS = (".hsaco", ".co", ".o")


def banner(message: str) -> None:
    print(f"== {message}", flush=True)


def fail(message: str) -> int:
    print(f"!! {message}", file=sys.stderr, flush=True)
    return 1


def detect_mode(path: Path) -> str | None:
    name = path.name.lower()
    if name.endswith(HIP_EXTS):
        return "hip"
    if name.endswith(ASM_EXTS):
        return "asm"
    if name.endswith(HSACO_EXTS):
        return "decompile"
    return None


def default_output(path: Path, mode: str) -> Path:
    suffix = ".asm" if mode == "decompile" else ".hsaco"
    # Strip the full known extension (handles the compound ".hip.cpp").
    name = path.name
    for ext in (*HIP_EXTS, *ASM_EXTS, *HSACO_EXTS):
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
            break
    else:
        name = path.stem
    return path.with_name(name + suffix)


def build_argv(mode: str, source: Path, output: Path, arch: str) -> list[str]:
    if mode == "hip":
        return [
            "amdclang++",
            "-x", "hip",
            "--offload-device-only",
            "--no-gpu-bundle-output",
            f"--offload-arch={arch}",
            "-O2",
            "-c", str(source),
            "-o", str(output),
        ]
    if mode == "asm":
        return [
            "amdclang",
            "-x", "assembler",
            "-target", "amdgcn-amd-amdhsa",
            f"-mcpu={arch}",
            str(source),
            "-o", str(output),
        ]
    if mode == "decompile":
        return ["llvm-objdump", "-d", f"--mcpu={arch}", str(source)]
    raise ValueError(f"unknown mode: {mode}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile HIP C++/assembly to HSACO, or decompile HSACO to assembly.",
    )
    parser.add_argument("input", type=Path, help="source, kernel, or .hsaco file")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="output path (default: <input> with .hsaco or .asm suffix)",
    )
    parser.add_argument(
        "--mode", choices=("auto", "hip", "asm", "decompile"), default="auto",
        help="direction; 'auto' picks from the input extension (default: auto)",
    )
    parser.add_argument(
        "--arch", default=DEFAULT_ARCH,
        help=f"gfx target for --offload-arch/-mcpu (default: {DEFAULT_ARCH})",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="echo the toolchain command before running it",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source: Path = args.input

    if not source.is_file():
        return fail(f"input not found: {source}")

    mode = args.mode
    if mode == "auto":
        detected = detect_mode(source)
        if detected is None:
            return fail(
                f"cannot infer mode from '{source.name}'; pass --mode {{hip,asm,decompile}}"
            )
        mode = detected

    output: Path = args.output or default_output(source, mode)
    tool_argv = build_argv(mode, source, output, args.arch)

    if args.verbose:
        banner(" ".join(tool_argv))

    try:
        completed = subprocess.run(tool_argv, capture_output=True, text=True)
    except FileNotFoundError:
        return fail(
            f"toolchain binary '{tool_argv[0]}' not found on PATH; "
            f"is .envrc / direnv active in this directory?"
        )

    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        return fail(f"{tool_argv[0]} failed (exit {completed.returncode})")

    # llvm-objdump writes disassembly to stdout; everything else writes the file itself.
    if mode == "decompile":
        output.write_text(completed.stdout)
    elif not output.is_file():
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        return fail(f"{tool_argv[0]} reported success but produced no output: {output}")

    banner(f"wrote {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
