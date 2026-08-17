# -*- coding: utf-8 -*-
"""把 gen/*.json 的批次產出合併進 prompt-templates.json。
合併前做正規化 + 六道驗收，任何一道不過就中止，不寫入。
"""
import json, glob, re, sys, shutil, datetime, collections, os

WORK = os.path.expanduser('~/insurance-allinone-work')
MAIN = f'{WORK}/prompt-templates.json'
BANNED = ['賦能', '底層邏輯', '顆粒度', '範式', '視頻', '軟件']
RCE = ['【角色 Role】', '【情境 Context】', '【期望 Expectation】']

def norm_placeholders(t):
    """<<<id>>> → <<<{id}>>>（agent 常漏大括號）。已正確的不動。"""
    sids = {s['id'] for s in t['structure']}
    def fix(m):
        inner = m.group(1)
        if inner.startswith('{'):
            return m.group(0)
        return '<<<{' + inner + '}>>>' if inner in sids else m.group(0)
    t['template'] = re.sub(r'<<<([^>]+)>>>', fix, t['template'])
    return t

def main():
    main_data = json.load(open(MAIN, encoding='utf-8'))
    old_ids = {x.get('id') for x in main_data}
    old_names = {x.get('name') for x in main_data}

    files = sorted(f for f in glob.glob(f'{WORK}/gen/*.json'))
    new, errs, warns = [], [], []
    seen_ids, seen_names = set(), set()

    for f in files:
        base = os.path.basename(f)
        try:
            batch = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            errs.append(f'{base} JSON 壞掉: {e}'); continue
        if not isinstance(batch, list):
            errs.append(f'{base} 不是陣列'); continue

        for t in batch:
            tid = t.get('id', '?')
            tag = f'{base}/{tid}'
            for k in ('id','name','category','industry','department','structure','template'):
                if k not in t: errs.append(f'{tag} 缺欄位 {k}')
            if any(k not in t for k in ('id','name','structure','template','category')):
                continue

            norm_placeholders(t)

            # 1 id / name 不得與站上或彼此重複
            if tid in old_ids:   errs.append(f'{tag} id 與站上既有重複')
            if tid in seen_ids:  errs.append(f'{tag} id 與其他新增重複')
            if t['name'] in old_names: errs.append(f'{tag} 名稱與站上既有重複：{t["name"]}')
            if t['name'] in seen_names: errs.append(f'{tag} 名稱與其他新增重複：{t["name"]}')
            seen_ids.add(tid); seen_names.add(t['name'])

            # 2 id 格式
            if not re.fullmatch(r'[a-z0-9_]+', tid):
                errs.append(f'{tag} id 非 ascii 小寫底線')

            # 3 欄位 ↔ 佔位符 完全對應
            sids = {s['id'] for s in t['structure']}
            used = set(re.findall(r'<<<\{(\w+)\}>>>', t['template']))
            for s in sids - used: errs.append(f'{tag} 欄位 {s} 沒被 template 使用')
            for u in used - sids: errs.append(f'{tag} template 用了不存在的欄位 {u}')
            if re.search(r'<<<(?!\{)[^>]+>>>', t['template']):
                errs.append(f'{tag} 仍有未正規化的佔位符')

            # 4 欄位規格
            if not (2 <= len(t['structure']) <= 6):
                warns.append(f'{tag} 欄位數 {len(t["structure"])}（建議 3-4）')
            for s in t['structure']:
                if s.get('type') not in ('text','textarea'):
                    errs.append(f'{tag} 欄位 {s.get("id")} type 不合法')
                if not re.fullmatch(r'[a-z0-9_]+', str(s.get('id',''))):
                    errs.append(f'{tag} 欄位 id 非 ascii: {s.get("id")}')
                if len(s.get('placeholder','')) < 40:
                    errs.append(f'{tag} 欄位 {s.get("id")} placeholder 太短（<40 字，等於沒教怎麼填）')
                if not s.get('label'):
                    errs.append(f'{tag} 欄位 {s.get("id")} 沒有 label')

            # 5 RCE 與長度
            for r in RCE:
                if r not in t['template']: errs.append(f'{tag} 缺 {r}')
            if len(t['template']) < 500:
                errs.append(f'{tag} template 僅 {len(t["template"])} 字（需 ≥500）')

            # 6 禁用詞
            for b in BANNED:
                if b in t['template'] or b in t['name']:
                    errs.append(f'{tag} 出現禁用詞「{b}」')

            t.setdefault('industry', ['保險'])
            t.setdefault('department', ['業務'])
            new.append(t)

    print(f'讀入批次檔 {len(files)} 個，提示詞 {len(new)} 支')
    if warns:
        print(f'\n⚠️  提醒 {len(warns)} 則：')
        for w in warns[:15]: print('  ', w)
    if errs:
        print(f'\n❌ 驗收未過，共 {len(errs)} 個問題（未寫入任何東西）：')
        for e in errs[:60]: print('  ', e)
        if len(errs) > 60: print(f'   …還有 {len(errs)-60} 個')
        sys.exit(1)

    print('\n✅ 六道驗收全過')
    shutil.copy(MAIN, f'{MAIN}.bak-{datetime.datetime.now():%Y%m%d-%H%M}')
    merged = main_data + new
    json.dump(merged, open(MAIN,'w',encoding='utf-8'), ensure_ascii=False, indent=2)

    c = collections.Counter(x.get('category') for x in merged)
    print(f'\n合併後總數：{len(main_data)} → {len(merged)}')
    print('各分類：')
    for k, v in c.most_common():
        flag = '✅' if v >= 50 else ('—' if k in ('保險微系統','電子名片','簡報製作') else '⚠️ 未達50')
        print(f'  {k}: {v} {flag}')

if __name__ == '__main__':
    main()
