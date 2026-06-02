#!/usr/bin/env python3
"""
pretags 画风 Lora 标记批量修正脚本

使用场景：
  磁盘上有 .safetensors 文件，对应的 pretags 条目存在但 Lora 被标记为 0（而非 1）。
  这类问题通常发生在批量导入后的后续维护阶段——条目已录入但 Lora 标志未更新。

使用方法：
  python3 scripts/fix_pretags_lora.py

前置条件：
  - pretags.json 路径：自动从项目根目录查找
  - 画风模型目录：通过 LORA_MODEL_DIR 环境变量配置，自动扫描所有 model_type/{画风}/ 子目录
  - 自动备份原文件到同目录

执行逻辑：
  1. 备份 pretags.json → pretags_backup_YYYYMMDD_HHMMSS.json
  2. 扫描所有 model_type/画风/ 子目录，收集所有 .safetensors 的 stem
  3. 遍历 pretags['画风'] 条目，对磁盘文件存在但 Lora != 1 的修正为 1
  4. 回写并 JSON 验证
  5. 输出修正统计

典型输出：
  ✅ 备份: .../pretags_backup_20260512_135706.json
  📂 磁盘画风文件: 267 个
  📊 结果
     修正为 Lora=1: 255 条
     跳过（已是1或无文件）: 312 条
     JSON 完整性验证: ✅
     修正后画风 Lora=1: 302
     修正后画风 Lora=0: 265
"""

import json, shutil, os, sys
from datetime import datetime

# 将项目根目录加入 sys.path 以便 import _env
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)
from _env import iter_lora_subdirs

PRETAGS = os.path.join(_PROJECT_ROOT, 'pretags.json')
LORA_DIRS = iter_lora_subdirs('画风')
BACKUP = PRETAGS.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')


def main():
    # Step 1: 备份
    shutil.copy2(PRETAGS, BACKUP)
    print(f'✅ 备份: {BACKUP}')

    # Step 2: 加载
    with open(PRETAGS, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Step 3: 收集磁盘文件（stem 格式，遍历所有 model_type/画风/ 子目录）
    disk_files = set()
    for lora_dir in LORA_DIRS:
        for fn in os.listdir(lora_dir):
            if fn.endswith('.safetensors'):
                disk_files.add(fn.replace('.safetensors', ''))

    print(f'📂 磁盘画风文件: {len(disk_files)} 个')

    # Step 4: 检查并修正
    changed = []
    skipped = []
    for k, v in data['画风'].items():
        mfn = v.get('model file name', '')
        if not isinstance(mfn, str) or not mfn:
            skipped.append((k, '无 model file name'))
            continue

        mfn_clean = mfn.replace('.safetensors', '')
        if mfn_clean not in disk_files:
            skipped.append((k, f'磁盘无此文件: {mfn}'))
            continue

        current_lora = v.get('Lora', 0)
        # 注意：Lora 可能存为字符串 "1" 而非整数 1，统一处理
        if str(current_lora) == '1':
            skipped.append((k, '已经是 Lora=1'))
            continue

        # 修正（写入整数类型以确保一致性）
        v['Lora'] = 1
        changed.append((k, current_lora, 1))

    # Step 5: 回写
    with open(PRETAGS, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Step 6: 验证
    with open(PRETAGS, 'r', encoding='utf-8') as f:
        verified = json.load(f)

    print(f'\n📊 结果')
    print(f'   修正为 Lora=1: {len(changed)} 条')
    print(f'   跳过: {len(skipped)} 条')
    print(f'   JSON 完整性验证: ✅')

    lora1_after = sum(1 for v in verified['画风'].values() if v.get('Lora') == 1)
    lora0_after = sum(1 for v in verified['画风'].values() if v.get('Lora') == 0)
    print(f'   修正后画风 Lora=1: {lora1_after}')
    print(f'   修正后画风 Lora=0: {lora0_after}')

    # 前10个
    if changed:
        print('\n📋 前10个修正条目:')
        for k, old, new in changed[:10]:
            print(f'   {k}: Lora={old} → Lora={new}')
        if len(changed) > 10:
            print(f'   ... 还有 {len(changed)-10} 条')

    print(f'\n✅ 完成')


if __name__ == '__main__':
    main()
