from pathlib import Path
from datetime import datetime
import hashlib



def human_size(byte_num: int):
    i = 0
    units = ['B', 'KB', 'MB', 'GB']
    while byte_num >= 1024 and i < len(units) - 1:
        byte_num = byte_num / 1024
        i += 1
    return f"{byte_num:.2f}{units[i]}"

def get_file_md5(path,chunk_size=8192):
    md5_obj=hashlib.md5()
    with open(path,"rb") as f:
        while True:
            chunk=f.read(chunk_size)
            if not chunk:
                break
            md5_obj.update(chunk)
        return md5_obj.hexdigest()

def main(r):
    print('\n以下是文件的详细信息')
    for ext, info in r["group"].items():
        print(f"\n后缀:{ext if ext else '无后缀'}")
        print(f"文件数量:{info['count']}")
        print(f"本组总大小：{human_size(info['total_bytes'])}")

        print("👉 本组重复大小文件：")
        has_dup = False
        # 使用info，不再写group[suffix]
       


        if not has_dup:
            print("    本组没有相同大小的文件")
        print('-' * 40)

    print('\n以下是总文件夹信息')
    print(f"重复文件{r["same_file"]}")
    print(f'文件总数：{r["files"]}')
    print(f'文件总大小：{human_size(r["bytes"])}')


def scan(root):
    total_amount = 0
    dir_count = 0
    total_size = 0
    group = {}
    same_file = {}
    s=Path(root)
    for item in s.rglob("*"):
        if "_dup" in item.parts:
            continue
        try:
            st = item.stat()
            suffix = item.suffix
            mtime_ts = st.st_mtime
            mtime = datetime.fromtimestamp(mtime_ts)
            mtime_str = mtime.strftime("%Y-%m-%d %H:%M:%S")

            if item.is_file():
                size = st.st_size
                total_amount += 1
                total_size += size
                path_str = str(item.absolute())

                if suffix not in group:
                    group[suffix] = {
                        "count": 0,
                        "total_bytes": 0,
                        "path": [],    # ✅补回缺失字段
                        "time": [],
                        "size_map": {}
                    }

                group[suffix]["count"] += 1
                group[suffix]["total_bytes"] += size
                group[suffix]["path"].append(path_str)
                group[suffix]["time"].append(mtime_str)

                if size not in group[suffix]["size_map"]:
                    group[suffix]["size_map"][size] = []
                group[suffix]["size_map"][size].append(path_str)

            elif item.is_dir():
                dir_count += 1
        except OSError as e:
            print(f"读取失败：{item},原因：{e}")
    for ext, info in group.items():
        for sz, path_list in info["size_map"].items():
            if len(path_list) >= 2:
                # ✅缩进进到if内部，只对重复的文件算md5
                for file_path in path_list:
                    a=get_file_md5(file_path)
                    if a not in same_file:
                        same_file[a] = []
                    same_file[a].append(file_path)
    return {
        "files": total_amount,
        "dirs": dir_count,
        "bytes": total_size,
        "group": group,
        "same_file": same_file,
    }

