# -*- coding: utf-8 -*-
"""晨间窗 v9 构建脚本：程序化像素画 -> 内嵌 SVG -> index.html
改画改字都在这里改，跑一遍就出新页面。
颜色图例: K=黑 W=白 R=红 Y=黄 B=蓝 G=绿
"""
import math
import pathlib

C = {
    'K': '#1a1a1a', 'W': '#f7f5ef', 'R': '#c0392b',
    'Y': '#e6b800', 'B': '#2e5f8a', 'G': '#3d7a52',
}

# ---------------- 程序化像素画 ----------------

def make_fish(w=46, h=21):
    """椭圆身体 + 叉尾 + 白肚皮 + 大眼睛，朝右。"""
    sil = set()  # 剪影
    cx, cy, rx, ry = 27.0, 10.0, 13.0, 7.5
    for y in range(h):
        for x in range(w):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                sil.add((x, y))
    # 叉尾：上下两个三角
    def tri(p1, p2, p3):
        (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        for y in range(h):
            for x in range(w):
                a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / den
                b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / den
                if a >= 0 and b >= 0 and (1 - a - b) >= 0:
                    sil.add((x, y))
    tri((16, 10), (3, 2), (8, 10))   # 上尾鳍
    tri((16, 10), (3, 18), (8, 10))  # 下尾鳍
    tri((22, 3.5), (28, 0), (30, 4))  # 背鳍
    grid = {}
    for (x, y) in sil:
        edge = any((x + dx, y + dy) not in sil
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            grid[(x, y)] = 'K'
        elif y >= cy + 3 and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
            grid[(x, y)] = 'W'  # 白肚皮（只在椭圆内，尾巴不白）
        else:
            grid[(x, y)] = 'R'
    # 眼睛：白块+黑瞳
    for dy in range(3):
        for dx in range(3):
            grid[(32 + dx, 6 + dy)] = 'W'
    grid[(33, 7)] = 'K'
    # 嘴巴：最右端中间一个小缺口
    right = max(x for (x, y) in sil)
    for y in (10, 11):
        if (right, y) in grid:
            grid[(right, y)] = 'K'
        if (right - 1, y) in grid and grid[(right - 1, y)] != 'K':
            grid[(right - 1, y)] = None  # 豁口
    return grid, w, h

def make_sun(r=5, rays=True):
    d = r * 2 + 5
    c = d // 2
    grid = {}
    for y in range(d):
        for x in range(d):
            dist = math.hypot(x - c + 0.5, y - c + 0.5)
            if dist <= r + 0.9:
                grid[(x, y)] = 'K' if dist > r - 0.4 else 'Y'
    if rays:
        for ang in range(0, 360, 45):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for rr in (r + 2.0, r + 3.2):
                x, y = round(c - 0.5 + dx * rr), round(c - 0.5 + dy * rr)
                grid[(x, y)] = 'Y'
    return grid, d, d

def make_seaweed(strands=((0, 8), (3, 6), (6, 9), (10, 5)), h=10):
    """strands: (x偏移, 高度)。左右摇摆的绿水草。"""
    w = max(x for x, _ in strands) + 3
    grid = {}
    for sx, sh in strands:
        for i in range(sh):
            sway = 1 if (i // 2) % 2 else 0
            y = h - 1 - i
            grid[(sx + sway, y)] = 'G'
            if i % 3 != 2:
                grid[(sx + sway + 1, y)] = 'G'
    return grid, w, h

WAVE = [  # 8x3 循环瓦片，白浪在蓝海
    "...WW...",
    "..W..W..",
    ".W....W.",
]

BIRD = [
    "K...K",
    ".K.K.",
    "..K..",
]

BUBBLE_S = ["WW", "WW"]
BUBBLE_M = ["WWW", "WKW", "WWW"]

# 卦画：山天大畜（艮上乾下）1=阳爻整杠 0=阴爻断杠
GUA_LINES = [1, 0, 0, 1, 1, 1]

# ---------------- SVG 生成 ----------------

def grid_svg(grid, cls='', repeat_x=1, w=None, h=None):
    if isinstance(grid, list):  # ASCII 行
        h = len(grid)
        w = max(len(r) for r in grid)
        cells = {(x, y): ch for y, row in enumerate(grid)
                 for x, ch in enumerate(row) if ch in C}
    else:  # dict {(x,y): ch}
        cells = {k: v for k, v in grid.items() if v in C}
    rects = []
    for rep in range(repeat_x):
        for (x, y), ch in cells.items():
            rects.append(
                f'<rect x="{x + rep * w}" y="{y}" width="1.02" height="1.02" fill="{C[ch]}"/>')
    c = f' class="{cls}"' if cls else ''
    return (f'<svg{c} viewBox="0 0 {w * repeat_x} {h}" shape-rendering="crispEdges" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(rects)}</svg>')

def gua_svg():
    rects = []
    for i, yang in enumerate(GUA_LINES):
        y = i * 2.05
        if yang:
            rects.append(f'<rect x="0" y="{y}" width="11" height="1.25" fill="#1a1a1a"/>')
        else:
            rects.append(f'<rect x="0" y="{y}" width="4.3" height="1.25" fill="#1a1a1a"/>')
            rects.append(f'<rect x="6.7" y="{y}" width="4.3" height="1.25" fill="#1a1a1a"/>')
    return ('<svg class="px-gua" viewBox="0 0 11 11.5" shape-rendering="crispEdges" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(rects)}</svg>')

# ---------------- 页面 ----------------

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>晨间窗</title>
<style>
  /* reTerminal E1002 · E Ink Spectra 6 · v9 像素海风
     六色：黑#1a1a1a 白#f7f5ef 红#c0392b 黄#e6b800 蓝#2e5f8a 绿#3d7a52 */
  :root {{ --u: min(1vw, 1.6667vh); }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width:100%; height:100%; overflow:hidden;
    background:#f7f5ef; color:#1a1a1a;
    font-family:"Noto Serif SC","Songti SC","SimSun",serif; font-weight:700;
  }}
  .frame {{
    width:100%; height:100%;
    border:calc(var(--u)*0.7) solid #1a1a1a;
    padding:calc(var(--u)*1.1) calc(var(--u)*1.6) calc(var(--u)*1.0);
    display:flex; flex-direction:column;
  }}

  /* ---- 顶栏 ---- */
  .topbar {{ display:flex; align-items:baseline; justify-content:space-between; }}
  .date {{ display:flex; align-items:baseline; gap:calc(var(--u)*1.4); }}
  .month-day {{ font-size:calc(var(--u)*4.4); line-height:1; }}
  .weekday {{ font-size:calc(var(--u)*2.2); color:#2e5f8a; letter-spacing:calc(var(--u)*0.4); }}
  .weather {{ font-size:calc(var(--u)*2.0); color:#3d7a52; letter-spacing:calc(var(--u)*0.15); }}

  /* ---- 海景 ---- */
  .scene {{ margin-top:calc(var(--u)*1.0); position:relative; }}
  .sky {{ height:calc(var(--u)*4.2); position:relative; }}
  .sky svg {{ position:absolute; }}
  .bird1 {{ width:calc(var(--u)*3.4); left:14%; top:0; }}
  .bird2 {{ width:calc(var(--u)*2.6); left:25%; top:calc(var(--u)*1.6); }}
  .sun {{ width:calc(var(--u)*7.6); right:3.5%; top:calc(var(--u)*-1.0); }}
  .sea {{
    height:calc(var(--u)*15.5); background:#2e5f8a;
    border:calc(var(--u)*0.45) solid #1a1a1a;
    position:relative; overflow:hidden;
  }}
  .sea svg {{ position:absolute; }}
  .wave1 {{ width:calc(var(--u)*160); left:0; top:calc(var(--u)*0.6); }}
  .wave2 {{ width:calc(var(--u)*160); left:calc(var(--u)*-3); top:calc(var(--u)*2.9); }}
  .fish {{ width:calc(var(--u)*33); left:28%; top:calc(var(--u)*0.55); }}
  .bub1 {{ width:calc(var(--u)*1.5); left:71%; top:calc(var(--u)*1.6); }}
  .bub2 {{ width:calc(var(--u)*2.0); left:74.5%; top:calc(var(--u)*0.4); }}
  .weed1 {{ left:4%; bottom:0; height:calc(var(--u)*5.5); }}
  .weed2 {{ left:86%; bottom:0; height:calc(var(--u)*6.5); }}

  /* ---- 底栏：卦卡 + 引文 ---- */
  .bottom {{ flex:1; min-height:0; display:flex; gap:calc(var(--u)*2.2);
             margin-top:calc(var(--u)*1.2); }}
  .gua-card {{
    width:37%; border:calc(var(--u)*0.45) solid #1a1a1a;
    padding:calc(var(--u)*0.9) calc(var(--u)*1.4);
    display:flex; flex-direction:column; justify-content:center;
  }}
  .gua-head {{ display:flex; align-items:center; gap:calc(var(--u)*1.3); }}
  .gua-title {{ font-size:calc(var(--u)*2.9); color:#c0392b; letter-spacing:calc(var(--u)*0.4); }}
  .px-gua {{ width:calc(var(--u)*6.0); height:auto; flex:none; }}
  .gua-trigrams {{ font-size:calc(var(--u)*1.55); color:#2e5f8a; line-height:1.4; }}
  .gua-text {{ font-size:calc(var(--u)*1.7); line-height:1.55; margin-top:calc(var(--u)*0.8); }}
  .gua-text .lbl {{ color:#c0392b; }}
  .quote {{ flex:1; display:flex; flex-direction:column; justify-content:center; }}
  .quote-text {{ font-size:calc(var(--u)*1.95); line-height:1.58; }}
  .quote-src {{ font-size:calc(var(--u)*1.7); color:#2e5f8a; margin-top:calc(var(--u)*0.6);
                letter-spacing:calc(var(--u)*0.2); }}

  /* ---- 聚焦条 ---- */
  .practice {{
    margin-top:calc(var(--u)*1.1);
    border:calc(var(--u)*0.45) solid #1a1a1a;
    padding:calc(var(--u)*0.8) calc(var(--u)*1.3);
    display:flex; align-items:center;
  }}
  .practice-tag {{
    background:#3d7a52; color:#f7f5ef;
    font-size:calc(var(--u)*1.9); letter-spacing:calc(var(--u)*0.3);
    padding:calc(var(--u)*0.35) calc(var(--u)*1.0);
    margin-right:calc(var(--u)*1.2); white-space:nowrap;
  }}
  .practice-text {{ font-size:calc(var(--u)*1.9); line-height:1.45; }}
</style>
</head>
<body>
  <div class="frame">

    <div class="topbar">
      <div class="date">
        <div class="month-day">9月20日</div>
        <div class="weekday">星期日</div>
      </div>
      <div class="weather">上海 · 晴 · 26°C</div>
    </div>

    <div class="scene">
      <div class="sky">
        {bird1}
        {bird2}
        {sun}
      </div>
      <div class="sea">
        {wave1}
        {wave2}
        {weed1}
        {weed2}
        {fish}
        {bub1}
        {bub2}
      </div>
    </div>

    <div class="bottom">
      <div class="gua-card">
        <div class="gua-head">
          {gua}
          <div>
            <div class="gua-title">山天大畜</div>
            <div class="gua-trigrams">艮上乾下 · 第二十六卦</div>
          </div>
        </div>
        <div class="gua-text">
          <span class="lbl">象曰</span>　天在山中，大畜。<br>
          <span class="lbl">藏</span>　　「陽氣內藏」——慢慢蓄，不必急。
        </div>
      </div>
      <div class="quote">
        <div class="quote-text">
          「真实的东西，本来就已经在那里了。<br>
          承认它，不会让它变得更糟；<br>
          不面对它，它也不会消失。<br>
          正因为它真实，它才是可以与你互动的东西。」
        </div>
        <div class="quote-src">—— 简德林《聚焦》</div>
      </div>
    </div>

    <div class="practice">
      <div class="practice-tag">聚焦</div>
      <div class="practice-text">喝咖啡前，花十秒问问身体：「今天，你想被怎样对待？」不用回答，听一听就好。</div>
    </div>

  </div>
</body>
</html>
"""

def build():
    fish, fw, fh = make_fish()
    sun, sw, sh = make_sun()
    weed, ww, wh = make_seaweed()
    weed2, ww2, wh2 = make_seaweed(strands=((0, 6), (3, 9), (7, 5), (11, 8)))
    html = HTML.format(
        bird1=grid_svg(BIRD, 'bird1'),
        bird2=grid_svg(BIRD, 'bird2'),
        sun=grid_svg(sun, 'sun', w=sw, h=sh),
        wave1=grid_svg(WAVE, 'wave1', repeat_x=40),
        wave2=grid_svg(WAVE, 'wave2', repeat_x=40),
        fish=grid_svg(fish, 'fish', w=fw, h=fh),
        bub1=grid_svg(BUBBLE_S, 'bub1'),
        bub2=grid_svg(BUBBLE_M, 'bub2'),
        weed1=grid_svg(weed, 'weed1', w=ww, h=wh),
        weed2=grid_svg(weed2, 'weed2', w=ww2, h=wh2),
        gua=gua_svg(),
    )
    out = pathlib.Path(__file__).parent / 'index.html'
    out.write_text(html, encoding='utf-8')
    print(f'written {out} ({len(html)} bytes)')

if __name__ == '__main__':
    build()
