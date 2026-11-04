# Build the documentation images for the Poly Bridge budget-modifier repo.
#
# Inputs live in images/raw/ (raw adb screencaps, not committed); the generated
# PNGs land in images/. Run from anywhere:  python make_images.py
from PIL import Image, ImageDraw, ImageFont
import os

REPO = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(REPO, "images", "raw")
OUT = os.path.join(REPO, "images")

GREEN_TITLE = (127, 227, 160)   # 0xFF7FE3A0 - panel title text / "应用"
GREEN_SEL   = (31, 111, 74)     # 0xFF1F6F4A - selected tab & 应用 button background
RED_X       = (255, 138, 128)   # 0xFFFF8A80 - the close glyph


def font(sz, bold=False):
    p = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()


def load(n):
    return Image.open(os.path.join(RAW, n)).convert("RGB")


def near(p, c, tol):
    return all(abs(p[i] - c[i]) <= tol for i in range(3))


def find_box(im, c, tol, region):
    px = im.load()
    x0, y0, x1, y1 = region
    xs, ys = [], []
    for y in range(y0, min(y1, im.size[1])):
        for x in range(x0, min(x1, im.size[0])):
            if near(px[x, y], c, tol):
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def panel_box(im, height, region):
    """Locate the panel from its distinctive green title text."""
    b = find_box(im, GREEN_TITLE, 45, region)
    if not b:
        raise SystemExit("panel title not found in region %s" % (region,))
    left = b[0] - 18
    top = ((b[1] + b[3]) // 2) - 54
    return (left, top, left + 594, top + height)


# ---------------------------------------------------------------- panel crops
# Collapsed state (113 px tall) and expanded state (771 px tall), both measured
# on device with `dumpsys window`. Title search is restricted to the top strip.
s71 = load("s71.png")                       # collapsed
s73 = load("s73.png")                       # expanded

# Geometry measured on device with `dumpsys window windows`:
#   mAttrs=(17,39), parent frame starts at y=84  ->  panel sits at screen (17, 123)
#   Requested w=594, h=771 expanded / h=113 collapsed
PANEL_L, PANEL_T, PANEL_W = 17, 123, 594
collapsed_box = (PANEL_L, PANEL_T, PANEL_L + PANEL_W, PANEL_T + 113)
expanded_box  = (PANEL_L, PANEL_T, PANEL_L + PANEL_W, PANEL_T + 771)
print("collapsed box:", collapsed_box)
print("expanded box :", expanded_box)

panel = s73.crop(expanded_box)
panel.save(os.path.join(OUT, "panel-expanded.png"))
print("panel-expanded:", panel.size)

s71.crop(collapsed_box).save(os.path.join(OUT, "panel-collapsed.png"))
print("panel-collapsed saved")

# ------------------------------------------------------- panel over the game
# s65 is a 2400x1080 landscape capture of the game with the panel floating on it.
game = load("s65.png")
game.resize((1600, 720), Image.LANCZOS).save(
    os.path.join(OUT, "panel-over-game.png"), optimize=True)
print("panel-over-game saved")

# ------------------------------------------------------------- HUD close-ups
# Both captures share the same HUD layout, so one crop rectangle fits both.
# A slim white border keeps the close-up from looking sliced off.
HUD = (860, 0, 1560, 118)


def hud(name):
    c = load(name).crop(HUD).resize((1400, 236), Image.LANCZOS)
    framed = Image.new("RGB", (c.size[0] + 8, c.size[1] + 8), (255, 255, 255))
    framed.paste(c, (4, 4))
    return framed


hud("s65.png").save(os.path.join(OUT, "hud-before.png"), optimize=True)
hud("s66.png").save(os.path.join(OUT, "hud-modded.png"), optimize=True)
print("hud-before / hud-modded saved")

# --------------------------------------------------------- annotated diagram
# Row centres inside the panel, derived from its own layout: 19 px top padding,
# 71 px title bar (26 dp), 88 px tab row (32 dp), 38 px hint (14 dp),
# four 93 px keypad rows (34 dp), 96 px action row (35 dp).
ann = panel.copy().convert("RGB")
PAD = 24
W, H = ann.size
LEGEND = [
    ("1", "标题栏：点一下收起 / 恢复，按住拖动可移动面板（不会拖出屏幕）"),
    ("2", "「—」最小化：把面板收成一条细标题栏；收起后变成「▢」"),
    ("3", "「✕」彻底关闭面板（后台服务仍在运行，从 App 可再次打开）"),
    ("4", "「当前:」点它变绿，再输游戏里“预算:”后面那个数字"),
    ("5", "「改成:」点它变绿，再输你想要的预算数字"),
    ("6", "自带数字键盘：没有输入框，也不弹系统输入法"),
    ("7", "「应用」开始修改内存里的数值"),
    ("8", "「撤销」对调两个数字再应用一次，用来撤回；「检测」数一下出现几处"),
    ("9", "状态行：显示 root 状态和修改结果"),
]
f_leg = font(23)
f_num = font(21, True)
line_h = 34
legend_h = PAD + len(LEGEND) * line_h + PAD
# Size the canvas so the longest legend line is never clipped.
probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
text_w = max(probe.textlength(n + ". " + t, font=f_leg) for n, t in LEGEND) + PAD * 4
canvas = Image.new("RGB", (int(max(W + PAD * 2 + 40, text_w)), H + PAD + legend_h),
                   (255, 255, 255))
canvas.paste(ann, (PAD, PAD))
dr = ImageDraw.Draw(canvas)

marks = [(1, 60, 54), (2, 455, 54), (3, 555, 54), (4, 35, 134), (5, 330, 134),
         (6, 300, 263), (7, 35, 646), (8, 400, 646), (9, 300, 730)]
for n, x, y in marks:
    cx, cy = PAD + x, PAD + y
    r = 15
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 40, 60),
               outline=(255, 255, 255), width=2)
    t = str(n)
    tb = dr.textbbox((0, 0), t, font=f_num)
    dr.text((cx - (tb[2] - tb[0]) / 2 - tb[0], cy - (tb[3] - tb[1]) / 2 - tb[1]),
            t, font=f_num, fill=(255, 255, 255))

top = PAD + H + PAD
dr.line((PAD, top - 12, W + PAD, top - 12), fill=(210, 210, 210), width=2)
for i, (num, text) in enumerate(LEGEND):
    y = top + i * line_h
    dr.text((PAD, y), num + ".", font=f_leg, fill=(200, 30, 50))
    dr.text((PAD + 34, y), text, font=f_leg, fill=(30, 30, 30))

canvas.save(os.path.join(OUT, "panel-annotated.png"), optimize=True)
print("panel-annotated:", canvas.size)
print("ALL DONE")
