#!/usr/bin/env python3

# Based on:
# https://github.com/Zren/mpv-osc-tethys/blob/master/icons/svgtohtmltoluapath.py

import re
import subprocess
import sys
from pathlib import Path

icons = [
    "play",
    "pause",
    "close",
    "minimize",
    "maximize",
    "maximize_exit",
    "fs_enter",
    "fs_exit",
    # "ch_prev",
    # "ch_next",
    "info",
    "cy_audio",
    "cy_sub",
    # "pip_enter",
    # "pip_exit",
    "pl_prev",
    "pl_next",
    "skipback",
    "skipfrwd",
    # "speed",
    "volume_low",
    "volume_medium",
    "volume_high",
    "volume_over",
    "volume_mute",
]

if len(sys.argv) > 1:
    icons = sys.argv[1:]

N = r"(-?\d+(\.\d+)?)"  # int or float pattern
F = r"(-?\d+\.\d+)"  # float pattern

canvasSizePattern = re.compile(rf"    <canvas id='canvas' width='{N}' height='{N}'></canvas>")
transformPattern = re.compile(r"\tctx.transform\(.+")
moveToPattern = re.compile(rf"\tctx.moveTo\({F}, {F}\);")
lineToPattern = re.compile(rf"\tctx.lineTo\({F}, {F}\);")
curveToPattern = re.compile(rf"\tctx.bezierCurveTo\({F}, {F}, {F}, {F}, {F}, {F}\);")


def convertToCanvas(svgFilepath: Path) -> Path:
    htmlFilepath = svgFilepath.with_suffix(".html")
    subprocess.run(["inkscape", svgFilepath, "-o", htmlFilepath])
    return htmlFilepath


def cleanNum(numstr: str) -> str:
    outstr = str(float(numstr))
    if outstr.endswith(".0"):
        outstr = outstr[:-2]
    return outstr


def generatePath(filepath: Path) -> str:
    path = []
    with filepath.open("r") as fin:
        for line in fin.readlines():
            line = line.rstrip()
            # print(line)

            m = canvasSizePattern.match(line)
            if m:
                # MPV's ASS alignment centering crops the path itself.
                # For the path to retain position in the SVG viewbox,
                # we need to "move" to the corners of the viewbox.
                cmd = "m 0 0"  # Top Left
                path.append(cmd)
                w = cleanNum(m.group(1))
                h = cleanNum(m.group(3))
                cmd = f"m {w} {h}"  # Bottom Right
                # print("size", cmd)
                path.append(cmd)
                continue

            m = transformPattern.match(line)
            if m:
                print("[error] filepath:", filepath)
                print("Cannot parse ctx.transform()")
                print("Please ungroup path to remove transormation")
                sys.exit(1)

            m = moveToPattern.match(line)
            if m:
                x = cleanNum(m.group(1))
                y = cleanNum(m.group(2))
                cmd = f"m {x} {y}"
                # print("moveTo", cmd)
                path.append(cmd)
                continue

            m = lineToPattern.match(line)
            if m:
                x = cleanNum(m.group(1))
                y = cleanNum(m.group(2))
                cmd = f"l {x} {y}"
                # print("lineTo", cmd)
                path.append(cmd)
                continue

            m = curveToPattern.match(line)
            if m:
                x1 = cleanNum(m.group(1))
                y1 = cleanNum(m.group(2))
                x2 = cleanNum(m.group(3))
                y2 = cleanNum(m.group(4))
                x = cleanNum(m.group(5))
                y = cleanNum(m.group(6))
                cmd = f"b {x1} {y1} {x2} {y2} {x} {y}"
                # print("curveTo", cmd)
                path.append(cmd)
                continue

    return str(" ".join(path))


def printIcon(name: str, htmlFilepath: Path) -> None:
    path = generatePath(htmlFilepath)
    print(rf'    {name} = "{{\\p1}}{path}{{\\p0}}",')


def genIconPath(name: str) -> None:
    svgFilepath = Path("icons", f"{name}.svg")
    if not svgFilepath.exists():
        print(f"Error: File '{svgFilepath}' does not exist.")
        sys.exit(1)
    htmlFilepath = convertToCanvas(svgFilepath)
    printIcon(name, htmlFilepath)
    htmlFilepath.unlink()


print("local icons = {")

for icon in icons:
    genIconPath(icon)

print("}")
