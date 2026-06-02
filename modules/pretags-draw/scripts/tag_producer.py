"""Tag Producer — 独立版提示词处理模块.

将中文关键词转换为 SDXL 英文 tag 的核心引擎。
支持人物/动作/服装/镜头/画风/场景预设标签、LoRA 调用、
中文关键词自动翻译、画师串随机抽取。

提示词精炼（大模型润色 + 中译英）由 agent 自行处理，本模块不调用外部 LLM。
未匹配 pretags 的中文文本会原样保留，由 agent 后续调用 LLM 润色翻译。
数据文件位于同级 skill 的 assets/ 目录中。
"""

# 2025.06.16 — 独立 skill 版本
# Original by Tangerdream

from __future__ import annotations

import json
import os
import random
import re
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# ── 数据文件路径 ──────────────────────────────────────────────────────────
_SKILL_ROOT = Path(__file__).resolve().parent.parent  # skill 根目录
_ASSETS_DIR = _SKILL_ROOT / "assets"


def _resolve_pretags_path() -> str:
    """解析 pretags.json 路径：环境变量 > 向上搜索 pretags 目录 > 向上搜索 pretags.json > 本地回退"""
    import os as _os
    # 1. 环境变量优先（现在支持目录或文件）
    env_path = _os.getenv('PRETAGS_DATA_PATH')
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return env_path
        elif p.is_dir():
            # 如果是目录，返回目录中第一个 JSON 文件
            json_files = sorted(p.glob('*.json'))
            if json_files:
                return str(json_files[0])
    # 2. 从脚本所在目录向上搜索项目根目录的 pretags 文件夹
    start = Path(__file__).resolve().parent
    for p in [start, *start.parents]:
        pretags_dir = p / 'pretags'
        if pretags_dir.is_dir():
            json_files = sorted(pretags_dir.glob('*.json'))
            if json_files:
                return str(json_files[0])
    # 3. 从脚本所在目录向上搜索项目根目录的 pretags.json（兼容旧部署）
    for p in [start, *start.parents]:
        candidate = p / 'pretags.json'
        if candidate.is_file():
            return str(candidate)
    # 4. 回退到本地 assets 目录（兼容旧部署）
    return str(_ASSETS_DIR / "pretags.json")


DEFAULT_PRETAGS_PATH = _resolve_pretags_path()
DEFAULT_ARTISTS_CSV_PATH = str(_ASSETS_DIR / "danbooru_artists.csv")
DEFAULT_HASHTAG_MAPPING_PATH = str(_SKILL_ROOT / "hashtag_mapping.json")


# ── 配置 ──────────────────────────────────────────────────────────────────

class Settings(argparse.Namespace):
    """tag_producer 配置。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 中文 Unicode 范围
        self.supper_languiage_Unicode = r'[\u4e00-\u9fff]'

        # 预设标签文件
        self.pretag_json_path = kwargs.get('pretag_json_path', DEFAULT_PRETAGS_PATH)
        self.pretag_excel_path = kwargs.get('pretag_excel_path', '')
        self.hashtag_mapping_path = kwargs.get('hashtag_mapping_path', DEFAULT_HASHTAG_MAPPING_PATH)

        # 关键词设置
        self.pretag_character_key_word = 'character'
        self.pretag_character_clothes_key_word = 'clothing'
        self.pretag_character_appearance_key_word = 'appearance'
        self.pretag_others_key_words = ['action', 'clothing', 'shot', 'style', 'scene', 'other']
        self.pretag_random_key_word = 'random'
        self.pretag_character_query_key_word = 'query'

        # 绘图系统类型
        self.sys = kwargs.get('sys', 'comfyui')

        # 有道翻译（已禁用）
        self.translate_Youdao = False
        self.translate_Youdao_key_word = 'translate'
        self.APP_KEY_Youdao = ''
        self.APP_SECRET_Youdao = ''

        # 代理（从环境变量读取）
        self.proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY') or None

        # 画师串
        self.roll_artist = True
        self.roll_artist_key_word = 'roll_artist'
        self.roll_artist_csv_path = kwargs.get('roll_artist_csv_path', DEFAULT_ARTISTS_CSV_PATH)
        
        # Tanger-Presets-Show 角色查询
        self.enable_character_query = kwargs.get('enable_character_query', True)


# ── 核心引擎 ──────────────────────────────────────────────────────────────

class TagProducer:
    """提示词处理引擎：# 前缀关键词 → SDXL 英文 tag.

    支持别名映射：用户可通过 hashtag_mapping.json 自定义关键字别名。
    例如 #char 等同于 #人物，#style 等同于 #画风。

    默认指令格式（使用 # 前缀，不限中文）：
    - #人物/char/character 角色名 [外貌/appearance] [服装/clothing] [权重]
    - #画风/style 标签名 [权重]（动作/服装/镜头/场景/其他同理）
    - #随机/random/rand [系列名] [外貌] [服装] [权重]
    - #撸串/artist/roll 数量
    - #角色/query/find 查询词
    - #角色名：直接查询角色（简写形式）
    - #翻译/trans 中文（需有道翻译配置）

    完整别名配置见 hashtag_mapping.json。
    """

    def __init__(self, args: Settings | None = None):
        """初始化 TagProducer。

        Args:
            args: 配置参数。
        """
        if args is None:
            args = Settings()
        if args.sys not in ['webui', 'comfyui']:
            raise ValueError("sys参数必须为'webui'或'comfyui'")
        self.sys = args.sys
        self.supper_languiage_Unicode = args.supper_languiage_Unicode
        self.sheetlist = args.pretag_others_key_words
        self.sheetlist.append(args.pretag_character_key_word)
        self.jobs = self.sheetlist.copy()
        self.pretag_random_key_word = args.pretag_random_key_word
        self.jobs.append(self.pretag_random_key_word)
        self.pretag_character_query_key_word = args.pretag_character_query_key_word
        if args.enable_character_query:
            self.jobs.append(self.pretag_character_query_key_word)
        self.pretag_character_key_word = args.pretag_character_key_word
        self.pretag_character_clothes_key_word = args.pretag_character_clothes_key_word
        self.pretag_character_appearance_key_word = args.pretag_character_appearance_key_word

        # 翻译
        if args.translate_Youdao:
            self.Translator = YoudaoTranslate(APP_KEY=args.APP_KEY_Youdao, APP_SECRET=args.APP_SECRET_Youdao)
            self.translate_key_word = args.translate_Youdao_key_word
            self.jobs.append(self.translate_key_word)
        else:
            self.translate_key_word = None

        # 代理
        if args.proxy:
            os.environ['http_proxy'] = args.proxy
            os.environ['https_proxy'] = args.proxy

        # 画师串
        if args.roll_artist:
            self.roll_artist_key_word = args.roll_artist_key_word
            self.roll_artist = RollArtist(csv_path=args.roll_artist_csv_path)
            self.jobs.append(self.roll_artist_key_word)

        # 预设标签
        self.jsonpath = args.pretag_json_path
        self.excelpath = args.pretag_excel_path
        if self.excelpath:
            self.dic = self.excel2dict(self.excelpath, self.sheetlist)
        elif self.jsonpath:
            with open(self.jsonpath, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # ── 统一数据源适配：前端格式 → 兼容旧 flat 格式 ──
            # 前端格式: {characters, series, categories:{动作,服装,...}}
            # 旧 flat 格式: {动作:{...}, 服装:{...}, ..., 人物:{...}, charsort:{...}}
            if 'categories' in loaded:
                # 转换分类数据（字段名映射：前端→旧格式）
                self.dic = {}
                for cat in ['action', 'clothing', 'shot', 'style', 'scene', 'other']:
                    if cat in loaded['categories']:
                        self.dic[cat] = {}
                        for _id, entry in loaded['categories'][cat].items():
                            tag_name = entry.get('name', _id)
                            item = {
                                'cname': tag_name,
                                'tag': entry.get('tag', ''),
                                'Lora': 1 if entry.get('has_lora') else 0,
                            }
                            if item['Lora']:
                                item['model file name'] = entry.get('lora_file', '')
                                item['model hash'] = entry.get('lora_hash', '')
                                item['unet weight'] = entry.get('unet_weight', 0.8)
                                item['clip weight'] = entry.get('clip_weight', 0.8)
                                item['link'] = entry.get('lora_link', '')
                            if 'description' in entry:
                                item['画风描述'] = entry['description']
                            if 'd_group' in entry:
                                item['d_group'] = entry['d_group']
                            self.dic[cat][tag_name] = item
                # 转换角色数据
                if 'characters' in loaded:
                    chars = {}
                    for _id, ch in loaded['characters'].items():
                        cname = ch.get('cname', _id)
                        chars[cname] = {
                            'cname': cname,
                            'Source': ch.get('source', ''),
                            'Lora': 1 if ch.get('has_lora') else 0,
                            'tag': ch.get('name', ''),
                            'model file name': ch.get('lora_file', 0),
                            'model hash': ch.get('lora_hash', 0),
                            'unet weight': ch.get('unet_weight', 0),
                            'clip weight': ch.get('clip_weight', 0),
                            'link': ch.get('lora_link', 0),
                            'name': ch.get('name', cname),
                            'appearance': ch.get('appearance', ''),
                            'clothing': ch.get('clothing', ''),
                        }
                    self.dic['character'] = chars
                # 转换系列数据（ID→cname 映射，兼容 ID 迁移后的数据格式）
                if 'series' in loaded:
                    charsort_data = {}
                    id_to_cname = {}
                    for _id, ch in loaded.get('characters', {}).items():
                        id_to_cname[_id] = ch.get('cname', _id)
                    for source, sdata in loaded['series'].items():
                        char_ids = sdata.get('characters', [])
                        charsort_data[source] = [id_to_cname.get(cid, cid) for cid in char_ids]
                    self.dic['charsort'] = charsort_data
            else:
                # 旧格式兼容
                self.dic = loaded
        else:
            raise FileNotFoundError("请提供预设标签的Excel或JSON文件路径")
        
        # Tanger-Presets-Show 角色查询
        self.character_query = None
        if args.enable_character_query:
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                from character_query import CharacterDB
                self.character_query = CharacterDB()
            except Exception:
                pass  # 静默失败，不影响主功能

        # 加载 hashtag 命令映射
        mapping_path = getattr(args, 'hashtag_mapping_path', DEFAULT_HASHTAG_MAPPING_PATH) if args else DEFAULT_HASHTAG_MAPPING_PATH
        self._load_hashtag_mapping(mapping_path)

    def reset(self, args: Settings):
        self.__init__(args)

    def _load_hashtag_mapping(self, mapping_path: str | None = None):
        """加载 hashtag 命令映射配置，构建别名查找表。

        映射文件格式见 hashtag_mapping.json。
        如果文件不存在或加载失败，使用 Settings 中的硬编码默认值构建。
        """
        self.cmd_alias_map: dict[str, tuple[str, str]] = {}   # alias → (cmd_type, data_key)
        self.field_alias_map: dict[str, str] = {}              # alias → canonical_name (子字段)
        self._random_aliases: set[str] = set()                 # 所有"随机"关键字的别名

        mapping = None
        if mapping_path and os.path.isfile(mapping_path):
            try:
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"[TagProducer] 警告: 映射文件加载失败 ({e})，使用默认配置")

        if mapping and isinstance(mapping, dict) and 'categories' in mapping:
            # ── 从映射文件构建 ──
            # Character
            char_cfg = mapping.get('character', {})
            char_data_key = char_cfg.get('data_key', self.pretag_character_key_word)
            for alias in char_cfg.get('aliases', [char_data_key]):
                self.cmd_alias_map[alias] = ('character', char_data_key)
            # Sub-fields (外貌, 服装)
            for sf_name, sf_cfg in char_cfg.get('sub_fields', {}).items():
                sf_data_key = sf_cfg.get('data_key', sf_name)
                for alias in sf_cfg.get('aliases', [sf_data_key]):
                    self.field_alias_map[alias] = sf_data_key
            # Categories
            for cat_name, cat_cfg in mapping.get('categories', {}).items():
                cat_data_key = cat_cfg.get('data_key', cat_name)
                for alias in cat_cfg.get('aliases', [cat_data_key]):
                    self.cmd_alias_map[alias] = ('category', cat_data_key)
            # Random
            rand_cfg = mapping.get('random', {})
            rand_data_key = rand_cfg.get('data_key', self.pretag_random_key_word)
            for alias in rand_cfg.get('aliases', [rand_data_key]):
                self.cmd_alias_map[alias] = ('random', rand_data_key)
                self._random_aliases.add(alias)
            # Query
            query_cfg = mapping.get('query', {})
            query_data_key = query_cfg.get('data_key', self.pretag_character_query_key_word)
            for alias in query_cfg.get('aliases', [query_data_key]):
                self.cmd_alias_map[alias] = ('query', query_data_key)
            # Roll artist
            roll_cfg = mapping.get('roll_artist', {})
            roll_data_key = roll_cfg.get('data_key', getattr(self, 'roll_artist_key_word', '撸串'))
            for alias in roll_cfg.get('aliases', [roll_data_key]):
                self.cmd_alias_map[alias] = ('roll_artist', roll_data_key)
            # Translate
            trans_cfg = mapping.get('translate', {})
            trans_data_key = trans_cfg.get('data_key', getattr(self, 'translate_key_word', None) or '翻译')
            for alias in trans_cfg.get('aliases', [trans_data_key]):
                self.cmd_alias_map[alias] = ('translate', trans_data_key)
        else:
            # ── 使用硬编码默认值构建（向后兼容） ──
            # 英文键名
            self.cmd_alias_map[self.pretag_character_key_word] = ('character', self.pretag_character_key_word)
            for cat in self.sheetlist:
                if cat != self.pretag_character_key_word:
                    self.cmd_alias_map[cat] = ('category', cat)
            self.cmd_alias_map[self.pretag_random_key_word] = ('random', self.pretag_random_key_word)
            self._random_aliases.add(self.pretag_random_key_word)
            self.cmd_alias_map[self.pretag_character_query_key_word] = ('query', self.pretag_character_query_key_word)
            if hasattr(self, 'roll_artist_key_word'):
                self.cmd_alias_map[self.roll_artist_key_word] = ('roll_artist', self.roll_artist_key_word)
            if self.translate_key_word:
                self.cmd_alias_map[self.translate_key_word] = ('translate', self.translate_key_word)
            # 中文别名（确保无映射文件时中文关键字仍可用）
            _CN_FALLBACK = {
                '人物': ('character', self.pretag_character_key_word),
                '动作': ('category', 'action'),
                '服装': ('category', 'clothing'),
                '镜头': ('category', 'shot'),
                '画风': ('category', 'style'),
                '场景': ('category', 'scene'),
                '其他': ('category', 'other'),
                '随机': ('random', self.pretag_random_key_word),
                '角色': ('query', self.pretag_character_query_key_word),
                '撸串': ('roll_artist', getattr(self, 'roll_artist_key_word', 'roll_artist')),
                '翻译': ('translate', getattr(self, 'translate_key_word', 'translate')),
            }
            for cn_alias, info in _CN_FALLBACK.items():
                if cn_alias not in self.cmd_alias_map:
                    self.cmd_alias_map[cn_alias] = info
                if info[0] == 'random':
                    self._random_aliases.add(cn_alias)
            # Sub-fields (中文别名 → 英文 data_key)
            self.field_alias_map['外貌'] = self.pretag_character_appearance_key_word
            self.field_alias_map['服装'] = self.pretag_character_clothes_key_word
            self.field_alias_map[self.pretag_character_appearance_key_word] = self.pretag_character_appearance_key_word
            self.field_alias_map[self.pretag_character_clothes_key_word] = self.pretag_character_clothes_key_word

    def _resolve_aim(self, word: str, cmd_type: str) -> str:
        """根据命令上下文解析 aim 词。

        - character 命令：解析子字段别名（外貌/服装等）
        - category 命令：仅解析随机关键字别名
        - 其他：不解析
        """
        if cmd_type == 'character':
            return self.field_alias_map.get(word, word)
        elif cmd_type == 'category':
            if word in self._random_aliases:
                return self.pretag_random_key_word
            return word
        return word

    # ── 数据加载 ──────────────────────────────────────────────────────────

    def todic(self, path, key):
        dic = {}
        df = pd.read_excel(path, sheet_name=key)
        ls = df.to_dict(orient='records')
        for item in ls:
            dic[item['cname']] = item
        return dic

    def charsort(self, chardic: dict):
        charsd = {}
        for key in chardic.keys():
            if chardic[key]['Source'] not in list(charsd.keys()):
                charsd[chardic[key]['Source']] = [chardic[key]['cname']]
            else:
                charsd[chardic[key]['Source']].append(chardic[key]['cname'])
        return charsd

    def excel2dict(self, excelpath, sheetlist=None):
        if sheetlist is None:
            sheetlist = self.sheetlist
        dic = {}
        for key in sheetlist:
            dic[key] = self.todic(excelpath, key)
        dic['charsort'] = self.charsort(dic[self.pretag_character_key_word])
        return dic

    def excel2json(self, excelpath=None, jsonpath=None, sheetlist=None):
        if sheetlist is None:
            sheetlist = self.sheetlist
        if excelpath is None:
            excelpath = self.excelpath
        if jsonpath is None:
            jsonpath = self.jsonpath
        dic = self.excel2dict(excelpath, sheetlist=sheetlist)
        with open(jsonpath, 'w', encoding='utf-8') as f:
            json.dump(dic, f, ensure_ascii=False, indent=4)
        print('已保存为JSON文件：', jsonpath)

    # ── 提示词处理 ────────────────────────────────────────────────────────

    def get_hashtag_commands(self, prompt):
        """提取 # 前缀的命令（支持任意字符，不限中文）"""
        return re.findall(r'#[^\s,，]+(?:\s+[^\s,，]+)*', prompt)

    def clean_commas(self, prompt: str):
        cleaned_prompt = re.sub(r',+', ',', prompt)
        return cleaned_prompt

    def get_weights(self, aims: list):
        numlist = []
        for aim in aims:
            try:
                numlist.append(float(aim))
            except Exception:
                pass
        if numlist:
            unet_weight = numlist[0]
            clip_weight = numlist[-1]
        else:
            unet_weight = 0
            clip_weight = 0
        return unet_weight, clip_weight

    def randkey(self, job):
        keys = self.dic[job].keys()
        return random.choice(list(keys))

    def get_tags(self, aims: list, job):
        tags = ''
        unet_weight, clip_weight = self.get_weights(aims)
        for key in aims[1:]:
            if key == self.pretag_random_key_word:
                key = self.randkey(job)
            try:
                if self.dic[job][key]['Lora']:
                    if not unet_weight:
                        unet_weight = self.dic[job][key]['unet weight']
                    if not clip_weight:
                        clip_weight = self.dic[job][key]['clip weight']
                    if self.sys == 'comfyui':
                        tags = tags + '<lora:' + self.dic[job][key]['model file name'] + ':' + str(unet_weight) + ':' + str(clip_weight) + '>,' + self.dic[job][key]['tag'] + ','
                    else:
                        tags = tags + '<lora:' + self.dic[job][key]['model file name'] + ':' + str(unet_weight) + '>,' + self.dic[job][key]['tag'] + ','
                else:
                    if unet_weight:
                        tags = tags + '(' + self.dic[job][key]['tag'] + ':' + str(unet_weight) + '),'
                    else:
                        tags = tags + self.dic[job][key]['tag'] + ','
            except Exception:
                pass
        return tags

    def get_chartags(self, aims: list):
        job = self.pretag_character_key_word
        tags = ''
        if aims[0] == job:
            begin_id = 1
        else:
            begin_id = 0
        unet_weight, clip_weight = self.get_weights(aims)
        for key in aims[begin_id:]:
            if key == self.pretag_random_key_word:
                key = self.randkey(job)
            try:
                if self.dic[job][key]['Lora']:
                    if not unet_weight:
                        unet_weight = self.dic[job][key]['unet weight']
                    if not clip_weight:
                        clip_weight = self.dic[job][key]['clip weight']
                    if self.sys == 'comfyui':
                        tags = tags + '<lora:' + self.dic[job][key]['model file name'] + ':' + str(unet_weight) + ':' + str(clip_weight) + '>,' + self.dic[job][key]['name'] + ','
                    else:
                        tags = tags + '<lora:' + self.dic[job][key]['model file name'] + ':' + str(unet_weight) + '>,' + self.dic[job][key]['name'] + ','
                else:
                    tags = tags + self.dic[job][key]['name'] + ','

                if self.pretag_character_appearance_key_word in aims:
                    tags = tags + self.dic[job][key][self.pretag_character_appearance_key_word] + ','
                if self.pretag_character_clothes_key_word in aims:
                    tags = tags + self.dic[job][key][self.pretag_character_clothes_key_word] + ','
            except Exception:
                pass
        return tags

    def repeatlora_del(self, input_str):
        lora_pattern = r'<lora:[^>]+>'
        lora_tags = re.finditer(lora_pattern, input_str)
        seen_loras = {}
        to_remove = []
        for match in lora_tags:
            tag = match.group()
            lora_name = tag[6:].split(':')[0]
            if lora_name in seen_loras:
                to_remove.append(tag)
            else:
                seen_loras[lora_name] = tag
        result = input_str
        for tag in to_remove:
            result = result.replace(tag, '')
        return result

    def tagrep(self, prompt: str) -> str:
        """处理提示词：# 前缀关键词替换、LoRA 解析。

        支持别名映射：用户可通过 hashtag_mapping.json 自定义关键字别名。
        例如 #char 等同于 #人物，#style 等同于 #画风。

        未匹配的 # 命令会原样保留。
        """
        prompt = prompt.replace('，', ',')
        cmd_list = self.get_hashtag_commands(prompt)

        for cmd in cmd_list:
            cmd_content = cmd[1:]  # 去掉 #
            aims = re.split(r'\s+', cmd_content)
            tags = ''

            # 通过别名映射解析命令关键字
            cmd_info = self.cmd_alias_map.get(aims[0])

            if cmd_info:
                cmd_type, data_key = cmd_info
                # 解析剩余参数中的子字段/特殊关键字别名
                resolved = [data_key] + [
                    self._resolve_aim(a, cmd_type) for a in aims[1:]
                ]

                if cmd_type == 'character':
                    tags = self.get_chartags(resolved)

                elif cmd_type == 'category':
                    tags = self.get_tags(resolved, data_key)

                elif cmd_type == 'random':
                    try:
                        aims2 = resolved[1:]
                        if aims2:
                            aims2[0] = random.choice(self.dic['charsort'][aims2[0]])
                        tags = self.get_chartags(aims2)
                    except Exception:
                        tags = self.get_chartags(resolved)

                elif cmd_type == 'query':
                    if self.character_query:
                        try:
                            query = ' '.join(aims[1:])
                            result = self.character_query.get_by_name(query)
                            if result:
                                tags = result['prompt']
                            else:
                                results = self.character_query.search(query, limit=1)
                                if results:
                                    tags = results[0]['prompt']
                        except Exception:
                            pass

                elif cmd_type == 'roll_artist':
                    try:
                        tags = self.roll_artist.roll_artist(int(aims[1]))
                    except Exception:
                        pass

                elif cmd_type == 'translate':
                    try:
                        aims2 = aims[1:]
                        sentence = ''
                        for i in aims2:
                            sentence = sentence + i + ','
                        tags = self.Translator.translate(sentence)
                    except Exception:
                        pass

            else:
                # 尝试直接作为角色名查询（#角色名 的简写形式）
                try:
                    char_name = cmd_content
                    if char_name in self.dic[self.pretag_character_key_word]:
                        tags = self.get_chartags([char_name])
                    else:
                        # 未匹配 → 原样保留
                        tags = cmd
                except Exception:
                    tags = cmd

            prompt = prompt.replace(cmd, tags)

        return self.clean_commas(self.repeatlora_del(prompt.replace('，', ',')))


# ── 有道翻译 ──────────────────────────────────────────────────────────────

class YoudaoTranslate:
    """有道翻译 API（需配置 APP_KEY/APP_SECRET）。"""

    def __init__(self, APP_KEY=None, APP_SECRET=None):
        import hashlib
        import time
        import uuid
        import requests
        self._hashlib = hashlib
        self._time = time
        self._uuid = uuid
        self._requests = requests
        self.APP_KEY = APP_KEY
        self.APP_SECRET = APP_SECRET

    def addAuthParams(self, appKey, appSecret, params):
        q = params.get('q')
        if q is None:
            q = params.get('img')
        q = "".join(q)
        salt = str(self._uuid.uuid1())
        curtime = str(int(self._time.time()))
        sign = self.calculateSign(appKey, appSecret, q, salt, curtime)
        params['appKey'] = appKey
        params['salt'] = salt
        params['curtime'] = curtime
        params['signType'] = 'v3'
        params['sign'] = sign

    def calculateSign(self, appKey, appSecret, q, salt, curtime):
        strSrc = appKey + self.getInput(q) + salt + curtime + appSecret
        return self.encrypt(strSrc)

    def encrypt(self, strSrc):
        hash_algorithm = self._hashlib.sha256()
        hash_algorithm.update(strSrc.encode('utf-8'))
        return hash_algorithm.hexdigest()

    def getInput(self, input):
        if input is None:
            return input
        inputLen = len(input)
        return input if inputLen <= 20 else input[0:10] + str(inputLen) + input[inputLen - 10:inputLen]

    def translate(self, q):
        lang_from = 'zh-CHS'
        lang_to = 'en'
        data = {'q': q, 'from': lang_from, 'to': lang_to}
        self.addAuthParams(self.APP_KEY, self.APP_SECRET, data)
        header = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = self._requests.post('https://openapi.youdao.com/api', data=data, headers=header)
        try:
            if response.json()["translation"][0]:
                return response.json()["translation"][0]
        except Exception:
            pass


# ── 画师随机 ──────────────────────────────────────────────────────────────

class RollArtist:
    """从画师 CSV 文件中随机选取画师。"""

    def __init__(self, csv_path: str | None = None):
        if csv_path is None:
            csv_path = DEFAULT_ARTISTS_CSV_PATH
        self.artists = pd.read_csv(csv_path)
        self.length = len(self.artists['name'])

    def roll_artist(self, roll_num: int) -> str:
        roll_nums = np.random.choice(self.length, roll_num, replace=False)
        artists = ''
        for i in roll_nums:
            if np.random.choice([0, 1], p=[0.7, 0.3]):
                artists = artists + self.artists['name'][i] + ','
            else:
                weight = np.random.uniform(0.5, 1.3)
                weight = str(round(weight, 2))
                artists = artists + '(' + self.artists['name'][i] + ':' + weight + '),'
        return artists


# ── 便捷单例 ──────────────────────────────────────────────────────────────

_default_instance: TagProducer | None = None


def get_tag_producer() -> TagProducer:
    """获取默认 TagProducer 单例（延迟初始化）。"""
    global _default_instance
    if _default_instance is None:
        _default_instance = TagProducer(Settings())
    return _default_instance


def process_prompt(prompt: str) -> str:
    """便捷函数：处理提示词。

    Args:
        prompt: 输入提示词（可含中文）。
    """
    return get_tag_producer().tagrep(prompt)


# ── CLI 入口 ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    prompt = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else '白毛 狐耳 红瞳 古风 妖媚,撸串 4'
    print(f"输入: {prompt}")
    print(f"输出: {process_prompt(prompt)}")
