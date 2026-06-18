#!/usr/bin/env python3
"""
Pretags 数据 API 服务器
统一数据源：通过 PRETAGS_DATA_PATH 环境变量指定 pretags.json 本体路径
"""
import json, os, base64, hashlib
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
import sys

def _load_dotenv():
    """从项目根目录加载 .env 文件（不依赖 python-dotenv）"""
    # 从脚本所在目录向上查找 .env
    start = Path(__file__).resolve().parent
    for p in [start, *start.parents]:
        env_path = p / ".env"
        if env_path.is_file():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
            return

def _scan_pretags_files(directory: str) -> list[dict]:
    """扫描目录中的所有 pretags JSON 文件"""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return []
    
    files = []
    for json_file in dir_path.glob('*.json'):
        if json_file.is_file():
            files.append({
                'filename': json_file.name,
                'path': str(json_file),
                'size': json_file.stat().st_size,
                'mtime': json_file.stat().st_mtime
            })
    
    # 按文件名排序
    files.sort(key=lambda x: x['filename'])
    return files

def _get_default_pretags_filename() -> str | None:
    """从配置文件读取默认 pretags 文件名"""
    config_file = Path(__file__).resolve().parent / '.pretags_default'
    if config_file.is_file():
        try:
            return config_file.read_text().strip()
        except Exception:
            pass
    return None

def _set_default_pretags_filename(filename: str) -> None:
    """保存默认 pretags 文件名到配置文件"""
    config_file = Path(__file__).resolve().parent / '.pretags_default'
    config_file.write_text(filename)

def _resolve_pretags_path(cli_path: str | None = None) -> str:
    """解析 pretags.json 路径。

    优先级：cli_path 参数 > PRETAGS_DATA_PATH 环境变量 > 向上搜索 pretags/ 目录

    支持目录或文件路径：
    - 文件路径：直接使用该文件
    - 目录路径：优先使用 .pretags_default 配置的默认文件，否则使用目录中第一个 JSON 文件

    如果所有来源都无效，将抛出 RuntimeError。
    """
    # 1. CLI 参数优先
    candidates = []
    if cli_path:
        candidates.append(('CLI 参数', cli_path))
    # 2. 环境变量
    env_path = os.getenv('PRETAGS_DATA_PATH')
    if env_path:
        candidates.append(('PRETAGS_DATA_PATH', env_path))

    for source, raw_path in candidates:
        p = Path(raw_path)
        if p.is_file():
            return raw_path
        elif p.is_dir():
            default_filename = _get_default_pretags_filename()
            if default_filename:
                default_path = p / default_filename
                if default_path.is_file():
                    return str(default_path)
            files = _scan_pretags_files(raw_path)
            if files:
                return files[0]['path']
            raise RuntimeError(f"{source} 指向目录但未找到 JSON 文件：{raw_path}")

    # 3. 向上搜索 pretags/ 目录（自动发现）
    start = Path(__file__).resolve().parent
    for p in [start, *start.parents]:
        pretags_dir = p / 'pretags'
        if pretags_dir.is_dir():
            default_filename = _get_default_pretags_filename()
            if default_filename:
                default_path = pretags_dir / default_filename
                if default_path.is_file():
                    return str(default_path)
            files = _scan_pretags_files(str(pretags_dir))
            if files:
                return files[0]['path']

    raise RuntimeError(
        "未找到 pretags 数据文件。请通过以下方式之一指定：\n"
        "  1. 设置 PRETAGS_DATA_PATH 环境变量（如 PRETAGS_DATA_PATH=./pretags/pretags-anima.json）\n"
        "  2. 在 .env 文件中配置 PRETAGS_DATA_PATH\n"
        "  3. 将 pretags 数据文件放在项目根目录的 pretags/ 文件夹中"
    )

def _get_pretags_directory() -> str:
    """获取 pretags 文件所在目录"""
    env_path = os.getenv('PRETAGS_DATA_PATH')
    if env_path:
        p = Path(env_path)
        if p.is_dir():
            return env_path
        elif p.is_file():
            return str(p.parent)
    
    # 返回当前数据文件所在目录
    return str(Path(DATA_PATH).parent)

_load_dotenv()

PORT = int(os.getenv('WEB_SHOW_PORT', 8765))
DATA_PATH = _resolve_pretags_path()

class PretagsHandler(SimpleHTTPRequestHandler):

    def send_error(self, code, message=None, explain=None):
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            msg = str(message) if message else ''
            self.wfile.write(json.dumps({'error': True, 'message': msg}).encode('utf-8'))
        except Exception:
            super().send_error(code, message, explain)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/save-pretags':
            self.handle_save_pretags()
        elif parsed_path.path == '/api/save-tag-preview':
            self.handle_save_tag_preview()
        elif parsed_path.path == '/api/add-tag':
            self.handle_add_tag()
        elif parsed_path.path == '/api/delete-tag':
            self.handle_delete_tag()
        elif parsed_path.path == '/api/edit-tag':
            self.handle_edit_tag()
        elif parsed_path.path == '/api/add-character':
            self.handle_add_character()
        elif parsed_path.path == '/api/delete-character':
            self.handle_delete_character()
        elif parsed_path.path == '/api/save-character-preview':
            self.handle_save_character_preview()
        elif parsed_path.path == '/api/switch-pretags-file':
            self.handle_switch_pretags_file()
        elif parsed_path.path == '/api/set-default-pretags-file':
            self.handle_set_default_pretags_file()
        else:
            self.send_error(404, 'Not Found')

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/get-pretags':
            self.handle_get_pretags()
        elif parsed_path.path == '/api/list-pretags-files':
            self.handle_list_pretags_files()
        elif parsed_path.path == '/api/get-current-pretags-file':
            self.handle_get_current_pretags_file()
        elif parsed_path.path == '/' or parsed_path.path == '':
            # 根路径直接返回 index.html，禁用缓存
            self._serve_file('/index.html', cache_control='no-cache, no-store, must-revalidate')
        else:
            # 静态文件：添加 Cache-Control 防止浏览器缓存旧版本
            clean_path = self.path.split('?')[0]
            if clean_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
                                     '.json', '.js', '.html', '.css', '.svg')):
                from urllib.parse import unquote
                self._serve_file(unquote(clean_path), cache_control='no-cache, no-store, must-revalidate')
            else:
                super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # ── helpers ──

    def _generate_card_id(self, card_type, **fields):
        """
        生成卡片ID（8位hash）
        - 人物类：cname + name + source
        - 其他类（画风、服装等）：name + tag
        """
        if card_type == 'character':
            text = f"{fields.get('cname', '')}{fields.get('name', '')}{fields.get('source', '')}"
        else:
            text = f"{fields.get('name', '')}{fields.get('tag', '')}"
        
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

    def _ensure_card_id(self, card_data, card_type):
        """
        确保卡片有ID，如果没有或字段变更则重新计算
        返回：(card_id, is_new_id)
        """
        if card_type == 'character':
            new_id = self._generate_card_id('character',
                cname=card_data.get('cname', ''),
                name=card_data.get('name', ''),
                source=card_data.get('source', ''))
        else:
            new_id = self._generate_card_id('tag',
                name=card_data.get('name', ''),
                tag=card_data.get('tag', ''))
        
        old_id = card_data.get('id', '')
        if old_id != new_id:
            card_data['id'] = new_id
            return new_id, True
        return old_id, False

    def _serve_file(self, filepath, cache_control=None):
        """直接读取文件并返回"""
        import mimetypes
        full_path = os.path.join(os.getcwd(), filepath.lstrip('/'))
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            ctype, _ = mimetypes.guess_type(full_path)
            self.send_response(200)
            self.send_header('Content-Type', ctype or 'application/octet-stream')
            self.send_header('Content-Length', len(content))
            self.send_header('Access-Control-Allow-Origin', '*')
            if cache_control:
                self.send_header('Cache-Control', cache_control)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f'File not found: {filepath}')

    def _read_data(self):
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_data(self, data):
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _ok(self, payload=None):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        resp = {'success': True}
        if payload:
            resp.update(payload)
        self.wfile.write(json.dumps(resp).encode('utf-8'))

    # ── GET /api/get-pretags ──

    def handle_get_pretags(self):
        data = self._read_data()
        self._ok(data)

    # ── GET /api/list-pretags-files ──

    def handle_list_pretags_files(self):
        """列出 PRETAGS_DATA_PATH 目录中的所有 JSON 文件"""
        try:
            pretags_dir = _get_pretags_directory()
            files = _scan_pretags_files(pretags_dir)
            current_file = Path(DATA_PATH).name
            
            self._ok({
                'files': files,
                'current': current_file,
                'directory': pretags_dir
            })
        except Exception as e:
            self.send_error(500, str(e))

    # ── GET /api/get-current-pretags-file ──

    def handle_get_current_pretags_file(self):
        """获取当前使用的 pretags 文件信息"""
        try:
            current_path = Path(DATA_PATH)
            self._ok({
                'filename': current_path.name,
                'path': str(current_path),
                'directory': str(current_path.parent)
            })
        except Exception as e:
            self.send_error(500, str(e))

    # ── POST /api/switch-pretags-file ──

    def handle_switch_pretags_file(self):
        """切换到指定的 pretags 文件"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            filename = req.get('filename', '')
            
            if not filename:
                self.send_error(400, 'Missing filename')
                return
            
            pretags_dir = _get_pretags_directory()
            new_path = Path(pretags_dir) / filename
            
            if not new_path.is_file():
                self.send_error(404, f'File not found: {filename}')
                return
            
            # 更新全局 DATA_PATH
            global DATA_PATH
            DATA_PATH = str(new_path)
            
            self._ok({
                'message': f'Switched to {filename}',
                'filename': filename,
                'path': str(new_path)
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    # ── POST /api/set-default-pretags-file ──

    def handle_set_default_pretags_file(self):
        """设置默认 pretags 文件"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            filename = req.get('filename', '')
            
            if not filename:
                self.send_error(400, 'Missing filename')
                return
            
            pretags_dir = _get_pretags_directory()
            file_path = Path(pretags_dir) / filename
            
            if not file_path.is_file():
                self.send_error(404, f'File not found: {filename}')
                return
            
            # 保存默认文件名
            _set_default_pretags_filename(filename)
            
            self._ok({
                'message': f'Set {filename} as default',
                'filename': filename
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    # ── POST /api/save-pretags ──

    def handle_save_pretags(self):
        """合并式保存：读取现有数据 → 按 type 合并更新 → 写回，绝不覆盖全文件"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            req_type = req.get('type', '')

            dt = self._read_data()

            if req_type == 'character':
                char_data = req.get('data', {})
                char_id = req.get('charId', '')  # 改用ID
                if not char_id:
                    self.send_error(400, 'Missing charId')
                    return
                if 'characters' not in dt:
                    dt['characters'] = {}
                
                # 获取旧数据
                existing = dt['characters'].get(char_id, {})
                old_cname = existing.get('cname', '')
                old_source = existing.get('source', '')
                old_preview = existing.get('preview', '')
                
                new_cname = char_data.get('cname', old_cname)
                new_source = char_data.get('source', old_source)
                
                # 处理预览图重命名（如果 cname 或 source 发生变化且存在预览图）
                if old_preview and (new_cname != old_cname or new_source != old_source):
                    self._rename_character_preview(old_cname, old_source, new_cname, new_source, old_preview)
                    # 更新预览图路径
                    safe_cname = new_cname.replace('/', '_').replace('\\', '_').replace(' ', '_')
                    safe_source = new_source.replace('/', '_').replace('\\', '_').replace(' ', '_')
                    new_preview = f"./data/character-previews/{safe_cname}__{safe_source}.jpg"
                    char_data['preview'] = new_preview
                
                # 合并更新：保留原条目中不在更新数据里的字段（如 preview）
                merged = {**existing, **char_data}
                
                # 计算新ID（如果关键字段变更）
                new_id, id_changed = self._ensure_card_id(merged, 'character')
                
                # 如果ID变更，需要删除旧key并创建新key
                if id_changed and new_id != char_id:
                    del dt['characters'][char_id]
                    dt['characters'][new_id] = merged
                    self._update_series_from_characters(dt)
                    self._write_data(dt)
                    self._ok({'message': 'Data saved', 'type': req_type, 'oldId': char_id, 'newId': new_id})
                    return
                else:
                    dt['characters'][char_id] = merged
                    self._update_series_from_characters(dt)
            else:
                self.send_error(400, f'Unknown save type: {req_type}')
                return

            self._write_data(dt)
            self._ok({'message': 'Data saved', 'type': req_type})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    # ── TAG PREVIEW ──

    def handle_save_tag_preview(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            tag_id = data.get('tagId')  # 改用ID
            category = data.get('category')
            image = data.get('image')
            if not tag_id or not category or not image:
                self.send_error(400, 'Missing required fields')
                return

            dt = self._read_data()
            if category not in dt.get('categories', {}) or tag_id not in dt['categories'][category]:
                self.send_error(404, f'标签ID "{tag_id}" 不存在')
                return
            
            tag_name = dt['categories'][category][tag_id].get('name', '')
            
            preview_dir = 'data/previews'
            os.makedirs(preview_dir, exist_ok=True)
            safe_name = tag_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
            filename = f"{category}_{safe_name}.jpg"
            filepath = os.path.join(preview_dir, filename)

            if 'dataUrl' in image:
                header, encoded = image['dataUrl'].split(',', 1)
                image_data = base64.b64decode(encoded)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
            elif 'url' in image:
                import urllib.request
                urllib.request.urlretrieve(image['url'], filepath)
            else:
                self.send_error(400, 'Invalid image data')
                return

            dt['categories'][category][tag_id]['preview'] = f"./data/previews/{filename}"
            self._write_data(dt)

            self._ok({'filepath': filepath, 'filename': filename})
        except Exception as e:
            print(f"Error saving tag preview: {e}")
            self.send_error(500, str(e))

    # ── HELPER: 重命名角色预览图 ──

    def _rename_character_preview(self, old_cname, old_source, new_cname, new_source, old_preview_path):
        """重命名角色预览图文件"""
        try:
            # 构建旧文件路径
            old_safe_cname = old_cname.replace('/', '_').replace('\\', '_').replace(' ', '_')
            old_safe_source = old_source.replace('/', '_').replace('\\', '_').replace(' ', '_')
            old_filename = f"{old_safe_cname}__{old_safe_source}.jpg"
            old_filepath = os.path.join('data/character-previews', old_filename)
            
            # 构建新文件路径
            new_safe_cname = new_cname.replace('/', '_').replace('\\', '_').replace(' ', '_')
            new_safe_source = new_source.replace('/', '_').replace('\\', '_').replace(' ', '_')
            new_filename = f"{new_safe_cname}__{new_safe_source}.jpg"
            new_filepath = os.path.join('data/character-previews', new_filename)
            
            # 如果旧文件存在且新旧路径不同，则重命名
            if os.path.exists(old_filepath) and old_filepath != new_filepath:
                # 如果新文件已存在，先删除（避免冲突）
                if os.path.exists(new_filepath):
                    os.remove(new_filepath)
                os.rename(old_filepath, new_filepath)
                print(f"预览图已重命名: {old_filename} -> {new_filename}")
        except Exception as e:
            print(f"重命名预览图失败: {e}")
            # 不抛出异常，允许继续保存数据

    def _rename_tag_preview(self, old_name, old_category, new_name, new_category, old_preview_path):
        """重命名标签预览图文件"""
        try:
            # 构建旧文件路径
            old_safe_name = old_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
            old_filename = f"{old_category}_{old_safe_name}.jpg"
            old_filepath = os.path.join('data/previews', old_filename)
            
            # 构建新文件路径
            new_safe_name = new_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
            new_filename = f"{new_category}_{new_safe_name}.jpg"
            new_filepath = os.path.join('data/previews', new_filename)
            
            # 如果旧文件存在且新旧路径不同，则重命名
            if os.path.exists(old_filepath) and old_filepath != new_filepath:
                if os.path.exists(new_filepath):
                    os.remove(new_filepath)
                os.rename(old_filepath, new_filepath)
                print(f"标签预览图已重命名: {old_filename} -> {new_filename}")
        except Exception as e:
            print(f"重命名标签预览图失败: {e}")
            # 不抛出异常，允许继续保存数据

    # ── CHARACTER PREVIEW ──

    def handle_save_character_preview(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            char_id = data.get('charId')  # 改用ID
            image = data.get('image')
            if not char_id or not image:
                self.send_error(400, 'Missing charId or image')
                return

            dt = self._read_data()
            if char_id not in dt.get('characters', {}):
                self.send_error(404, f'角色ID "{char_id}" 不存在')
                return
            
            char = dt['characters'][char_id]
            cname = char.get('cname', '')
            source = char.get('source', '')

            preview_dir = 'data/character-previews'
            os.makedirs(preview_dir, exist_ok=True)
            safe_cname = cname.replace('/', '_').replace('\\', '_').replace(' ', '_')
            safe_source = (source or 'unknown').replace('/', '_').replace('\\', '_').replace(' ', '_')
            filename = f"{safe_cname}__{safe_source}.jpg"
            filepath = os.path.join(preview_dir, filename)

            if 'dataUrl' in image:
                header, encoded = image['dataUrl'].split(',', 1)
                image_data = base64.b64decode(encoded)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
            elif 'url' in image:
                import urllib.request
                urllib.request.urlretrieve(image['url'], filepath)
            else:
                self.send_error(400, 'Invalid image data')
                return

            preview_path = f"./data/character-previews/{filename}"
            dt['characters'][char_id]['preview'] = preview_path
            self._write_data(dt)

            self._ok({'filepath': filepath, 'preview': preview_path})
        except Exception as e:
            print(f"Error saving character preview: {e}")
            self.send_error(500, str(e))

    # ── TAG CRUD (frontend format: data['categories'][category][tagName]) ──

    def _build_tag_entry(self, tag_data):
        """从表单数据构建前端格式的标签条目"""
        has_lora = tag_data.get('has_lora', False)
        entry = {
            'name': tag_data.get('name', ''),
            'tag': tag_data.get('tag', ''),
            'has_lora': bool(has_lora),
        }
        if has_lora:
            entry['lora_file'] = tag_data.get('lora_file', '')
            entry['lora_hash'] = tag_data.get('lora_hash', '')
            entry['unet_weight'] = tag_data.get('unet_weight', 0.8)
            entry['clip_weight'] = tag_data.get('clip_weight', 0.8)
            entry['lora_link'] = tag_data.get('lora_link', '')
        if tag_data.get('description'):
            entry['description'] = tag_data['description']
        dg = tag_data.get('d_group')
        if dg is not None and dg != 0:
            entry['d_group'] = dg
        return entry

    def handle_add_tag(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            category = data.get('category')
            tag_name = data.get('tagName')
            tag_data = data.get('tagData', {})
            if not category or not tag_name:
                self.send_error(400, 'Missing category or tagName')
                return

            dt = self._read_data()
            cats = dt.setdefault('categories', {})
            if category not in cats:
                cats[category] = {}
            
            # 生成标签ID
            tag_id = self._generate_card_id('tag',
                name=tag_name,
                tag=tag_data.get('tag', ''))
            
            # 检查ID是否已存在（支持同名卡片）
            if tag_id in cats[category]:
                self.send_error(409, f'标签ID "{tag_id}" 已存在（可能是重复的标签）')
                return

            entry = self._build_tag_entry({**tag_data, 'name': tag_name})
            entry['id'] = tag_id
            
            # 使用ID作为key
            cats[category][tag_id] = entry
            self._write_data(dt)
            self._ok({'tagName': tag_name, 'tagId': tag_id})
        except Exception as e:
            print(f"Error adding tag: {e}")
            self.send_error(500, str(e))

    def handle_delete_tag(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            category = data.get('category')
            tag_id = data.get('tagId')  # 改用ID
            if not category or not tag_id:
                self.send_error(400, 'Missing category or tagId')
                return

            dt = self._read_data()
            cats = dt.get('categories', {})
            if category not in cats or tag_id not in cats[category]:
                self.send_error(404, f'标签ID "{tag_id}" 不存在')
                return

            tag_name = cats[category][tag_id].get('name', '')
            del cats[category][tag_id]
            self._write_data(dt)
            self._ok({'tagId': tag_id, 'tagName': tag_name})
        except Exception as e:
            print(f"Error deleting tag: {e}")
            self.send_error(500, str(e))

    def handle_edit_tag(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            category = data.get('category')
            tag_id = data.get('tagId')  # 改用ID
            tag_data = data.get('tagData', {})
            if not category or not tag_id:
                self.send_error(400, 'Missing category or tagId')
                return

            dt = self._read_data()
            cats = dt.get('categories', {})
            if category not in cats or tag_id not in cats[category]:
                self.send_error(404, f'标签ID "{tag_id}" 不存在')
                return

            existing = cats[category][tag_id]
            old_name = existing.get('name', '')
            new_name = tag_data.get('name', old_name)
            old_preview = existing.get('preview', '')
            
            # 处理预览图重命名（如果标签名发生变化且存在预览图）
            if old_preview and new_name != old_name:
                self._rename_tag_preview(old_name, category, new_name, category, old_preview)
                # 更新预览图路径
                safe_name = new_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
                new_preview = f"./data/previews/{category}_{safe_name}.jpg"
            else:
                new_preview = old_preview
            
            updated = self._build_tag_entry(tag_data)
            if new_preview:
                updated['preview'] = new_preview
            elif 'preview' in existing:
                updated['preview'] = existing['preview']
            
            # 计算新ID（如果关键字段变更）
            new_id, id_changed = self._ensure_card_id(updated, 'tag')
            
            # 如果ID变更，需要删除旧key并创建新key
            if id_changed and new_id != tag_id:
                del cats[category][tag_id]
                cats[category][new_id] = updated
                self._write_data(dt)
                self._ok({'oldId': tag_id, 'newId': new_id, 'oldName': old_name, 'newName': new_name, 'preview': new_preview})
            else:
                cats[category][tag_id] = updated
                self._write_data(dt)
                self._ok({'tagId': tag_id, 'oldName': old_name, 'newName': new_name, 'preview': new_preview})
        except Exception as e:
            print(f"Error editing tag: {e}")
            self.send_error(500, str(e))

    # ── CHARACTER CRUD (frontend format: data['characters'][cname]) ──

    def _update_series_from_characters(self, dt):
        """从 characters 重建 series 索引（使用ID）"""
        series = {}
        for char_id, ch in dt.get('characters', {}).items():
            src = ch.get('source', '')
            if not src:
                continue
            if src not in series:
                series[src] = {'name': src, 'count': 0, 'characters': []}
            series[src]['count'] += 1
            series[src]['characters'].append(char_id)  # 使用ID而非name
        dt['series'] = series

    def handle_add_character(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            char_data = data.get('data', {})
            cname = char_data.get('cname', '')
            if not cname:
                self.send_error(400, 'Missing cname')
                return

            has_lora = char_data.get('has_lora', False)
            source = char_data.get('source', '')
            appearance = char_data.get('appearance', '')
            clothing = char_data.get('clothing', '')
            tags = []
            if appearance:
                tags.extend([t.strip() for t in appearance.split(',') if t.strip()])
            if clothing:
                tags.extend([t.strip() for t in clothing.split(',') if t.strip()])

            # 生成卡片ID
            char_id = self._generate_card_id('character',
                cname=cname,
                name=char_data.get('name', ''),
                source=source)

            dt = self._read_data()
            if char_id in dt.get('characters', {}):
                self.send_error(409, f'角色ID "{char_id}" 已存在（可能是重复的角色）')
                return

            entry = {
                'id': char_id,
                'cname': cname,
                'source': source,
                'name': char_data.get('name', ''),
                'appearance': appearance,
                'clothing': clothing,
                'has_lora': bool(has_lora),
                'tags': list(set(tags)),
                'tags_count': len(tags),
            }
            if has_lora:
                entry['lora_file'] = char_data.get('lora_file', '')
                entry['lora_hash'] = char_data.get('lora_hash', '')
                entry['unet_weight'] = char_data.get('unet_weight', 0.8)
                entry['clip_weight'] = char_data.get('clip_weight', 0.8)
                entry['lora_link'] = char_data.get('lora_link', '')

            if 'characters' not in dt:
                dt['characters'] = {}
            dt['characters'][char_id] = entry  # 使用ID作为key
            self._update_series_from_characters(dt)
            self._write_data(dt)
            self._ok({'cname': cname, 'charId': char_id})
        except Exception as e:
            print(f"Error adding character: {e}")
            self.send_error(500, str(e))

    def handle_delete_character(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            char_id = data.get('charId')  # 改用ID
            if not char_id:
                self.send_error(400, 'Missing charId')
                return

            dt = self._read_data()
            if char_id not in dt.get('characters', {}):
                self.send_error(404, f'角色ID "{char_id}" 不存在')
                return

            cname = dt['characters'][char_id].get('cname', '')
            del dt['characters'][char_id]
            self._update_series_from_characters(dt)
            self._write_data(dt)
            self._ok({'charId': char_id, 'cname': cname})
        except Exception as e:
            print(f"Error deleting character: {e}")
            self.send_error(500, str(e))

def main():
    # 切换到脚本所在目录，使所有相对路径正常工作
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('0.0.0.0', PORT), PretagsHandler)
    print(f'Pretags API 服务器启动在端口 {PORT}')
    print(f'访问地址: http://0.0.0.0:{PORT}')
    print(f'API 端点:')
    print(f'  POST /api/add-tag, /api/edit-tag, /api/delete-tag')
    print(f'  POST /api/add-character, /api/delete-character')
    print(f'  POST /api/save-tag-preview, /api/save-character-preview')
    print(f'  POST /api/save-pretags, GET /api/get-pretags')
    print(f'按 Ctrl+C 停止服务器')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\\n服务器已停止')
        server.server_close()

if __name__ == '__main__':
    main()
