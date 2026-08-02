import re
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
settings_file = repo_root / 'backend' / 'app' / 'services' / 'settings_catalog.py'
defs_file = repo_root / 'backend' / 'app' / 'config' / 'definitions.py'

text = settings_file.read_text(encoding='utf-8')
# find _config_field("id", "Title", ... group="x",\n                        key="y",
pattern = re.compile(r"_config_field\([\s\S]*?group=\s*\"([a-z0-9_]+)\"[\s\S]*?key=\s*\"([a-z0-9_]+)\"", re.I)
matches = pattern.findall(text)
keys = {f"{g}.{k}" for g,k in matches}

# also include _local_preference and others referencing config? But focus on config_field

# parse definitions for full_key occurrences by finding "key=" lines near group
defs_text = defs_file.read_text(encoding='utf-8')
def_pattern = re.compile(r"config_definition\([\s\S]*?group=\s*\"([a-z0-9_]+)\"[\s\S]*?key=\s*\"([a-z0-9_]+)\"", re.I)
def_matches = def_pattern.findall(defs_text)
def_keys = {f"{g}.{k}" for g,k in def_matches}

missing = sorted(list(keys - def_keys))
print('Total settings_catalog keys:', len(keys))
print('Total definitions:', len(def_keys))
print('Missing count:', len(missing))
for m in missing:
    print(m)
