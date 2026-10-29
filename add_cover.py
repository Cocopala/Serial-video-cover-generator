"""把定稿的无编号封面插入生成器第一行（最新在最上），然后重新打包。

用法示例（坐标都是源图像素，编号牌中心点）：
  python add_cover.py --series travel --id C \
      --wide final/cover-16x9.png --wide-number 520,780,-4,280,94 \
      --standard final/cover-4x3.png --standard-number 450,820,-5,280,94

--*-number 格式：x,y,angle,maxWidth,fontSize
  x,y      编号牌中心（源图像素）   angle    旋转角度（度，逆时针为负）
  maxWidth 文字最大宽度（四位数会自动缩小到这个宽度内）   fontSize 三位数时的字号
"""
from pathlib import Path
import argparse, datetime, hashlib, json, shutil, subprocess, sys

root = Path(__file__).parent
catalog_path = root / 'catalog.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def parse_number(text, args):
    try:
        x, y, angle, max_width, size = (float(v) for v in text.split(','))
    except ValueError:
        sys.exit(f'编号定位格式应为 x,y,angle,maxWidth,fontSize：{text}')
    spec = {'x': x, 'y': y, 'angle': angle, 'maxWidth': max_width, 'fontSize': size}
    spec = {k: int(v) if v == int(v) else v for k, v in spec.items()}
    if args.fill: spec['fill'] = args.fill
    if args.stroke: spec['stroke'] = args.stroke
    if args.stroke_width: spec['strokeWidth'] = args.stroke_width
    if args.italic is not None: spec['italic'] = args.italic
    return spec


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--series', required=True, help='系列 id（见 catalog.json 的 series.id）')
p.add_argument('--id', required=True, help='款式短 ID，行首显示，例如 G 或角色名；同系列不能重复')
p.add_argument('--name', help='款式说明，默认等于 id，例如 漫画-特写')
p.add_argument('--wide', help='16:9 无编号定稿 PNG')
p.add_argument('--wide-number', help='16:9 编号定位')
p.add_argument('--standard', help='4:3 无编号定稿 PNG')
p.add_argument('--standard-number', help='4:3 编号定位')
p.add_argument('--fill'); p.add_argument('--stroke'); p.add_argument('--stroke-width', type=float)
p.add_argument('--italic', action=argparse.BooleanOptionalAction, default=None)
p.add_argument('--dry-run', action='store_true', help='只检查并打印，不写文件')
args = p.parse_args()

catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
series = next((s for s in catalog['series'] if s['id'] == args.series), None)
if not series:
    sys.exit('未知系列：' + args.series + '；可选：' + ', '.join(s['id'] for s in catalog['series']))
if any(e['id'] == args.id for e in series['entries']):
    sys.exit(f'{args.series} 已有款式 {args.id}。新版本请换新 ID；确需替换旧款时请手动修改 catalog.json。')

covers, copies = {}, []
for ratio, src, num, tag in [('16:9', args.wide, args.wide_number, '16x9'), ('4:3', args.standard, args.standard_number, '4x3')]:
    if not src:
        continue
    src = Path(src)
    if not src.is_file():
        sys.exit(f'找不到 {ratio} 定稿：{src}')
    if not num:
        sys.exit(f'{ratio} 缺少 --{"wide" if tag == "16x9" else "standard"}-number 编号定位')
    name = f'{args.series}-{args.id}-{tag}-无编号.png'
    dest = root / 'assets' / name
    if dest.exists() and sha(dest) != sha(src):
        sys.exit(f'目标素材已存在且内容不同：{dest}')
    covers[ratio] = {'asset': name, 'number': parse_number(num, args)}
    copies.append((src, dest))
if not covers:
    sys.exit('至少提供 --wide 或 --standard 其中一张')

entry = {'id': args.id, 'name': args.name or args.id, 'added': datetime.date.today().isoformat(), 'covers': covers}
print(json.dumps(entry, ensure_ascii=False, indent=2))
if args.dry_run:
    sys.exit(0)

for src, dest in copies:
    shutil.copy2(src, dest)
    print('复制', src, '->', dest, 'SHA256', sha(dest))
series['entries'].insert(0, entry)  # 最新永远放第一行，旧款依次下移
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'已插入 {args.series} 第 1 行；该系列共 {len(series["entries"])} 款')
subprocess.run([sys.executable, '-X', 'utf8', str(root / 'build.py')], check=True)
print('下一步：node verify.cjs，并打开 validation/ 里该款 #9999 导出图确认编号落在牌面中央。')
