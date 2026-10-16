"""Author editable ink-and-wash story illustrations; no generated stock images."""
import json
import math
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "public/handdraw-moon-v1"
INK, FUR, CREAM, BLUE = "#655044", "#bd8757", "#f0d4a0", "#8aa8b8"


class Art:
    def __init__(self):
        self.shapes = []
        self.matrix = (1, 0, 0, 1, 0, 0)
        self.part = "environment"

    def at(self, x=0, y=0, scale=1, angle=0, flip=1):
        a = math.radians(angle)
        self.matrix = (math.cos(a)*scale*flip, math.sin(a)*scale*flip,
                       -math.sin(a)*scale, math.cos(a)*scale, x, y)
        return self

    def point(self, x, y):
        a, b, c, d, e, f = self.matrix
        return round(a*x+c*y+e, 2), round(b*x+d*y+f, 2)

    def path(self, data, fill=None, width=2.6, ink=INK, opacity=1, draw=True):
        tokens = re.findall(r"[A-Za-z]|-?\d*\.?\d+", data)
        output, points, index = [], [], 0
        while index < len(tokens):
            token = tokens[index]
            if token.isalpha():
                if token not in "MLCQZ":
                    raise ValueError("Only absolute M/L/C/Q/Z are accepted")
                output.append(token)
                index += 1
            else:
                x, y = self.point(float(token), float(tokens[index+1]))
                output.append(f"{x},{y}")
                points.append((x, y))
                index += 2
        xs, ys = zip(*points)
        self.shapes.append({"d": " ".join(output), "fill": fill, "stroke": ink, "strokeWidth": width,
                            "opacity": opacity, "part": self.part, "draw": draw,
                            "bounds": [min(xs)-3, min(ys)-3, max(xs)+3, max(ys)+3]})

    def oval(self, x, y, rx, ry, fill=None, width=2.6, ink=INK, **kwargs):
        k = .5522848
        self.path(f"M{x-rx} {y} C{x-rx} {y-k*ry} {x-k*rx} {y-ry} {x} {y-ry} C{x+k*rx} {y-ry} {x+rx} {y-k*ry} {x+rx} {y} C{x+rx} {y+k*ry} {x+k*rx} {y+ry} {x} {y+ry} C{x-k*rx} {y+ry} {x-rx} {y+k*ry} {x-rx} {y} Z", fill, width, ink, **kwargs)

    def line(self, data, width=2, ink=INK, **kwargs):
        self.path(data, width=width, ink=ink, **kwargs)


def leaf(art, x, y, angle=0, size=1):
    old = art.matrix
    art.at(x, y, size, angle)
    art.path("M0 0 C-19 -25 -18 -48 -5 -61 C17 -49 22 -22 0 0 Z", "#a6ae88", width=1.6, opacity=.8)
    art.line("M0 -2 Q-4 -25 -5 -53", 1.2, "#7d866c", opacity=.7)
    art.matrix = old


def branch(art, x, y, scale=1, flip=1):
    art.part = "tree-branch"
    art.at(x, y, scale, flip=flip)
    art.path("M-270 -60 C-190 -26 -136 1 -65 6 C5 9 74 0 176 -42 C95 11 19 28 -58 26 C-139 25 -198 0 -270 -18 Z", "#a29278", 2.4)
    art.line("M-184 -7 Q-57 28 92 -12", 1.3, "#8a7964")
    positions = [(-190,-22,-30),(-128,-3,18),(-65,9,-21),(7,12,33),(75,-1,15),(130,-23,45)]
    for px, py, angle in positions:
        gx, gy = art.point(px, py)
        leaf(art, gx, gy, angle*flip, .75*scale)
        gx, gy = art.point(px+13, py+14)
        leaf(art, gx, gy, 150*flip-angle, .65*scale)
    art.at()


def ground(art, x=800, y=690, width=1000):
    art.part = "ground"
    art.at(x, y)
    art.oval(0, 0, width/2, 22, "#d6c9ac", 0, opacity=.25, draw=False)
    art.line(f"M{-width/2} 1 Q-250 -8 0 -2 Q240 -10 {width/2} 2", 1.5, "#b7ac91", opacity=.65)
    for px in [-340,-170,210,400]:
        art.line(f"M{px} 0 Q{px-2} -15 {px+4} -20 M{px+2} 0 Q{px+13} -10 {px+18} -10", 1.4, "#939d7e", opacity=.8)
    art.at()


def moon(art, x, y, radius=65, reflection=False, broken=False):
    art.part = "moon-reflection" if reflection else "moon"
    art.at(x, y)
    if broken:
        for dx, dy, w in [(-8,-24,38),(7,-9,47),(-12,8,35),(12,23,24)]:
            art.path(f"M{dx-w} {dy} Q{dx} {dy-8} {dx+w} {dy+2} Q{dx+7} {dy+9} {dx-w} {dy+4} Z", "#f9eac0", .7, "#c7d2cb")
    else:
        art.oval(0, 0, radius, radius*(.42 if reflection else 1), "#f4dea5", 1.5, "#b9aa83")
        if not reflection:
            art.oval(-radius*.25, -radius*.16, radius*.22, radius*.19, "#dac89a", 0, opacity=.28)
            art.oval(radius*.27, radius*.3, radius*.16, radius*.12, "#dac89a", 0, opacity=.3)
            art.line(f"M{-radius*.8} {-radius*.63} Q{-radius*.13} {-radius*1.05} {radius*.43} {-radius*.84}", 1.3, "#fff5da", opacity=.85)
    art.at()


def ripples(art, x, y, scale=1, broken=False):
    art.part = "water"
    art.at(x, y, scale)
    for dy, w in [(-48,110),(-24,143),(15,135),(42,93)]:
        art.line(f"M{-w} {dy} Q{-w/2} {dy-7} -16 {dy} M23 {dy+2} Q{w*.7} {dy+8} {w} {dy-3}", 1.8, "#668d9e", opacity=.7)
    if broken:
        art.line("M-85 -4 Q-50 -25 -16 -1 Q25 26 69 2 Q100 -14 124 -2", 2.2, "#dfecdf", opacity=.9)
    art.at()


def well(art, x, y, scale=1, reflect=True):
    art.part = "well-stones"
    art.at(x, y, scale)
    art.path("M-246 0 L-233 154 C-150 211 159 210 233 155 L247 0 Z", "#cec4ae", 3)
    art.line("M-235 55 C-94 101 100 101 236 55 M-235 108 C-83 160 99 160 236 108", 2.1, "#9d9683")
    for dx, top, bottom in [(-140,25,78),(0,43,99),(139,25,77),(-190,78,131),(-70,100,154),(78,100,155),(190,78,130),(-140,151,184),(0,163,193),(140,151,184)]:
        art.line(f"M{dx} {top} Q{dx-5} {(top+bottom)/2} {dx} {bottom}", 1.8, "#9d9683")
    art.oval(0, 0, 250, 100, "#e3dbc6", 3.2)
    art.oval(0, -4, 211, 72, "#90aab5", 2.4)
    art.line("M-240 12 C-150 104 148 106 240 12", 3.2, "#9e957f")
    art.line("M-224 26 C-109 96 121 95 222 23", 1.2, "#f7efd7")
    for dx, dy in [(-210,-37),(-110,-86),(25,-96),(158,-68),(-178,65),(-45,93),(94,89),(213,45)]:
        art.line(f"M{dx} {dy} L{dx*.89} {dy*.78}", 1.8, "#aaa08c")
    art.at()
    if reflect:
        moon(art, x+20*scale, y-7*scale, 53*scale, True)
    ripples(art, x, y, .95*scale)


def bucket(art, x, y, scale=1, reflection=True, broken=False, handle=True):
    art.part = "wooden-bucket"
    art.at(x, y, scale)
    if handle:
        art.line("M-80 -1 C-120 -160 124 -160 81 -1", 5, "#8c785d")
        art.line("M-80 -1 C-114 -149 117 -149 81 -1", 1.3, "#d9c39b")
    art.path("M-108 0 L-84 151 C-40 183 46 183 85 151 L108 0 Z", "#b39368", 3.2)
    for dx in [-67,-27,19,62]:
        art.line(f"M{dx} 28 Q{dx-6} 92 {dx*.8} 164", 1.9, "#876d50")
        art.line(f"M{dx+8} 52 Q{dx+4} 110 {dx*.8+6} 143", .9, "#cfb188", opacity=.7)
    art.path("M-99 51 C-46 80 50 80 99 51 L96 68 C39 95 -40 95 -96 69 Z", "#8f9185", 1.9)
    art.path("M-89 132 C-38 157 42 157 89 132 L86 145 C37 172 -37 172 -86 146 Z", "#8f9185", 1.9)
    art.oval(0, 0, 110, 45, "#e0c69b", 2.8)
    art.oval(0, -2, 94, 33, BLUE, 2)
    art.at()
    if reflection:
        moon(art, x+3*scale, y-2*scale, 34*scale, True, broken)
    ripples(art, x, y, .48*scale, broken)


def monkey(art, x, y, scale=1, pose="stand", angle=0, flip=1, elder=False, gaze="right", expression="smile"):
    art.at(x, y, scale, angle, flip)
    fur = "#a2a091" if elder else FUR
    light = "#e9ddbe" if elder else CREAM
    art.part = "monkey-tail"
    art.path("M-48 81 C-113 98 -156 91 -166 50 C-177 10 -147 -12 -122 3 C-102 15 -111 42 -127 40 C-116 22 -143 14 -149 36 C-159 73 -107 85 -51 63 Z", fur, 2.8)
    art.part = "monkey-legs"
    if pose == "sit":
        art.path("M-34 87 C-66 88 -94 128 -94 151 C-82 166 -41 154 -19 138 L7 109 Z", fur)
        art.path("M23 95 C48 93 80 116 83 149 C69 166 36 159 24 143 L-1 118 Z", fur)
        art.oval(-74, 155, 34, 13, light, 2)
        art.oval(67, 156, 32, 13, light, 2)
    else:
        stride = 24 if pose == "run" else 0
        art.path(f"M-40 83 C-54 113 -46 150 {-52-stride} 175 C-49 188 -18 193 -13 177 L-8 104 Z", fur)
        art.path(f"M14 91 C19 128 {30+stride} 148 {24+stride} 177 C34 189 65 180 58 166 L45 91 Z", fur)
        art.oval(-43-stride, 180, 34, 13, light, 2.2)
        art.oval(48+stride, 176, 34, 13, light, 2.2)
    art.part = "monkey-body"
    art.path("M-38 -9 C-71 18 -62 78 -45 109 C-23 126 23 122 48 103 C65 61 63 14 37 -9 Z", fur, 3)
    art.path("M-17 3 C-49 21 -43 74 -24 91 C-8 107 18 101 30 83 C45 53 34 12 14 3 Z", light, 1.6, "#b59571")
    art.line("M-36 5 Q-56 31 -48 54 M35 4 Q50 18 47 32", 1.3, "#e2b67b", opacity=.8)
    art.part = "monkey-head"
    art.oval(-64, -77, 24, 28, fur)
    art.oval(64, -77, 24, 28, fur)
    art.oval(-64, -77, 13, 17, light, 1.5)
    art.oval(64, -77, 13, 17, light, 1.5)
    art.path("M-59 -105 C-48 -137 -24 -144 -8 -139 L-15 -153 L4 -144 L15 -151 L18 -138 C49 -138 65 -112 66 -79 C72 -37 41 -10 0 -13 C-42 -10 -76 -47 -64 -85 Z", fur, 3.1)
    art.path("M0 -101 C-25 -135 -59 -112 -49 -81 C-70 -52 -32 -25 1 -28 C39 -25 68 -54 48 -82 C58 -113 24 -133 0 -101 Z", light, 2)
    art.oval(0, -46, 40, 25, "#f0d2aa" if not elder else "#e2d4b9", 1.7)
    for eye_x in [-23, 23]:
        art.oval(eye_x, -82, 13.5, 18, "#fff5d9", 1.7)
        gx, gy = (4, -1) if gaze == "right" else ((0, -7) if gaze == "up" else (2, 7))
        art.oval(eye_x+gx, -82+gy, 5.5, 8.5, "#493c34", .9)
        art.oval(eye_x+gx+1.5, -85+gy, 1.8, 2.5, "#fff8e1", 0)
    art.path("M-6 -58 Q0 -64 7 -58 Q2 -51 -6 -58 Z", "#8f6851", 1.3)
    if expression == "panic":
        art.line("M-37 -108 Q-24 -120 -12 -109 M12 -111 Q26 -121 37 -109", 2.7)
        art.oval(2, -35, 9, 12, "#88604a", 1.6)
    elif expression == "sad":
        art.line("M-36 -103 Q-24 -98 -12 -110 M12 -110 Q23 -100 37 -105", 2.4)
        art.line("M-13 -32 Q0 -43 14 -33", 2.1)
    else:
        art.line("M-35 -106 Q-24 -112 -13 -105 M13 -106 Q24 -113 36 -105", 2.3)
        art.line("M-18 -37 Q0 -22 19 -38", 2)
        art.line("M1 -53 L1 -41", 1.1)
    for dx in [-44, 44]:
        art.oval(dx, -51, 8.5, 4.5, "#d4967a", 0, opacity=.48)
    if elder:
        art.path("M-29 -25 Q-35 -7 -16 -9 Q-14 15 0 17 Q17 7 20 -9 Q37 -7 30 -26 Q0 -8 -29 -25 Z", "#f2ebd7", 1.5)
        art.line("M-10 -13 Q-8 1 -4 4 M6 -12 Q9 -1 5 7", 1, "#b3ad96")
    art.part = "monkey-arms"
    arms = {
        "stand": [(-45,9,-84,44,-66,95),(43,9,85,41,69,95)],
        "lean": [(-45,9,-72,60,-40,88),(43,9,91,26,127,28)],
        "run": [(-45,9,-88,-10,-94,-48),(43,9,93,-4,123,31)],
        "carry": [(-45,9,-77,57,-44,91),(43,9,90,-29,145,-50)],
        "point": [(-45,9,-82,49,-67,96),(43,9,83,-36,112,-79)],
        "sit": [(-45,9,-67,66,-38,105),(43,9,68,60,42,107)],
    }[pose]
    for sx, sy, ex, ey, hx, hy in arms:
        # Closed arm contours retain a drawable outline and a separate colour fill.
        art.path(f"M{sx-7} {sy-6} Q{ex-13} {ey-5} {hx-7} {hy+7} Q{hx+2} {hy+18} {hx+12} {hy+3} Q{ex+12} {ey-11} {sx+8} {sy+6} Z", fur, 2.4)
        art.oval(hx+2, hy+4, 13, 15, light, 1.6)
        art.line(f"M{hx-5} {hy+7} L{hx-3} {hy+14} M{hx+1} {hy+7} L{hx+3} {hy+15} M{hx+7} {hy+5} L{hx+9} {hy+12}", 1.1, "#a98361")
    art.at()


def accents(art, x, y, surprise=False):
    art.part = "gesture"
    art.at(x, y)
    if surprise:
        art.line("M-25 -2 L-37 -25 M0 -12 L0 -43 M25 -2 L37 -25", 3, "#bd8e55")
    else:
        art.line("M0 0 Q25 -11 48 0 M10 14 Q31 7 46 14", 2, "#9d9c83", opacity=.7)
    art.at()


def make_scenes():
    scenes = []
    a = Art(); ground(a, 800, 693, 1140)
    branch(a, 480, 130, 1.15)
    well(a, 1055, 500, .95)
    monkey(a, 635, 471, 1.13, "lean", 17, gaze="down", expression="panic")
    accents(a, 688, 265, True)
    scenes.append({"id":"discovery", "shapes":a.shapes})

    a = Art(); ground(a, 820, 695, 1030)
    bucket(a, 1110, 504, .9, reflection=False)
    monkey(a, 715, 459, 1.23, "run", -7, expression="panic")
    accents(a, 435, 482)
    branch(a, 1320, 155, .66, -1)
    scenes.append({"id":"rescue", "shapes":a.shapes})

    a = Art(); ground(a, 820, 695, 1100)
    well(a, 1050, 460, 1.15, reflect=False)
    a.part="rope"; a.at(); a.line("M708 528 Q807 266 1040 325", 3.3, "#a48a64")
    bucket(a, 1040, 399, .62)
    monkey(a, 560, 455, 1.24, "lean", 13, gaze="down")
    scenes.append({"id":"capture", "shapes":a.shapes})

    a = Art(); ground(a, 795, 696, 1040)
    monkey(a, 661, 456, 1.23, "carry", -6, gaze="down", expression="sad")
    bucket(a, 835, 480, .82, broken=True)
    a.at(); a.part="splashes"
    for px, py, angle in [(940,447,24),(965,477,45),(931,500,-15)]:
        a.at(px,py,1,angle);a.path("M0 0 C-9 -16 -10 -24 0 -31 C10 -21 13 -10 0 0 Z", "#9ebcc6", 1.5)
    a.at(); accents(a, 561, 273, True)
    scenes.append({"id":"shattered", "shapes":a.shapes})

    a = Art(); ground(a, 820, 699, 1250)
    monkey(a, 538, 435, 1.37, "point", elder=True, gaze="up")
    monkey(a, 1015, 491, 1.04, "stand", flip=-1, gaze="down", expression="sad")
    bucket(a, 1237, 590, .61, broken=True)
    branch(a, 1250, 130, .78, -1)
    scenes.append({"id":"question", "shapes":a.shapes})

    a = Art(); ground(a, 820, 701, 1220)
    branch(a, 470, 170, 1.12)
    a.part="night-wash"; a.at(); a.oval(1080,215,175,125,"#a8bdc5",0,opacity=.12,draw=False)
    moon(a, 1090, 192, 85)
    monkey(a, 633, 472, 1.18, "point", elder=True, gaze="up")
    monkey(a, 887, 542, .94, "sit", gaze="up")
    well(a, 1310, 595, .48)
    scenes.append({"id":"look-up", "shapes":a.shapes})

    a = Art(); ground(a, 820, 693, 1150)
    bucket(a, 1037, 500, 1.16)
    monkey(a, 608, 504, 1.12, "sit", gaze="right")
    branch(a, 1300, 148, .85, -1)
    accents(a, 805, 453)
    scenes.append({"id":"still-water", "shapes":a.shapes})

    a = Art(); ground(a, 830, 701, 1210)
    branch(a, 1070, 154, 1.08, -1)
    moon(a, 1240, 263, 62)
    well(a, 558, 565, .65)
    monkey(a, 1001, 525, 1.04, "sit", gaze="up")
    bucket(a, 1198, 614, .48)
    scenes.append({"id":"ending", "shapes":a.shapes})
    return scenes


def main():
    scenes = make_scenes()
    (ROOT / "content/handdraw-moon-v1/art.json").write_text(json.dumps(scenes, ensure_ascii=False, separators=(",", ":")), encoding='utf-8')
    rng = np.random.default_rng(314)
    noise = rng.normal(0, .6, (1080, 1920, 1))
    paper = np.clip(np.array([249, 246, 236])[None,None,:] + noise, 0, 255).astype(np.uint8)
    Image.fromarray(paper).save(ASSETS / "paper.jpg", quality=90)
    source = ROOT / ".cache/handdraw-hosted/2c035a0c900589f8650fed9fe6b863773e4496a3c1bb389dcb7dc35501bd1dd5/teacher-pen.png"
    target = ASSETS / "drawing-hand.png"
    if not source.is_file():
        source = target
    if not source.is_file():
        raise FileNotFoundError("The attributed drawing-hand asset is missing; restore it before making the art package")
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    with Image.open(source) as hand:
        print("hand", hand.size)
    provenance = {"illustrations":"Original editable vector artwork, authored by code in scripts/create_moon_art.py", "aiImageGenerationUsed":False,
                  "hand":{"source":"https://github.com/threerocks/sweety-handdraw-video", "commit":"5206ec0d17f9b353e400b64b9c51ad69e721e02a", "asset":"teacher-pen.png", "sha256":"2c035a0c900589f8650fed9fe6b863773e4496a3c1bb389dcb7dc35501bd1dd5", "license":"MIT", "copyright":"Copyright (c) 2026 threerocks"}}
    (ROOT / "content/handdraw-moon-v1/asset-sources.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2), encoding='utf-8')
    license_path = ROOT.parents[1] / "licenses/MIT-drawing-hand.txt"
    if license_path.is_file():
        shutil.copy2(license_path, ASSETS / "drawing-hand-LICENSE.txt")
    print(json.dumps({"scenes":len(scenes),"shapes":[len(s["shapes"]) for s in scenes]}))


if __name__ == "__main__":
    main()
