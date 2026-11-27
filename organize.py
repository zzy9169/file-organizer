import argparse
from scan import main,scan
import logging
from pathlib import Path
import shutil
import csv
logger=logging.getLogger("FileManager")
logger.setLevel(logging.INFO)
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
file_handler = logging.FileHandler(LOG_DIR / "organize.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

parser=argparse.ArgumentParser(description="文件批量管理器")
parser.add_argument("target", help="要整理的目录")
parser.add_argument("--apply", action="store_true",help="真的移动文件；不加只预览")
args = parser.parse_args()

def write_report(r, out=None):
    out = out or Path(__file__).parent / "report.csv"
    groups = [(md5, ps) for md5, ps in r["same_file"].items() if len(ps) >= 2]
    groups.sort(key=lambda kv: -len(kv[1]))        # 组大的排前面

    rows = []
    for gid, (md5, paths) in enumerate(groups, 1):
        paths = sorted(paths)                       # 和 build_ops 同一套规则
        keep = paths[0]
        for p in paths:
            rows.append({
                "重复组": gid,
                "原路径": p,
                "大小(字节)": Path(p).stat().st_size,
                "哈希": md5,
                "建议动作": "保留" if p == keep else "归档",
            })

    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        FIELDS = ["重复组", "原路径", "大小(字节)", "哈希", "建议动作"]
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

def build_ops(r, root):
    root = Path(root).resolve()
    ops = []
    for md5, paths in r["same_file"].items():
        if len(paths) < 2:
            continue                 # 不是重复组
        paths = sorted(paths)        # 排序，保证每次保留同一份
        keep = paths[0]
        for p in paths[1:]:
            rel = Path(p).relative_to(root)      # 相对路径
            dst = root / "_dup" / rel       # 搬到 _dup 下，保持原结构
            ops.append((Path(p), dst, md5, keep))
    return ops

def move_duplicate(ops):
    success=0
    fail=0
    for src, dst, md5, keep in ops:
        try:
            if dst.exists():
                logger.warning("跳过（目标已存在）%s", dst)
                fail += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src,dst)
            logger.info(f"将{src}->{dst}")
            success+=1
        except OSError as e:
            logger.warning("跳过 %s:%s", src, e)
            fail+=1
    logger.info("完成：成功 %d,失败 %d", success, fail)
    return success,fail
r=scan(args.target)
main(r)
write_report(r)
ops = build_ops(r, args.target)
for src, dst, md5, keep in ops:
        print(f"将 {src}  →  {dst}")
print(f"共 {len(ops)} 个文件待移动")
if args.apply:
    move_duplicate(ops)
else:
    print("文件未移动，加--apply开始")




