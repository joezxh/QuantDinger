import os

files = [
    'frontend/src/config/defaultSettings.js',
    'frontend/src/layouts/UserLayout.vue',
    'frontend/src/layouts/BasicLayout.vue',
    'frontend/src/views/user/Login.vue',
    'frontend/src/views/ai-analysis/components/index.vue',
    'frontend/src/views/user-manage/index.vue',
    'frontend/src/views/profile/index.vue',
    'frontend/src/views/indicator-ide/index.vue',
    'frontend/src/views/indicator-analysis/components/IndicatorEditor.vue',
    'frontend/src/utils/request.js',
    'frontend/src/components/GlobalFooter/index.vue',
    'frontend/src/components/GlobalHeader/RightContent.vue',
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
    if not os.path.exists(path):
        print(f'MISSING: {path}')
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    new_content = content.replace('QuantDinger', 'QuantumQuant')
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(new_content)
        print(f'UPDATED: {f}')
    else:
        print(f'NO CHANGE: {f}')
