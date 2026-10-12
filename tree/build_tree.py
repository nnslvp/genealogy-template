# -*- coding: utf-8 -*-
"""Строит tree/tree.json и GEDCOM из карточек persons/*.md.
Запуск из корня проекта: python3 tree/build_tree.py && python3 tree/build_html.py

Читает из каждой карточки:
  front matter: id, name, sex, birth, death, birthplace, status (v = документ, y = со слов, h = гипотеза)
  раздел «## Родство»: строки «- Родители: [[a]], [[b]]», «- Супруг(а): [[x]]», «- Дети: [[c]], [[d]]»
Ключ человека = имя файла без .md. Файлы README.md и _*.md пропускаются.
Настройки (корень дерева, имя, фамилия, места) — tree/config.json.
"""
import json, re, glob, os, datetime, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)
CFG = json.load(open('tree/config.json', encoding='utf-8'))

FM_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.S)
LINK_RE = re.compile(r'\[\[([^\]|]+)\]\]')

def parse_card(path):
    key = os.path.basename(path)[:-3]
    text = open(path, encoding='utf-8').read()
    fm = {}
    m = FM_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.split('#')[0].strip()
    st = fm.get('status') or ('v' if '| ✅' in text else 'y')
    if st not in ('v', 'y', 'h'):
        st = 'y'
    person = dict(id=key, name=fm.get('name') or key, sex=fm.get('sex', '').upper()[:1] or 'U',
                  birth=fm.get('birth', ''), death=fm.get('death', ''), place=fm.get('birthplace', ''),
                  st=st, note=fm.get('note', ''), card=True)
    rel = dict(parents=[], spouses=[], children=[])
    sec = re.search(r'^## Родство\s*\n(.*?)(?=^## |\Z)', text, re.S | re.M)
    if sec:
        for line in sec.group(1).splitlines():
            low = line.lower()
            links = [l.strip() for l in LINK_RE.findall(line) if l.strip()]
            if 'родител' in low or 'отец' in low or 'мать' in low:
                rel['parents'] += links
            elif 'супруг' in low or 'жена' in low or 'муж' in low:
                rel['spouses'] += links
            elif 'дети' in low or 'сын' in low or 'дочь' in low:
                rel['children'] += links
    return key, person, rel

P, REL = {}, {}
for path in sorted(glob.glob('persons/*.md')):
    base = os.path.basename(path)
    if base == 'README.md' or base.startswith('_'):
        continue
    key, person, rel = parse_card(path)
    P[key] = person
    REL[key] = rel

# Ссылки на несуществующие карточки — заглушки без файла (card=False), чтобы дерево не рвалось.
missing = set()
for k, r in REL.items():
    for x in r['parents'] + r['spouses'] + r['children']:
        if x not in P:
            missing.add(x)
for x in sorted(missing):
    P[x] = dict(id=x, name=x.replace('-', ' '), sex='U', birth='', death='', place='', st='h', note='карточки нет', card=False)
    REL[x] = dict(parents=[], spouses=[], children=[])

# Дети по родителям: объединяем «Родители» у ребёнка и «Дети» у родителя.
parents_of = {k: list(dict.fromkeys(r['parents'])) for k, r in REL.items()}
for k, r in REL.items():
    for c in r['children']:
        if k not in parents_of.setdefault(c, []):
            parents_of[c].append(k)

def split_hw(ids):
    h = w = None
    for i in ids:
        s = P[i]['sex']
        if s == 'M' and not h: h = i
        elif s == 'F' and not w: w = i
        elif not h: h = i
        elif not w: w = i
    return h, w

fams = {}  # (h, w) -> children
for c, pr in parents_of.items():
    if not pr:
        continue
    h, w = split_hw(pr[:2])
    fams.setdefault((h, w), [])
    if c not in fams[(h, w)]:
        fams[(h, w)].append(c)
for k, r in REL.items():
    for s in r['spouses']:
        h, w = split_hw([k, s])
        if (h, w) not in fams and (w, h) not in fams:
            fams[(h, w)] = []

def gdate(s):
    s = (s or '').strip()
    m = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', s)
    if m:
        mon = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'][int(m.group(2)) - 1]
        return f'{int(m.group(1))} {mon} {m.group(3)}'
    m = re.search(r'(\d{4})', s)
    if m:
        return ('ABT ' if any(x in s for x in ('ок', '~', '?', '±')) else '') + m.group(1)
    return s

F = [dict(h=h, w=w, ch=ch) for (h, w), ch in fams.items()]
fam_of_child, fam_of_spouse = {}, {}
for n, f in enumerate(F, 1):
    for c in f['ch']: fam_of_child.setdefault(c, []).append(n)
    for s in (f['h'], f['w']):
        if s: fam_of_spouse.setdefault(s, []).append(n)

keys = list(P)
num = {k: i + 1 for i, k in enumerate(keys)}
out = ['0 HEAD', '1 SOUR genealogy-template', '1 GEDC', '2 VERS 5.5.1', '2 FORM LINEAGE-LINKED', '1 CHAR UTF-8',
       f'1 DATE {datetime.date.today().strftime("%d %b %Y").upper()}']
for k in keys:
    p = P[k]
    out += [f'0 @I{num[k]}@ INDI', f'1 NAME {p["name"]}', f'1 SEX {p["sex"] if p["sex"] in "MF" else "U"}']
    if p['birth'] or p['place']:
        out.append('1 BIRT')
        if p['birth']: out.append(f'2 DATE {gdate(p["birth"])}')
        if p['place']: out.append(f'2 PLAC {p["place"]}')
    if p['death']:
        out += ['1 DEAT', f'2 DATE {gdate(p["death"])}']
    note = {'v': 'документ', 'y': 'со слов родни / чужое дерево', 'h': 'гипотеза'}[p['st']]
    out.append(f'1 NOTE Статус: {note}. Карточка: persons/{k}.md' if p['card'] else f'1 NOTE Статус: {note}. Карточки нет')
    for n in fam_of_child.get(k, []): out.append(f'1 FAMC @F{n}@')
    for n in fam_of_spouse.get(k, []): out.append(f'1 FAMS @F{n}@')
for n, f in enumerate(F, 1):
    out.append(f'0 @F{n}@ FAM')
    if f['h']: out.append(f'1 HUSB @I{num[f["h"]]}@')
    if f['w']: out.append(f'1 WIFE @I{num[f["w"]]}@')
    for c in f['ch']: out.append(f'1 CHIL @I{num[c]}@')
out.append('0 TRLR')

ged = CFG.get('ged', 'family.ged')
open(f'tree/{ged}', 'w', encoding='utf-8').write('\n'.join(out) + '\n')

root = CFG['root']
if root not in P:
    print(f'ВНИМАНИЕ: корень {root} из tree/config.json не найден среди карточек', file=sys.stderr)
data = dict(persons=P, families=F, hyp=[],
            root=root, rootName=CFG.get('root_name', ''), rootGen=CFG.get('root_name_gen', ''),
            lineP=CFG.get('lineP', []), lineM=CFG.get('lineM', []), empty=CFG.get('empty', {}))
json.dump(data, open('tree/tree.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(P), 'persons,', len(F), 'families,', len(missing), 'без карточки')
