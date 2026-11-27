import json
from pathlib import Path
def load_rules(path):
    if not path.exists():
        raise FileNotFoundError(f"找不到{path}")
    with open(path,"r",encoding="utf-8") as f:
        try:
            a=json.load(f)
        except json.JSONDecodeError as err:
            raise RuntimeError(f'json解码错误{err}') from err
        return a