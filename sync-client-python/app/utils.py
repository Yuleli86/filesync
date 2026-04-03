import os
import hashlib
import time
from typing import Optional, List
from datetime import datetime
from app.models import FileData


def calculate_file_hash(file_path: str) -> str:
    if os.path.isdir(file_path):
        return hashlib.md5(file_path.encode()).hexdigest()
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_size(file_path: str) -> int:
    if os.path.isdir(file_path):
        return 0
    return os.path.getsize(file_path)


def get_last_modified(file_path: str) -> datetime:
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp)


def create_file_data(file_path: str, base_dir: str) -> FileData:
    rel_path = os.path.relpath(file_path, base_dir)
    dir_path = os.path.dirname(rel_path)
    filename = os.path.basename(file_path)
    
    return FileData(
        path=dir_path if dir_path else "",
        filename=filename,
        size=get_file_size(file_path),
        file_hash=calculate_file_hash(file_path),
        last_modified=get_last_modified(file_path),
        is_directory=os.path.isdir(file_path)
    )


def walk_directory(directory: str) -> List[str]:
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            file_list.append(dir_path)
    return file_list


def ensure_directory(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def is_file_changed(file_path: str, old_hash: str) -> bool:
    if not os.path.exists(file_path):
        return True
    current_hash = calculate_file_hash(file_path)
    return current_hash != old_hash
