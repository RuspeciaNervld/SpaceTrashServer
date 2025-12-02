
import os
import sys
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入配置文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CLIENT_A_WATCH_PATH as WATCH_PATH, CLIENT_A_SERVER_URL as SERVER_URL, CLIENT_A_CHECK_INTERVAL as CHECK_INTERVAL, CLIENT_A_TARGET_FILENAMES as TARGET_FILENAMES

# 确保监控目录存在
os.makedirs(WATCH_PATH, exist_ok=True)

class FileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_upload_times = {filename: 0 for filename in TARGET_FILENAMES}
        
    def on_modified(self, event):
        # 只处理特定文件名的修改事件
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename in TARGET_FILENAMES:
                current_time = time.time()
                # 避免短时间内重复上传（5秒内只上传一次）
                if current_time - self.last_upload_times[filename] > 5:
                    print(f"检测到文件更新: {event.src_path}")
                    # 等待文件写入完成
                    time.sleep(1)
                    upload_file(event.src_path)
                    self.last_upload_times[filename] = current_time
    
    def on_created(self, event):
        # 处理文件创建事件（首次创建时）
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename in TARGET_FILENAMES:
                current_time = time.time()
                # 避免短时间内重复上传（5秒内只上传一次）
                if current_time - self.last_upload_times[filename] > 5:
                    print(f"检测到文件创建: {event.src_path}")
                    # 等待文件写入完成
                    time.sleep(1)
                    upload_file(event.src_path)
                    self.last_upload_times[filename] = current_time

def upload_file(file_path):
    """
    上传文件到服务器
    """
    try:
        with open(file_path, 'rb') as f:
            files = {'image': (os.path.basename(file_path), f, 'image/png')}
            response = requests.post(SERVER_URL, files=files)

            if response.status_code == 200:
                result = response.json()
                print(f"上传成功: {result['message']}")
            else:
                print(f"上传失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"上传文件时出错: {e}")

def check_existing_files():
    """
    检查目标文件是否已存在
    """
    found_files = False
    for filename in TARGET_FILENAMES:
        target_path = os.path.join(WATCH_PATH, filename)
        if os.path.exists(target_path):
            print(f"发现目标文件: {target_path}")
            upload_file(target_path)
            found_files = True
    return found_files

if __name__ == "__main__":
    print(f"开始监控目录: {WATCH_PATH}")
    print(f"目标文件名: {TARGET_FILENAMES}")
    print(f"服务器地址: {SERVER_URL}")

    # 检查目标文件是否已存在
    check_existing_files()

    # 设置文件系统监控
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
