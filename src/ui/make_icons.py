"""
Generates the UI icon set in src/images/ui/ (dev tool, needs Pillow).

    python src/ui/make_icons.py

Every icon is drawn as simple strokes on a 24-unit grid, rendered at 4x and
downsampled, so all icons share one line weight and style. Each icon is
written in several colours (one per button style) because Tk cannot recolour
images at runtime.
"""
from pathlib import Path
from PIL import Image, ImageDraw

SIZE  = 18                     # final px
SCALE = 4
U     = SIZE * SCALE / 24      # px per grid unit
W     = round(2 * U)           # stroke width

COLOURS = {
    "light":    "#e6edf3",     # secondary buttons   (theme.TEXT)
    "dark":     "#0e1117",     # primary buttons     (theme.ON_ACCENT)
    "white":    "#ffffff",     # danger buttons      (theme.ON_DANGER)
    "disabled": "#7d8ba0",     # any disabled button (theme.TEXT_DISABLED)
}

OUT = Path(__file__).resolve().parent.parent / "images" / "ui"


def P(*pts):
    return [(x * U, y * U) for x, y in pts]


def line(d, c, *pts):
    d.line(P(*pts), fill=c, width=W, joint="curve")
    for x, y in pts:                                   # round caps
        r = W / 2
        d.ellipse((x * U - r, y * U - r, x * U + r, y * U + r), fill=c)


def rect(d, c, x0, y0, x1, y1, r=2, fill=False):
    d.rounded_rectangle(P((x0, y0), (x1, y1)), radius=r * U, outline=c, width=W,
                        fill=c if fill else None)


def circle(d, c, cx, cy, r, fill=False):
    d.ellipse(P((cx - r, cy - r), (cx + r, cy + r)), outline=c, width=W, fill=c if fill else None)


def arc(d, c, cx, cy, r, start, end):
    d.arc(P((cx - r, cy - r), (cx + r, cy + r)), start, end, fill=c, width=W)


def person(d, c, dx=0):
    circle(d, c, 9 + dx, 8, 3.5)
    arc(d, c, 9 + dx, 21, 7, 200, 340)


ICONS = {
    "message": lambda d, c: (rect(d, c, 3, 4, 21, 16, 3), line(d, c, (8, 16), (6, 20), (12, 16)),
                             line(d, c, (7.5, 8.5), (16.5, 8.5)), line(d, c, (7.5, 12), (13, 12))),
    "lock": lambda d, c: (rect(d, c, 5, 11, 19, 21, 2), arc(d, c, 12, 11, 4.5, 180, 360),
                          line(d, c, (7.5, 11), (7.5, 9.5)), line(d, c, (16.5, 11), (16.5, 9.5)),
                          line(d, c, (12, 15), (12, 17))),
    "power": lambda d, c: (arc(d, c, 12, 13, 8, 300, 240), line(d, c, (12, 3), (12, 12))),
    "user_lock": lambda d, c: (person(d, c, -1), rect(d, c, 15, 15.5, 22, 21, 1),
                               arc(d, c, 18.5, 15.5, 2.2, 180, 360)),
    "user_unlock": lambda d, c: (person(d, c, -1), rect(d, c, 15, 15.5, 22, 21, 1),
                                 arc(d, c, 18.5, 13.5, 2.2, 180, 330)),
    "key": lambda d, c: (circle(d, c, 8, 15, 4.5), line(d, c, (11.2, 11.8), (20, 3)),
                         line(d, c, (17, 6), (20, 9)), line(d, c, (14.5, 8.5), (16.5, 10.5))),
    "user_add": lambda d, c: (person(d, c, -1), line(d, c, (19, 9), (19, 15)), line(d, c, (16, 12), (22, 12))),
    "user_del": lambda d, c: (person(d, c, -1), line(d, c, (16.5, 9.5), (21.5, 14.5)),
                              line(d, c, (21.5, 9.5), (16.5, 14.5))),
    "play": lambda d, c: d.polygon(P((7, 4), (19, 12), (7, 20)), fill=c),
    "stop": lambda d, c: rect(d, c, 6, 6, 18, 18, 2, fill=True),
    "refresh": lambda d, c: (arc(d, c, 12, 12, 8, 30, 300), d.polygon(P((19.5, 3.5), (20.5, 10.5), (13.5, 8.5)), fill=c)),
    "upload": lambda d, c: (line(d, c, (12, 16), (12, 4)), line(d, c, (7, 9), (12, 4), (17, 9)),
                            line(d, c, (4, 16), (4, 20), (20, 20), (20, 16))),
    "upload_root": lambda d, c: (line(d, c, (9, 15), (9, 4)), line(d, c, (5, 8), (9, 4), (13, 8)),
                                 line(d, c, (3, 15), (3, 20), (12, 20)),
                                 line(d, c, (18, 11), (22, 12.5), (22, 16), (18, 21), (14, 16), (14, 12.5), (18, 11))),
    "download": lambda d, c: (line(d, c, (12, 4), (12, 15)), line(d, c, (7, 10), (12, 15), (17, 10)),
                              line(d, c, (4, 16), (4, 20), (20, 20), (20, 16))),
    "folder_download": lambda d, c: (line(d, c, (3, 6), (3, 19), (21, 19), (21, 8), (11, 8), (9, 5), (3, 5), (3, 6)),
                                     line(d, c, (12, 10.5), (12, 16)), line(d, c, (9.5, 13.5), (12, 16), (14.5, 13.5))),
    "folder": lambda d, c: line(d, c, (3, 6), (3, 19), (21, 19), (21, 8), (11, 8), (9, 5), (3, 5), (3, 6)),
    "terminal": lambda d, c: (rect(d, c, 3, 4, 21, 20, 2), line(d, c, (7, 9), (10, 12), (7, 15)),
                              line(d, c, (12, 15), (16, 15))),
    "connect": lambda d, c: (line(d, c, (3, 12), (14, 12)), line(d, c, (10, 8), (14, 12), (10, 16)),
                             line(d, c, (14, 4), (20, 4), (20, 20), (14, 20))),
    "help": lambda d, c: (circle(d, c, 12, 12, 9), arc(d, c, 12, 9.5, 3, 190, 400),
                          line(d, c, (12, 13), (12, 14)), line(d, c, (12, 17), (12, 17))),
    "exit": lambda d, c: (line(d, c, (10, 4), (4, 4), (4, 20), (10, 20)), line(d, c, (9, 12), (20, 12)),
                          line(d, c, (16, 8), (20, 12), (16, 16))),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in ICONS.items():
        for variant, colour in COLOURS.items():
            big = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
            draw(ImageDraw.Draw(big), colour)
            big.resize((SIZE, SIZE), Image.LANCZOS).save(OUT / f"{name}_{variant}.png")
    print(f"wrote {len(ICONS) * len(COLOURS)} icons to {OUT}")


if __name__ == "__main__":
    main()
