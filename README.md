# Serial Video Cover Generator · 视频封面生成器

给系列视频批量出带集数编号的封面。底图只做一次（编号牌留空），编号由页面上的独立文字层实时画上去，改集数不用重新出图。完全离线，在浏览器里直接打开本地 HTML 即可使用。

An offline, single-page cover generator for numbered video series. Artwork is made once with a blank number plate; the episode number is drawn live as a separate text layer and exported as JPG.

## 功能

- 顶部标题栏切换多个系列，每个系列有独立的编号器（`−  #001  +`，始终三位数，0–9999，各自记住上次的编号）。
- 一个款式一行：左 16:9（导出 1920×1080），右 4:3（导出 1440×1080）。每页最多 4 行，新款永远排在第一行。
- 点击图片下载当前编号的 JPG。
- 页面只加载当前页的缩略图，下载时才加载原图，款式再多也能很快打开。

## 快速试用（演示素材由程序生成）

```bash
python -m pip install Pillow
npm run demo            # 生成演示底图并打包到 examples/demo/
```

然后用浏览器打开 `examples/demo/封面生成器.html`。

## 用自己的素材

1. 把无编号底图（PNG）放进 `assets/`。
2. 参考 `examples/catalog.json` 写 `catalog.json`：每个系列一个 `series`，`entries` 按新增时间倒序（第 0 项显示在第一行）。每张图的 `number` 是编号牌在**源图像素**里的中心 `x,y`、旋转角 `angle`、三位数字号 `fontSize`，以及四位数时的最大宽度 `maxWidth`。
3. `python -X utf8 build.py` 生成 `封面生成器.html` 和 `data/`（两者必须放在同一目录）。

新增款式建议用脚本，它会复制素材、插到第一行并重新打包：

```bash
python -X utf8 add_cover.py --series travel --id C --name 新款 \
  --wide final/cover-16x9.png --wide-number 520,780,-4,280,94 \
  --standard final/cover-4x3.png --standard-number 450,820,-5,280,94
```

## 验收

```bash
npm install
npx playwright install chromium   # 或者用系统 Edge（默认）
npm run verify:demo               # PW_CHANNEL=chrome 可改用 Chrome
```

`verify.cjs` 会离线检查编号器加减、两系列编号独立、分页顺序、每张 JPG 的尺寸、回到顶部、手机宽度无横向滚动。

## 目录

| 文件 | 作用 |
| --- | --- |
| `studio.template.html` | 页面界面、绘制与下载逻辑 |
| `build.py` | 打包：生成 HTML 和按需加载的 `data/thumb`、`data/full` |
| `add_cover.py` | 把新定稿插到系列第一行并重新打包 |
| `legacy-render.js` | 早期款式的 SVG 编号定位（保持历史输出逐像素一致） |
| `verify.cjs` | 浏览器验收 |
| `examples/` | 演示目录和占位素材生成脚本 |

个人素材（`assets/`、`catalog.json`、生成的 `data/` 和 HTML）都在 `.gitignore` 里，不会进入仓库。
