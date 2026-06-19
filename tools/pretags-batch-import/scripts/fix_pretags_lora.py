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
# 脚本位于 <root>/tools/pretags-batch-import/scripts/，需向上三层到达项目根
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)
from _env import iter_lora_subdirs

PRETAGS = os.path.join(_PROJECT_ROOT, 'pretags.json')
LORA_DIRS = iter_lora_subdirs('画风')


def main(pretags_path=None, check_only=False):
    pretags_path = pretags_path or PRETAGS

    # Step 1: 备份（仅在实际修复时）
    if not check_only:
        backup_path = pretags_path.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        shutil.copy2(pretags_path, backup_path)
        print(f'✅ 备份: {backup_path}')
    else:
        print('🔍 仅检查模式（--check），不写盘、不备份')

    # Step 2: 加载
    with open(pretags_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 兼容新旧数据结构：
    #   新结构（ID-key）: data['categories']['style']，字段 lora_file / has_lora
    #   旧结构（name-key）: data['画风']，字段 model file name / Lora
    if isinstance(data.get('categories'), dict) and 'style' in data['categories']:
        style_table = data['categories']['style']
        lora_file_key = 'lora_file'
        lora_flag_key = 'has_lora'
    elif '画风' in data:
        style_table = data['画风']
        lora_file_key = 'model file name'
        lora_flag_key = 'Lora'
    else:
        print('❌ 未识别的 pretags 结构（无 categories.style 也无 画风）')
        sys.exit(1)

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
    for k, v in style_table.items():
        mfn = v.get(lora_file_key, '')
        if not isinstance(mfn, str) or not mfn:
            skipped.append((k, f'无 {lora_file_key}'))
            continue

        mfn_clean = mfn.replace('.safetensors', '')
        if mfn_clean not in disk_files:
            skipped.append((k, f'磁盘无此文件: {mfn}'))
            continue

        current_lora = v.get(lora_flag_key, 0)
        # has_lora 为布尔 True，或旧 Lora 为整数/字符串 "1"
        already_set = current_lora is True or str(current_lora) == '1'
        if already_set:
            skipped.append((k, f'已经是 {lora_flag_key}=true'))
            continue

        # 修正：新结构写布尔 True，旧结构写整数 1
        v[lora_flag_key] = True if lora_flag_key == 'has_lora' else 1
        changed.append((k, current_lora, v[lora_flag_key]))

    # Step 5: 回写（仅在实际修复时）
    if not check_only:
        with open(pretags_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Step 6: 验证
    verified = data
    if not check_only:
        with open(pretags_path, 'r', encoding='utf-8') as f:
            verified = json.load(f)
    verified_table = verified.get('categories', {}).get('style') if 'categories' in verified else verified.get('画风', {})

    print(f'\n📊 结果')
    print(f'   修正为 {lora_flag_key}=true: {len(changed)} 条')
    print(f'   跳过: {len(skipped)} 条')
    print(f'   JSON 完整性验证: ✅')

    lora_true = sum(1 for v in verified_table.values()
                    if v.get(lora_flag_key) is True or str(v.get(lora_flag_key)) == '1')
    lora_false = sum(1 for v in verified_table.values()
                     if v.get(lora_flag_key) in (False, 0, None) or str(v.get(lora_flag_key)) == '0')
    print(f'   画风 {lora_flag_key}=true: {lora_true}')
    print(f'   画风 {lora_flag_key}=false: {lora_false}')

    # 前10个
    if changed:
        print('\n📋 前10个修正条目:')
        for k, old, new in changed[:10]:
            print(f'   {k}: Lora={old} → Lora={new}')
        if len(changed) > 10:
            print(f'   ... 还有 {len(changed)-10} 条')

    print(f'\n✅ 完成')


if __name__ == '__main__':
    import argparse
    _parser = argparse.ArgumentParser(description='pretags 画风 Lora 标记批量修正脚本')
    _parser.add_argument('--pretags', '-p', default=None,
                         help='指定 pretags JSON 路径（默认自动查找项目根 pretags.json）')
    _parser.add_argument('--check', action='store_true',
                         help='仅检查并输出报告，不写盘、不备份')
    _args = _parser.parse_args()
    main(pretags_path=_args.pretags, check_only=_args.check)
