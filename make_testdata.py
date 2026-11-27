# -*- coding: utf-8 -*-
"""生成项目 02 的测试数据：模拟一个真实又乱的目录。

用法：
    python make_testdata.py D:\\py\\test\\项目2\\_sandbox

跑完会打印一份"标准答案"（文件数、重复组数、可回收空间），
写扫描器的时候拿它对照，就知道自己算得对不对。
"""
import os
import random
import shutil
import stat
import sys
import time
from pathlib import Path

random.seed(42)  # 固定种子，每次生成的数据完全一样，便于对比

root = Path(sys.argv[1] if len(sys.argv) > 1 else '_sandbox')


def _force_remove(func, path, exc):
    """Windows 下只读文件删不掉：先去掉只读属性再删。"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


if root.exists():
    print(f'目标已存在，先删掉：{root}')
    shutil.rmtree(root, onexc=_force_remove)
root.mkdir(parents=True)

now = time.time()
YEAR = 365 * 24 * 3600


def stamp(days_ago, hours=0):
    return now - days_ago * 24 * 3600 - hours * 3600


def write(rel, data, days_ago=30, readonly=False):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    t = stamp(days_ago)
    os.utime(p, (t, t))
    if readonly:
        os.chmod(p, 0o444)
    return p


# ---------------------------------------------------------------- 内容样本
def blob(tag, size):
    head = tag.encode() * 8
    body = bytes(random.getrandbits(8) for _ in range(size))
    return head + body


PHOTO = blob('JPEG', 180_000)      # 一张"照片"，会被复制三份
SCREEN = blob('PNG', 90_000)       # 一张"截图"，两份
DOC = blob('DOCX', 40_000)         # 一份文档，两份
VIDEO = blob('MP4', 2_000_000)     # 一个 2MB 视频，独占
NOTES = blob('TXT', 1_200)         # 笔记，三份

# ---------------------------------------------------------------- 重复文件（同一个内容，不同名字/不同目录）
dups = [
    (PHOTO, ['照片/IMG_2031.jpg', '照片/备份/IMG_2031 (1).jpg', '下载/IMG_2031.jpg']),
    (SCREEN, ['照片/截图 2026-03-12.png', '下载/截图 2026-03-12.png']),
    (DOC, ['文档/简历.docx', '桌面副本/简历 最终版.docx']),
    (NOTES, ['笔记/todo.txt', '笔记/旧/todo.txt', '笔记/旧/备份/todo (副本).txt']),
]

dup_groups = 0
dup_waste = 0
for content, names in dups:
    for i, name in enumerate(names):
        write(name, content, days_ago=random.randint(1, 300))
    dup_groups += 1
    dup_waste += content.__len__() * (len(names) - 1)

# ---------------------------------------------------------------- 独占文件（各种扩展名、各种日期、零散分布）
EXTS = ['jpg', 'png', 'pdf', 'py', 'txt', 'zip', 'docx', 'xlsx', 'mp4', 'log']
FOLDERS = ['照片/2026', '照片/2026/旅行', '下载', '文档/课程', '文档/课程/大三上',
           '代码/练习', '代码/练习/第1章', '杂项', '杂项/待整理']
names_cn = ['报告', '课堂笔记', '期末复习', '实验数据', '照片备份', '会议记录', '作业']

for i in range(60):
    ext = random.choice(EXTS)
    folder = random.choice(FOLDERS)
    if random.random() < 0.3:
        base = random.choice(names_cn)
        fname = f'{base}{i}.{ext}'
    else:
        fname = f'file_{i:03d}.{ext}'
    size = random.randint(2_000, 60_000)
    write(f'{folder}/{fname}', blob(ext.upper(), size), days_ago=random.randint(0, 400))

# ---------------------------------------------------------------- 边界情况
write('杂项/空文件.txt', b'', days_ago=120)                       # 0 字节
write('杂项/空文件 2.log', b'', days_ago=90)                      # 0 字节
write('杂项/只读文件.pdf', blob('PDF', 5_000), days_ago=60, readonly=True)  # 移动会失败
write('杂项/' + '超长文件名' * 12 + '.txt', blob('LONG', 800), days_ago=15)
write('杂项/带 空格 和-符号.txt', blob('ODD', 600), days_ago=45)
write('视频/一节课的录屏.mp4', VIDEO, days_ago=7)                 # 2MB 大文件

# ---------------------------------------------------------------- 统计（标准答案）
import hashlib
from collections import defaultdict

files = 0
total = 0
by_key = defaultdict(list)

for p in root.rglob('*'):
    if not p.is_file():
        continue
    size = p.stat().st_size
    files += 1
    total += size
    if size == 0:
        continue  # 0 字节文件哈希相同，但真实工具一般不把它们当"重复"
    h = hashlib.md5(p.read_bytes()).hexdigest()
    by_key[(size, h)].append(p)

groups = {k: v for k, v in by_key.items() if len(v) > 1}
waste = sum(k[0] * (len(v) - 1) for k, v in groups.items())

print()
print('=' * 52)
print(f'测试目录: {root}')
print(f'文件总数: {files}')
print(f'总大小:   {total / 1024 / 1024:.2f} MB')
print(f'重复组:   {len(groups)} 组，涉及 {sum(len(v) for v in groups.values())} 个文件')
print(f'可回收:   {waste / 1024 / 1024:.2f} MB（每组保留 1 份后）')
print('=' * 52)
for k, v in groups.items():
    print(f'  {k[0]:>8,} 字节 × {len(v)} 份 -> {[x.name for x in v]}')
print('=' * 52)
print('扫描器的输出应该和上面这几个数字对得上。')
print('目录里还有一个只读文件，--apply 时它会移动失败，'
      '程序应该提示但继续处理其他文件。')
print('另有 2 个 0 字节文件：它们的哈希相同，但要不要算"重复"由你决定'
      '（真实工具一般排除 0 字节）。')
