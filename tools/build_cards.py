"""Build self-contained, static Profile cards; no image or font requests at runtime."""
from pathlib import Path
import html
import hashlib
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
ASSETS = ROOT / 'assets' / 'cards'
ASSETS.mkdir(exist_ok=True)
PALETTES = {
    'day': dict(paper='#faf9f2', ink='#283e35', muted='#637369', line='#dbe2d6', accent='#7e8051', sky='#eef1df', hill='#c1cdb2', hill2='#8fa98f', leaf='#657e62', trunk='#8b8b73', sun='#ddba7c', button='#2c483c', buttonText='#faf9ed'),
    'night': dict(paper='#15241f', ink='#eeeedf', muted='#bac8bb', line='#344b40', accent='#dbbd83', sky='#1b3231', hill='#294a3b', hill2='#365945', leaf='#7c976f', trunk='#acb4a1', sun='#e4dcc0', button='#ecebd9', buttonText='#233e32'),
}
SANS = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif"
SERIF = "Georgia,'Times New Roman',serif"
OUTPUTS = {}


def text(x, y, value, size=25, color=None, weight=400, family=SANS, italic=False):
    return f'<text x="{x}" y="{y}" fill="{color or P["ink"]}" font-family="{family}" font-size="{size}" font-weight="{weight}"' + (' font-style="italic"' if italic else '') + f'>{html.escape(value)}</text>'


def width(value, size):
    return sum(1 if ord(c) > 255 else .67 if c.isupper() else .56 if c.islower() else .35 if c == ' ' else .50 for c in value) * size


def lines(value, max_width, size):
    if '\n' in value:
        return [line for part in value.split('\n') for line in lines(part,max_width,size)]
    words = re.findall(r'[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)*[，。；：、！？）]*|[\u3400-\u9fff][，。；：、！？）]*|[^A-Za-z0-9]', value)
    result, line = [], ''
    for word in words:
        if line and width(line + word, size) > max_width:
            if word in '，。、；：）' and result and len(line) < 2:
                result[-1] += line + word
                line = ''
                continue
            result.append(line.rstrip())
            line = word.lstrip()
        else:
            line += word
    if line.strip():
        result.append(line.rstrip())
    return result


def paragraph(x, y, value, max_width, size=25, leading=41, color=None):
    items = lines(value, max_width, size)
    return ''.join(text(x, y + i * leading, line, size, color) for i, line in enumerate(items)), y + len(items) * leading


def rule(x1, y, x2):
    return f'<path d="M{x1} {y}H{x2}" stroke="{P["line"]}"/>'


def arrow(x, y, size=18, color=None):
    return f'<path d="M{x} {y + size}l{size} -{size}m-{size} 0h{size}v{size}" fill="none" stroke="{color or P["ink"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'


def button(x, y, label, size=23, h=54):
    w = max(174, width(label, size) + 88)
    return f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{P["button"]}"/>' + text(x + 23, y + h/2 + size*.34, label, size, P['buttonText']) + arrow(x + w - 41, y + h/2 - 8, 15, P['buttonText'])


def tree(x, y, scale=1, opacity=1):
    # Organic branch contours share the woodland palette without reproducing the animated point field.
    out = [f'<g transform="translate({x} {y}) scale({scale})" opacity="{opacity}">']
    for path, stroke in [('M0 0C-7 -44 7 -77 -2 -123C-8 -150 -18 -169 -26 -186',9),('M-2 -81C18 -110 40 -139 61 -177',5),('M-1 -106C-29 -125 -54 -148 -69 -175',5),('M21 -119C23 -148 19 -169 24 -192',4),('M-9 -140C-32 -164 -36 -180 -43 -201',3)]:
        out.append(f'<path d="{path}" fill="none" stroke="{P["trunk"]}" stroke-width="{stroke}" stroke-linecap="round"/>')
    rng = random.Random(872)
    for cx, cy, r in [(-55,-183,35),(-24,-207,37),(15,-201,32),(54,-182,33),(-77,-161,26),(76,-158,24),(29,-168,39),(-13,-172,41)]:
        for i in range(5):
            a=i*math.tau/5;px=cx+math.cos(a)*r*.44;py=cy+math.sin(a)*r*.24;rr=r*(.44+rng.random()*.13)
            out.append(f'<path d="M{px-rr:.1f} {py:.1f}c{-rr*.12:.1f} {-rr:.1f} {rr*1.2:.1f} {-rr*1.18:.1f} {rr*1.77:.1f} {-rr*.48:.1f}c{rr*.8:.1f} {rr*.77:.1f} {-rr*.15:.1f} {rr*1.43:.1f} {-rr*.94:.1f} {rr*1.08:.1f}c{-rr*.6:.1f} {rr*.42:.1f} {-rr*.98:.1f} {-rr*.08:.1f} {-rr*.83:.1f} {-rr*.6:.1f}Z" fill="{P["leaf"]}" opacity="{.28+rng.random()*.28:.2f}"/>')
    out.append('</g>')
    return ''.join(out)


def landscape(x, y, w, h, night, compact=False):
    if compact:
        out=[f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="0 0 480 200" preserveAspectRatio="xMidYMid slice"><rect width="480" height="200" fill="{P["sky"]}"/>']
        if night:
            out.append(f'<path d="M425 24a18 18 0 1 0 22 23a17 17 0 0 1-22-23Z" fill="{P["sun"]}"/>')
            for sx,sy in [(36,34),(86,58),(164,28),(213,63),(329,31),(378,75),(453,91)]:out.append(f'<circle cx="{sx}" cy="{sy}" r="1.3" fill="{P["sun"]}" opacity=".5"/>')
        else:out.append(f'<circle cx="428" cy="40" r="19" fill="{P["sun"]}"/>')
        out += [f'<path d="M-10 153Q132 88 288 149T490 145V210H-10Z" fill="{P["hill"]}"/>',f'<path d="M-10 182Q193 131 306 176T490 166V210H-10Z" fill="{P["hill2"]}"/>',tree(272,184,.57,.95),tree(74,190,.43,.5),'</svg>']
        return ''.join(out)
    out = [f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="0 0 360 310" preserveAspectRatio="xMidYMid slice">', f'<rect width="360" height="310" fill="{P["sky"]}"/>']
    if night:
        rng = random.Random(821)
        for i in range(22):
            out.append(f'<circle cx="{rng.randint(15,350)}" cy="{rng.randint(15,164)}" r="{.7+rng.random()*.8:.1f}" fill="{P["sun"]}" opacity="{.25+rng.random()*.4:.2f}"/>')
        out.append(f'<path d="M279 37a21 21 0 1 0 24 28a20 20 0 0 1-24-28Z" fill="{P["sun"]}"/>')
    else:
        out.append(f'<circle cx="286" cy="59" r="22" fill="{P["sun"]}" opacity=".85"/>')
    out += [f'<path d="M-20 236Q84 134 210 226T390 211V330H-20Z" fill="{P["hill"]}"/>', f'<path d="M-20 267Q140 192 231 257T390 248V330H-20Z" fill="{P["hill2"]}"/>', tree(170,259,.91,.95), tree(333,271,.58,.48), f'<path d="M158 310Q147 272 191 252Q208 241 198 231" fill="none" stroke="{P["paper"]}" stroke-width="8" opacity=".32"/>', '</svg>']
    return ''.join(out)


def shell(kind, w, h, parts, label):
    title = html.escape(label)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{title}</title><defs><clipPath id="card"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26"/></clipPath></defs><g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="{P["paper"]}"/>{"".join(parts)}</g><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="none" stroke="{P["line"]}" stroke-width="1.5"/></svg>'


def build(kind, mobile, night):
    global P
    P = PALETTES['night' if night else 'day']
    w, pad = (480, 28) if mobile else (960, 42)
    parts = []
    if kind == 'intro':
        h = 500 if mobile else 310
        parts += [landscape(0,333,w,h-333,night,compact=True) if mobile else landscape(605,0,355,h,night)]
        if mobile:
            parts += [f'<rect width="480" height="333" fill="{P["paper"]}"/>', text(pad,68,'LHC-PROG',61,family=SERIF,italic=True),text(pad,113,'中南大学',24,P['muted']),text(pad,151,'计算机科学与技术本科生',24,P['muted']),text(pad,206,'具身智能 · 机器学习',26),text(pad,249,'3D 视觉 · 医学影像处理',26),button(pad,278,'访问个人主页',23)]
        else:
            parts += [text(pad,78,'LHC-PROG',66,family=SERIF,italic=True),text(pad,122,DATA['identity'],23,P['muted']),text(pad,171,'具身智能 · 机器学习',25),text(pad,209,'3D 视觉 · 医学影像处理',25),button(pad,236,'访问个人主页',22,h=50)]
    elif kind == 'research':
        y=65
        parts += [text(pad,y,'研究实践',34,weight=600),text(pad,126,'X-VLA × VGGT',45,family=SERIF)]
        if not mobile:parts += [text(w-198,65,'阅读研究',23,P['muted']),arrow(w-66,46,17,P['muted'])]
        desc='跨域 Soft Prompt 共享与 VGGT 几何注入。'
        p,y=paragraph(pad,178,desc,w-2*pad,29 if mobile else 25,46 if mobile else 42);parts.append(p);y+=18
        if mobile:
            entries=[('基线复现','六域部署与系统评测；贯通模型服务、动作转换与结果记录。'),('方法实现','Soft Prompt 蒸馏\n参数级 · 行为级 · 轨迹级\n几何注入\nGI-RGD · GCRP\nSpatial Forcing'),('诊断与追溯','梯度分析、模块隔离与参数替换；交叉诊断损失曲线、表征相关性与 rollout 行为。')]
            for heading,body in entries:
                parts += [rule(pad,y,w-pad),text(pad,y+45,heading,29,weight=600)]
                p,end=paragraph(pad,y+87,body,w-2*pad,29,46,P['muted']);parts.append(p);y=end+24
        else:
            entries=[('基线复现','六域模型部署与系统评测，贯通模型服务、动作转换与结果记录。'),('方法实现','Soft Prompt 蒸馏\n参数 · 行为 · 轨迹\nGI-RGD · GCRP\nSpatial Forcing'),('诊断与追溯','梯度分析、模块隔离与参数替换；表征相关性与 rollout 行为追踪。')]
            parts.append(rule(pad,y,w-pad));bottoms=[]
            for i,(heading,body) in enumerate(entries):
                x=pad+i*300;parts.append(text(x,y+50,heading,27,weight=600));p,end=paragraph(x,y+94,body,260,24,40,P['muted']);parts.append(p);bottoms.append(end)
            y=max(bottoms)+20
        parts += [rule(pad,y,w-pad),text(pad,y+44,'六域评测',25,weight=600)];y+=91
        if mobile:
            for i,name in enumerate(DATA['research']['domains']):
                x=pad+(i%2)*219;row=i//2
                parts.append(text(x,y+row*45,name,28,P['muted']))
            y+=132
            parts.append(button(pad,y,'阅读研究详情',23));y+=82
        else:
            x=pad
            for name in DATA['research']['domains']:
                parts.append(text(x,y,name,23,P['muted']));x+=width(name,23)+29
            y+=39
        h=y+17
    elif kind == 'skills':
        h=392 if mobile else 226
        parts.append(text(pad,62,'技术能力',34,weight=600))
        for i,item in enumerate(DATA['skills']):
            if mobile:
                y=116+i*91;parts += [text(pad,y,item['title'],23,P['muted']),text(pad,y+41,item['tools'],29),rule(pad,y+61,w-pad) if i<2 else '']
            else:
                x=pad+i*300;parts += [text(x,121,item['title'],23,P['muted']),text(x,170,item['tools'],27)]
    else:
        h=460 if mobile else 265
        parts += [landscape(0,310,w,h-310,night,compact=True) if mobile else landscape(605,0,355,h,night)]
        if mobile:parts.append(f'<rect width="480" height="310" fill="{P["paper"]}"/>')
        parts += [text(pad,55,'校园协作 · 2026',23,P['muted']),text(pad,117,'MiniCamp',56,family=SERIF,italic=True)]
        phrase='活动统筹 · 宣传执行' if mobile else '活动统筹 · 宣传执行 · 现场协作 · 赞助对接'
        parts.append(text(pad,164,phrase,25 if mobile else 23))
        if mobile:parts.append(text(pad,204,'现场协作 · 赞助对接',25))
        parts.append(button(pad,233 if mobile else 191,'查看活动官网',23,h=54))
    return shell(kind,w,h,parts,{'intro':'LHC-PROG','research':'研究实践','skills':'技术能力','minicamp':'MiniCamp'}[kind]+' · '+('夜林' if night else '晨光'))


def picture(kind, alt, link=None):
    def image(mobile,night):
        return './assets/cards/'+OUTPUTS[kind,mobile,night]
    value=f'''<picture>
  <source media="(max-width:1000px) and (prefers-color-scheme:dark)" srcset="{image(True,True)}">
  <source media="(max-width:1000px)" srcset="{image(True,False)}">
  <source media="(prefers-color-scheme:dark)" srcset="{image(False,True)}">
  <img src="{image(False,False)}" width="100%" alt="{html.escape(alt,quote=True)}">
</picture>'''
    return f'<a href="{link}" title="{html.escape(alt,quote=True)}">\n{value}\n</a>' if link else value


def main():
    for kind in ['intro','research','skills','minicamp']:
        for mobile in [False,True]:
            for night in [False,True]:
                suffix=('-night' if night else '-day')+('-mobile' if mobile else '')
                content=build(kind,mobile,night)
                name=kind+suffix+'-'+hashlib.sha256(content.encode()).hexdigest()[:10]+'.svg'
                OUTPUTS[kind,mobile,night]=name
                (ASSETS/name).write_text(content,encoding='utf-8',newline='\n')
    for file in ASSETS.glob('*.svg'):
        if re.fullmatch(r'(intro|research|skills|minicamp)-(day|night)(-mobile)?(-[a-f0-9]{10})?\.svg',file.name) and file.name not in OUTPUTS.values():
            file.unlink()
    cards=[
        picture('intro','LHC-PROG · 中南大学计算机科学与技术本科生。具身智能、机器学习、3D 视觉、医学影像处理。访问个人主页 ↗','https://lhc-prog.github.io/'),
        picture('research','研究实践 · X-VLA 跨域 Soft Prompt 共享与 VGGT 几何注入；六域部署、方法实现、诊断与追溯。阅读研究详情 ↗','https://lhc-prog.github.io/#research'),
        picture('skills','技术能力：Python、C/C++、Java、PyTorch、Linux、Git。'),
        picture('minicamp','MiniCamp 2026 校园黑客松 · 活动统筹、宣传、现场执行与赞助对接。查看活动官网 ↗',DATA['practice']['url']),
    ]
    body='\n\n'.join('<p>\n'+card+'\n</p>' for card in cards)
    native=['<details>','<summary>文字介绍</summary>','','中南大学 · 计算机科学与技术本科生','',' · '.join(DATA['interests']),'','## 研究实践','',DATA['research']['description'],'','覆盖六域：'+' · '.join(DATA['research']['domains']),'']
    native += ['- **'+i['title']+'** — '+i['text'] for i in DATA['research']['contributions']]
    native += ['','## 主要发现','']+['- **'+i['title']+'** — '+i['text'] for i in DATA['research']['findings']]
    native += ['','## 技术能力','','Python · C/C++ · Java · PyTorch · Linux · Git','','## 协作实践','','MiniCamp 2026 校园黑客松。'+DATA['practice']['description'],'','</details>']
    body+='\n\n'+'\n'.join(native)+'\n'
    (ROOT/'README.md').write_text(body,encoding='utf-8',newline='\n')
    total=sum((ASSETS/OUTPUTS[kind,False,False]).stat().st_size for kind in ['intro','research','skills','minicamp'])
    print('Four static cards; desktop day payload:',total,'bytes; mobile, light and dark variants generated.')


if __name__=='__main__':
    main()
