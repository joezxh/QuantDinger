import os, re

# Replace case variations, but protect API paths /addons/quantdinger/
files = [
    'frontend/src/views/user-manage/index.vue',
    'frontend/src/views/profile/index.vue',
    'frontend/src/utils/request.js',
    'frontend/src/components/GlobalHeader/RightContent.vue',
    'README.md',
    'docs/README_CN.md',
]

base = 'd:/projects/QuantDinger'
for f in files:
    path = os.path.join(base, f)
    if not os.path.exists(path):
        print(f'MISSING: {path}')
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content
    # Replace variations
    content = content.replace('quantdinger', 'quantumquant')
    content = content.replace('QUANTDINGER', 'QUANTUMQUANT')
    content = content.replace('Quantdinger', 'QuantumQuant')
    if content != original:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f'UPDATED: {f}')
    else:
        print(f'NO CHANGE: {f}')
