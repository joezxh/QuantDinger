import os

files = [
    'frontend/src/layouts/UserLayout.vue',
    'frontend/src/layouts/BasicLayout.vue',
]

lang_files = [
    'frontend/src/locales/lang/zh-CN.js',
    'frontend/src/locales/lang/zh-TW.js',
    'frontend/src/locales/lang/en-US.js',
    'frontend/src/locales/lang/vi-VN.js',
    'frontend/src/locales/lang/th-TH.js',
    'frontend/src/locales/lang/ja-JP.js',
    'frontend/src/locales/lang/ko-KR.js',
    'frontend/src/locales/lang/fr-FR.js',
    'frontend/src/locales/lang/de-DE.js',
    'frontend/src/locales/lang/ar-SA.js',
]

all_files = files + lang_files

base = 'd:/projects/QuantDinger'
for f in all_files:
    path = os.path.join(base, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content
    content = content.replace('Quantdinger', 'QuantumQuant')
    content = content.replace('quantdinger', 'quantumquant')
    content = content.replace('QUANTDINGER', 'QUANTUMQUANT')
    if content != original:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f'UPDATED: {f}')
    else:
        print(f'NO CHANGE: {f}')
