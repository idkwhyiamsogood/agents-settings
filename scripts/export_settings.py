#!/usr/bin/env python3
"""Export an allowlisted snapshot of agent settings; never copy account/session state."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEY = re.compile(r'^(?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|client[_-]?secret|password|authorization|secret[_-]?key|token)$', re.I)
SECRET_PATTERNS = [
    re.compile(r'\bsk-(?:proj-|ant-api\d+-)?[A-Za-z0-9_-]{32,}\b'),
    re.compile(r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b'),
]
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv'}
SKIP_NAMES = {'.DS_Store', '.sync-manifest.json'}

def parse_jsonc(data):
    text = data.decode('utf-8-sig')
    token = r'"(?:\\.|[^"\\])*"'
    text = re.sub(token + r'|//[^\n]*|/\*[\s\S]*?\*/',
                  lambda m: m[0] if m[0].startswith('"') else '', text)
    text = re.sub(token + r'|,(?=\s*[}\]])',
                  lambda m: m[0] if m[0].startswith('"') else '', text)
    return json.loads(text)

def clean_json(obj):
    if isinstance(obj, dict):
        return {k: '<REDACTED>' if SECRET_KEY.match(k) and isinstance(v, str) and v else clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(v) for v in obj]
    return obj

def validate_secret_free(data, name):
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return
    if any(p.search(text) for p in SECRET_PATTERNS):
        raise ValueError(f'Possible credential in {name}; export blocked (value not printed)')
    if re.search(r'https?://[^\s/]+:[^\s/@]+@', text):
        raise ValueError(f'URL credentials in {name}; export blocked')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--home', type=Path, default=Path.home())
    ap.add_argument('--check', action='store_true', help='Validate existing snapshot without reading live settings')
    args = ap.parse_args()
    if args.check:
        manifest = json.loads((ROOT/'manifest.json').read_text())
        for row in manifest['files']:
            p = ROOT/row['path']
            data = p.read_bytes()
            if hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError(f'Snapshot changed: {row["path"]}; rerun export')
            validate_secret_free(data, row['path'])
        for row in manifest.get('symlinks', []):
            link = ROOT/row['path']
            assert link.is_symlink() and str(link.readlink()) == row['target'] and link.exists(), row['path']
        print(f'Validated {len(manifest["files"])} snapshot files')
        return
    home = args.home.expanduser().resolve()
    pending = {}
    links = []
    def put(rel, data):
        validate_secret_free(data, rel)
        pending[str(rel)] = data
    def copy_file(src, dest, json_filter=False):
        if not src.is_file():
            return
        data = src.read_bytes()
        if json_filter and data.strip():
            try:
                data = (json.dumps(clean_json(parse_jsonc(data)), ensure_ascii=False, indent=2)+'\n').encode()
            except json.JSONDecodeError:
                raise ValueError(f'Expected JSON or JSONC: {src}')
        elif src.suffix == '.toml':
            text = data.decode()
            text = re.sub(r'(?im)^(\s*(?:api_key|access_token|refresh_token|client_secret|password|authorization)\s*=\s*)["\'][^"\'\n]*["\']', r'\1"<REDACTED>"', text)
            data = text.encode()
        put(dest, data)
    def copy_tree(src, dest):
        if not src.is_dir():
            return
        for p in sorted(src.rglob('*')):
            rel = p.relative_to(src)
            if any(x in SKIP_DIRS for x in rel.parts) or p.name in SKIP_NAMES:
                continue
            if p.is_symlink():
                # Skill links are exported separately as metadata, not traversed blindly.
                links.append({'path': str(Path(dest)/rel), 'target': str(p.readlink())})
            elif p.is_file():
                copy_file(p, Path(dest)/rel, p.suffix == '.json')
    codex = home/'.codex'
    for name in ['AGENTS.md', 'config.toml']:
        copy_file(codex/name, 'codex/'+name)
    for name in ['document-rules', 'rules', 'skills']:
        copy_tree(codex/name, 'codex/'+name)
    plugins = []
    cache = codex/'plugins/cache'
    for meta in sorted(cache.rglob('.codex-plugin/plugin.json')) if cache.exists() else []:
        version_dir = meta.parent.parent
        dest = Path('codex/plugins/cache')/version_dir.relative_to(cache)
        copy_tree(version_dir/'skills', dest/'skills')
        copy_file(meta, dest/'.codex-plugin/plugin.json', True)
        copy_file(version_dir/'.app.json', dest/'.app.json', True)
        for name in ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'NOTICE', 'README.md']:
            copy_file(version_dir/name, dest/name)
        install = version_dir.parent/'.codex-remote-plugin-install.json'
        copy_file(install, dest.parent/install.name, True)
        plugins.append({'name': version_dir.parent.name, 'version': version_dir.name, 'path': str(dest)})
    put('codex/plugins/installed.json', (json.dumps(plugins, ensure_ascii=False, indent=2)+'\n').encode())
    claude = home/'.claude'
    for name in ['CLAUDE.md', 'settings.json', 'settings.local.json']:
        copy_file(claude/name, 'claude/'+name, name.endswith('.json'))
    for name in ['skills', 'skills-library', 'agents', 'commands', 'rules']:
        copy_tree(claude/name, 'claude/'+name)
    claude_config = home/'.claude.json'
    if claude_config.is_file():
        config = json.loads(claude_config.read_text())
        put('claude/mcp.json', (json.dumps(clean_json({'mcpServers': config.get('mcpServers', {})}), ensure_ascii=False, indent=2)+'\n').encode())
    cursor = home/'.cursor'
    for name in ['mcp.json', 'argv.json']:
        copy_file(cursor/name, 'cursor/'+name, True)
    for name in ['skills', 'skills-cursor', 'rules']:
        copy_tree(cursor/name, 'cursor/'+name)
    for app, folder in [('cursor', 'Cursor'), ('vscode', 'Code')]:
        src = home/'.config'/folder/'User'
        for name in ['settings.json', 'keybindings.json', 'mcp.json']:
            # Editor files may be JSONC; normalize before filtering credentials.
            copy_file(src/name, f'{app}/user/{name}', True)
        copy_tree(src/'snippets', f'{app}/user/snippets')
    put('skill-links.json', (json.dumps(links, ensure_ascii=False, indent=2)+'\n').encode())
    # Build everything before writing, so a rejected credential cannot partially export a snapshot.
    rows = []
    for rel, data in sorted(pending.items()):
        dst = ROOT/rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        rows.append({'path': rel, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    for row in links:
        dst = ROOT/row['path']
        resolved = (dst.parent/row['target']).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            raise ValueError(f'Invalid skill link: {row["path"]}')
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink():
            if str(dst.readlink()) != row['target']:
                raise ValueError(f'Existing link differs: {row["path"]}')
        elif dst.exists():
            raise ValueError(f'Existing skill conflicts: {row["path"]}')
        else:
            dst.symlink_to(row['target'], target_is_directory=True)
    manifest_path = ROOT/'manifest.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    stale = sorted({x['path'] for x in previous.get('files', [])} - pending.keys())
    manifest_path.write_text(json.dumps({'exported_at': datetime.now(timezone.utc).isoformat(), 'files': rows, 'symlinks': links, 'stale_files_to_review': stale}, ensure_ascii=False, indent=2)+'\n')
    if stale:
        raise ValueError('Stale snapshot files need manual review; no files deleted')
    print(f'Exported {len(rows)} files; {len(plugins)} plugins; {len(links)} skill links')

if __name__ == '__main__':
    main()
