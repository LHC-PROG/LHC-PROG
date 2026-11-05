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
KINDS = ['intro','about']


from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

FONT_DATA={}
for key,filename in [('cn','ma-shan-zheng-profile.ttf'),('en','fraunces-italic.woff2')]:
    font=TTFont(ROOT/'tools'/'fonts'/filename)
    FONT_DATA[key]=(font,font.getGlyphSet(),font.getBestCmap(),font['head'].unitsPerEm)
OUTLINE_DEFS={}


def text(x,y,value,size=25,color=None,weight=400,family=SANS,italic=False):
    cursor=0;parts=[]
    for ch in value:
        if ch=='·':
            parts.append(f'<circle cx="{cursor+size*.24:.2f}" cy="{-size*.31:.2f}" r="{size*.045:.2f}"/>');cursor+=size*.48;continue
        key='cn' if ord(ch)>255 else 'en'
        font,glyphs,cmap,units=FONT_DATA[key]
        if ord(ch) not in cmap:raise ValueError('Missing artistic glyph: '+ch)
        name=cmap[ord(ch)];gid='glyph-'+key+'-'+format(ord(ch),'x');scale=size/units
        if gid not in OUTLINE_DEFS:
            pen=SVGPathPen(glyphs,ntos=lambda v:format(v,'.2f').rstrip('0').rstrip('.') if v else '0')
            glyphs[name].draw(pen);OUTLINE_DEFS[gid]=f'<path id="{gid}" d="{pen.getCommands()}"/>'
        parts.append(f'<use href="#{gid}" transform="translate({cursor:.2f} 0) scale({scale:.6f} {-scale:.6f})"/>')
        cursor+=font['hmtx'][name][0]*scale
    return f'<g data-label="{html.escape(value,quote=True)}" aria-label="{html.escape(value,quote=True)}" fill="{color or P["ink"]}" transform="translate({x} {y})">'+''.join(parts)+'</g>'


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
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{title}</title><defs>{"".join(OUTLINE_DEFS.values())}<clipPath id="card"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26"/></clipPath></defs><g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="{P["paper"]}"/>{"".join(parts)}</g><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="none" stroke="{P["line"]}" stroke-width="1.5"/></svg>'


def invitation(x,y,label,size=29):
    w=max(272,width(label,size)+104);h=64;top=y-43
    return f'<rect x="{x}" y="{top}" width="{w}" height="{h}" rx="{h/2}" fill="#fcfaef" stroke="{P["line"]}"/>'+text(x+27,y,label,size,'#243d32')+arrow(x+w-43,top+22,18,'#243d32')


def build(kind,mobile,night):
    global P
    OUTLINE_DEFS.clear()
    P=PALETTES['night' if night else 'day']
    w,pad=(480,28) if mobile else (960,42)
    if kind=='intro':
        h=500 if mobile else 330
        art=landscape(0,328,w,172,night,compact=True) if mobile else landscape(605,0,355,h,night)
        parts=[art,text(pad,81 if mobile else 92,DATA['name'],62 if mobile else 76,family=SERIF,italic=True),text(pad,139 if mobile else 156,DATA['identity'],29,P['muted']),text(pad,185 if mobile else 202,DATA['major'],29,P['muted']),invitation(pad,275 if mobile else 275,'进入个人主页',30 if mobile else 29)]
    else:
        h=350 if mobile else 230
        if mobile:
            parts=[text(pad,58,'研究兴趣',26,P['accent']),text(pad,112,'具身智能 · 3D 视觉',30),text(pad,157,'医学影像处理',32),rule(pad,194,w-pad),text(pad,246,DATA['hobby_label'],28,P['accent']),text(pad,300,' · '.join(DATA['hobbies']),29)]
        else:
            parts=[tree(895,286,.55,.14),text(pad,86,'研究兴趣',25,P['accent']),text(192,86,' · '.join(DATA['interests']),30),rule(pad,121,w-pad),text(pad,178,DATA['hobby_label'],27,P['accent']),text(192,178,' · '.join(DATA['hobbies']),30)]
    return shell(kind,w,h,parts,DATA['name']+' · '+('夜林' if night else '晨光'))


def picture(kind,alt,link=None):
    def asset(mobile,night):return './assets/cards/'+OUTPUTS[kind,mobile,night]
    content=f'''<picture>
  <source media="(max-width:1000px) and (prefers-color-scheme:dark)" srcset="{asset(True,True)}">
  <source media="(max-width:1000px)" srcset="{asset(True,False)}">
  <source media="(prefers-color-scheme:dark)" srcset="{asset(False,True)}">
  <img src="{asset(False,False)}" width="100%" alt="{html.escape(alt,quote=True)}">
</picture>'''
    return f'<a href="{link}" title="{html.escape(alt,quote=True)}">\n{content}\n</a>' if link else content


def main():
    for kind in KINDS:
        for mobile in [False,True]:
            for night in [False,True]:
                content=build(kind,mobile,night)
                name=kind+('-night' if night else '-day')+('-mobile' if mobile else '')+'-'+hashlib.sha256(content.encode()).hexdigest()[:10]+'.svg'
                OUTPUTS[kind,mobile,night]=name
                (ASSETS/name).write_text(content,encoding='utf-8',newline='\n')
    # Delete only generator-owned card names inside this repository's card directory.
    assert ASSETS.resolve().is_relative_to(ROOT.resolve())
    for file in ASSETS.glob('*.svg'):
        if re.fullmatch(r'(intro|about|research|skills|vision3d|medical|minicamp)-(day|night)(-mobile)?(-[a-f0-9]{10})?\.svg',file.name) and file.name not in OUTPUTS.values():file.unlink()
    cards=[picture('intro','LHC-PROG · 中南大学 · 24级本科生 · 计算机科学与技术。点击进入我的个人主页。',DATA['homepage']),picture('about','研究兴趣：具身智能、3D 视觉、医学影像处理。My热爱：创造、游戏、咖啡、音乐。')]
    (ROOT/'README.md').write_text('\n\n'.join('<p>\n'+card+'\n</p>' for card in cards)+'\n',encoding='utf-8',newline='\n')
    total=sum((ASSETS/OUTPUTS[k,False,False]).stat().st_size for k in KINDS)
    print('Two static cards; desktop day payload:',total,'bytes; light, dark and mobile variants generated.')


if __name__=='__main__':main()
