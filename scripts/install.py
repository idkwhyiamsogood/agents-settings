"""Portable, explicit-destination installer. Preview by default; no live export."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {
    'codex-rules': [('codex/AGENTS.md', 'AGENTS.md'), ('codex/document-rules', 'document-rules')],
    'codex-config': [('codex/config.toml', 'config.toml')],
    'claude-rules': [('claude/CLAUDE.md', 'CLAUDE.md')],
    'skills': [('skills/figma-build', 'figma-build'), ('skills/figma-codegen', 'figma-codegen'),
               ('skills/repomix-codebase-parsing', 'repomix-codebase-parsing')],
    'cursor-user': [('cursor/user', '.')],
    'vscode-user': [('vscode/user', '.')],
}

def plan(component, destination):
    result = []
    for source, relative in COMPONENTS[component]:
        source = ROOT / source
        for item in sorted(source.rglob('*')) if source.is_dir() else [source]:
            if item.is_symlink():
                raise ValueError('Source symlinks are unsupported')
            if item.is_file():
                target = destination / relative
                if source.is_dir():
                    target /= item.relative_to(source)
                # Reject symlinked destinations or parents, including dangling links.
                if any(p.is_symlink() for p in [target, *target.parents]):
                    raise ValueError(f'Destination contains a symlink: {target}')
                if any(p.exists() and not p.is_dir() for p in target.parents):
                    raise ValueError(f'Destination parent is not a directory: {target}')
                status = 'create'
                if target.exists():
                    status = 'same' if target.is_file() and target.read_bytes() == item.read_bytes() else 'conflict'
                result.append((item, target, status))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', choices=COMPONENTS, required=True)
    parser.add_argument('--destination', type=Path, required=True,
                        help='Actual directory discovered from the target application')
    parser.add_argument('--apply', action='store_true', help='Copy missing files after a conflict-free preflight')
    args = parser.parse_args()
    destination = args.destination.expanduser().absolute()
    if destination == ROOT or ROOT in destination.parents:
        parser.error('Destination must be outside the source repository')
    rows = plan(args.component, destination)
    for _, target, status in rows:
        print(f'{status}: {target}')
    if any(status == 'conflict' for _, _, status in rows):
        parser.exit(1, 'Conflicts found; nothing written. Merge manually or choose a clean staging directory.\n')
    if args.apply:
        for source, target, status in rows:
            if status == 'create':
                target.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation also avoids overwriting a file appearing after preflight.
                with target.open('xb') as output, source.open('rb') as original:
                    shutil.copyfileobj(original, output)
        print('Applied. Restart the application and verify discovery.')
    else:
        print('Preview only. Add --apply to copy missing files.')

if __name__ == '__main__':
    main()
