"""生成演示用占位底图（纯程序绘制，无版权素材），写到 examples/assets/。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).parent / 'assets'
out.mkdir(exist_ok=True)
SPECS = [  # 文件名, 尺寸, 两端颜色, 标题, 空白编号牌 (中心x, 中心y, 宽, 高)
    ('demo-sunset-16x9.png', (1672, 941), ((255, 140, 66), (120, 40, 140)), 'SUNSET EPISODES', (500, 780, 340, 120)),
    ('demo-sunset-4x3.png', (1448, 1086), ((255, 140, 66), (120, 40, 140)), 'SUNSET', (420, 860, 340, 120)),
    ('demo-ocean-16x9.png', (1672, 941), ((40, 180, 200), (20, 40, 110)), 'OCEAN LOG', (1170, 780, 340, 120)),
    ('demo-ocean-4x3.png', (1448, 1086), ((40, 180, 200), (20, 40, 110)), 'OCEAN', (1020, 860, 340, 120)),
    ('demo-forest-16x9.png', (1672, 941), ((150, 210, 90), (20, 70, 50)), 'FOREST DIARY', (836, 790, 340, 120)),
]
for name, (w, h), (c1, c2), title, (cx, cy, pw, ph) in SPECS:
    im = Image.new('RGB', (w, h))
    px = im.load()
    for y in range(h):
        t = y / (h - 1)
        row = tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))
        for x in range(w):
            px[x, y] = row
    d = ImageDraw.Draw(im)
    for i in range(0, w + h, 90):  # 斜线纹理
        d.line([(i, 0), (i - h, h)], fill=tuple(min(255, v + 18) for v in c1), width=18)
    font = ImageFont.load_default(size=round(h * 0.12))
    d.text((w / 2, h * 0.3), title, font=font, anchor='mm', fill='white', stroke_width=8, stroke_fill=(20, 20, 30))
    d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], radius=18, fill=(22, 28, 36), outline=(255, 230, 120), width=8)
    im.save(out / name)
    print('wrote', out / name)
