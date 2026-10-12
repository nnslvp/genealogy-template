# -*- coding: utf-8 -*-
"""Собирает tree/tree.html из tree/tree.json и tree/template.html. Запуск: python3 tree/build_html.py"""
import json, os, datetime
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
d = json.load(open('tree/tree.json', encoding='utf-8'))
cfg = json.load(open('tree/config.json', encoding='utf-8'))
t = open('tree/template.html', encoding='utf-8').read()
n = len(d['persons']); f = len(d['families'])
rep = {
    '__DATA__': json.dumps(d, ensure_ascii=False),
    '__COUNT__': f'{n} человек и {f} семей',
    '__DATE__': datetime.date.today().strftime('%d.%m.%Y'),
    '__ROOTNAME__': cfg.get('root_name', 'заявитель'),
    '__GED__': cfg.get('ged', 'family.ged'),
    '__FAMILY__': cfg.get('family', ''),
    '__PLACES__': cfg.get('places', ''),
}
for k, v in rep.items():
    t = t.replace(k, v)
open('tree/tree.html', 'w', encoding='utf-8').write(t)
print('tree.html', n, f)
