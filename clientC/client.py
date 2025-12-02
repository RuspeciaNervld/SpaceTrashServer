
import os
import sys
import time
import requests
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入配置文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    CLIENT_C_SERVER_URL as SERVER_URL, 
    CLIENT_C_CHECK_INTERVAL as CHECK_INTERVAL, 
    CLIENT_C_JSON_FILENAME as JSON_FILENAME,
    CLIENT_C_GLB_FILENAME as GLB_FILENAME
)

# 获取文件所在目录
# 将相对路径转换为绝对路径
if not os.path.isabs(JSON_FILENAME):
    JSON_FILENAME = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), JSON_FILENAME))
if not os.path.isabs(GLB_FILENAME):
    GLB_FILENAME = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), GLB_FILENAME))

WATCH_PATH = os.path.dirname(JSON_FILENAME)
if not WATCH_PATH:  # 如果是相对路径，则使用当前目录
    WATCH_PATH = '.'

# 确保监控目录存在
os.makedirs(WATCH_PATH, exist_ok=True)

class FileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_upload_time = 0
        self.json_updated = False
        self.glb_updated = False
        self.json_last_modified = 0  # 记录JSON文件最后修改时间
        self.glb_last_modified = 0   # 记录GLB文件最后修改时间
        self.upload_cooldown = 3     # 上传后的冷却时间（秒），防止重复检测
        self.last_uploaded_files = set()  # 记录最近上传的文件路径
        print("文件监控器已初始化")

    def on_modified(self, event):
        # 处理文件修改事件
        if not event.is_directory:
            current_time = time.time()
            print(f"[监控日志] 检测到文件修改: {event.src_path}")
            
            # 检查是否在冷却期内
            if event.src_path in self.last_uploaded_files and current_time - self.last_upload_time < self.upload_cooldown:
                print(f"[监控日志] 文件在冷却期内，忽略修改事件 (剩余冷却时间: {self.upload_cooldown - (current_time - self.last_upload_time):.1f}秒)")
                return
            
            # 检查是否是目标文件
            if event.src_path == JSON_FILENAME:
                print(f"[监控日志] 这是目标JSON文件")
                # 更新JSON文件最后修改时间
                self.json_last_modified = current_time
                self.json_updated = True
                print(f"[监控日志] JSON文件状态: 已更新 (修改时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))})")
            elif event.src_path == GLB_FILENAME:
                print(f"[监控日志] 这是目标GLB文件")
                # 更新GLB文件最后修改时间
                self.glb_last_modified = current_time
                self.glb_updated = True
                print(f"[监控日志] GLB文件状态: 已更新 (修改时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))})")
            else:
                print(f"[监控日志] 非目标文件，忽略")
                return
            
            # 检查两个文件是否都已更新
            if self.json_updated and self.glb_updated:
                print(f"[监控日志] 两个文件都已更新，准备上传")
                print(f"[监控日志] JSON文件最后修改: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.json_last_modified))}")
                print(f"[监控日志] GLB文件最后修改: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.glb_last_modified))}")
                
                # 等待文件写入完成
                print(f"[监控日志] 等待文件写入完成...")
                time.sleep(2)
                
                # 再次检查文件是否存在且可读
                if os.path.exists(JSON_FILENAME) and os.path.exists(GLB_FILENAME):
                    try:
                        # 尝试读取文件确保它们已完全写入
                        with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
                            json.load(f)  # 验证JSON格式
                        with open(GLB_FILENAME, 'rb') as f:
                            f.read(1)  # 尝试读取一个字节
                        
                        print(f"[监控日志] 文件验证通过，开始上传")
                        
                        # 立即重置标志，防止重复上传
                        self.json_updated = False
                        self.glb_updated = False
                        
                        # 将文件添加到最近上传的集合中
                        self.last_uploaded_files.add(GLB_FILENAME)
                        self.last_uploaded_files.add(JSON_FILENAME)
                        
                        # 根据JSON内容确定文件类型
                        file_type = determine_file_type(JSON_FILENAME)
                        print(f"[监控日志] 根据JSON内容确定文件类型: {file_type}")
                        
                        # 执行上传
                        upload_files(GLB_FILENAME, JSON_FILENAME, file_type)
                        
                        self.last_upload_time = current_time
                        print(f"[监控日志] 上传完成，文件更新标志已重置")
                        
                        # 清理过期的上传记录（超过冷却时间的记录）
                        self.last_uploaded_files = {path for path in self.last_uploaded_files if current_time - self.last_upload_time < self.upload_cooldown}
                    except Exception as e:
                        print(f"[监控日志] 文件验证失败: {e}")
                else:
                    print(f"[监控日志] 文件不存在，无法上传")
            else:
                print(f"[监控日志] 等待另一个文件更新 (JSON: {self.json_updated}, GLB: {self.glb_updated})")

    def on_created(self, event):
        # 处理文件创建事件（首次创建时）
        if not event.is_directory:
            current_time = time.time()
            print(f"[监控日志] 检测到文件创建: {event.src_path}")
            
            # 检查是否在冷却期内
            if event.src_path in self.last_uploaded_files and current_time - self.last_upload_time < self.upload_cooldown:
                print(f"[监控日志] 文件在冷却期内，忽略创建事件 (剩余冷却时间: {self.upload_cooldown - (current_time - self.last_upload_time):.1f}秒)")
                return
            
            # 检查是否是目标文件
            if event.src_path == JSON_FILENAME:
                print(f"[监控日志] 这是目标JSON文件")
                # 更新JSON文件最后修改时间
                self.json_last_modified = current_time
                self.json_updated = True
                print(f"[监控日志] JSON文件状态: 已创建 (创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))})")
            elif event.src_path == GLB_FILENAME:
                print(f"[监控日志] 这是目标GLB文件")
                # 更新GLB文件最后修改时间
                self.glb_last_modified = current_time
                self.glb_updated = True
                print(f"[监控日志] GLB文件状态: 已创建 (创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))})")
            else:
                print(f"[监控日志] 非目标文件，忽略")
                return
            
            # 检查两个文件是否都已创建
            if self.json_updated and self.glb_updated:
                print(f"[监控日志] 两个文件都已创建，准备上传")
                print(f"[监控日志] JSON文件创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.json_last_modified))}")
                print(f"[监控日志] GLB文件创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.glb_last_modified))}")
                
                # 等待文件写入完成
                print(f"[监控日志] 等待文件写入完成...")
                time.sleep(2)
                
                # 再次检查文件是否存在且可读
                if os.path.exists(JSON_FILENAME) and os.path.exists(GLB_FILENAME):
                    try:
                        # 尝试读取文件确保它们已完全写入
                        with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
                            json.load(f)  # 验证JSON格式
                        with open(GLB_FILENAME, 'rb') as f:
                            f.read(1)  # 尝试读取一个字节
                        
                        print(f"[监控日志] 文件验证通过，开始上传")
                        
                        # 立即重置标志，防止重复上传
                        self.json_updated = False
                        self.glb_updated = False
                        
                        # 将文件添加到最近上传的集合中
                        self.last_uploaded_files.add(GLB_FILENAME)
                        self.last_uploaded_files.add(JSON_FILENAME)
                        
                        # 根据JSON内容确定文件类型
                        file_type = determine_file_type(JSON_FILENAME)
                        print(f"[监控日志] 根据JSON内容确定文件类型: {file_type}")
                        
                        # 执行上传
                        upload_files(GLB_FILENAME, JSON_FILENAME, file_type)
                        
                        self.last_upload_time = current_time
                        print(f"[监控日志] 上传完成，文件更新标志已重置")
                        
                        # 清理过期的上传记录（超过冷却时间的记录）
                        self.last_uploaded_files = {path for path in self.last_uploaded_files if current_time - self.last_upload_time < self.upload_cooldown}
                    except Exception as e:
                        print(f"[监控日志] 文件验证失败: {e}")
                else:
                    print(f"[监控日志] 文件不存在，无法上传")
            else:
                print(f"[监控日志] 等待另一个文件创建 (JSON: {self.json_updated}, GLB: {self.glb_updated})")

def determine_file_type(json_path):
    """
    根据JSON文件内容确定文件类型
    返回: 'recycle', 'unrecycle' 或 'harmful'
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据格式
        if not isinstance(data, list) or len(data) == 0:
            print(f"[类型判断] JSON数据格式不正确，使用默认类型")
            return 'unrecycle'  # 默认类型
        
        # 获取第一个元素
        item = data[0]
        if 'output' not in item or 'tag' not in item['output'] or 'harmfulness' not in item['output']:
            print(f"[类型判断] JSON数据缺少必要字段，使用默认类型")
            return 'unrecycle'  # 默认类型
        
        tags = item['output']['tag']
        harmfulness = item['output']['harmfulness']
        
        print(f"[类型判断] 标签: {tags}")
        print(f"[类型判断] 危害性: {harmfulness}")
        
        # 判断类型
        # 大小写不敏感比较
        tags = [tag.lower() for tag in tags]
        harmfulness = [h.lower() for h in harmfulness]
        if 'non-harmful' in harmfulness:
            if 'non-recyclable' in tags:
                return 'unrecycle'
            else:
                return 'recycle'
        else:
            return 'harmful'
            
    except Exception as e:
        print(f"[类型判断] 处理JSON文件时出错: {e}")
        return 'unrecycle'  # 默认类型

def upload_files(glb_path, json_path, file_type='unrecycle'):
    """
    上传GLB和JSON文件到服务器B
    """
    print(f"[上传日志] 开始上传文件")
    print(f"[上传日志] GLB文件路径: {glb_path}")
    print(f"[上传日志] JSON文件路径: {json_path}")
    print(f"[上传日志] 文件类型: {file_type}")
    print(f"[上传日志] 服务器地址: {SERVER_URL}")
    
    try:
        # 获取文件大小
        glb_size = os.path.getsize(glb_path) if os.path.exists(glb_path) else 0
        json_size = os.path.getsize(json_path) if os.path.exists(json_path) else 0
        print(f"[上传日志] GLB文件大小: {glb_size} 字节")
        print(f"[上传日志] JSON文件大小: {json_size} 字节")
        
        print(f"[上传日志] 正在读取文件...")
        
        # 根据文件类型修改GLB文件名
        base_name, ext = os.path.splitext(os.path.basename(glb_path))
        if file_type == 'recycle':
            glb_filename = f"{base_name}_recycle{ext}"
        elif file_type == 'harmful':
            glb_filename = f"{base_name}_harmful{ext}"
        else:  # unrecycle
            glb_filename = f"{base_name}_unrecycle{ext}"
        
        print(f"[上传日志] 修改后的GLB文件名: {glb_filename}")
        
        with open(glb_path, 'rb') as glb_file, open(json_path, 'r', encoding='utf-8') as json_file:
            files = {
                'glb': (glb_filename, glb_file, 'model/gltf-binary'),
                'json': (os.path.basename(json_path), json_file, 'application/json')
            }
            
            print(f"[上传日志] 正在发送请求到服务器...")
            start_time = time.time()
            response = requests.post(SERVER_URL, files=files)
            end_time = time.time()
            
            print(f"[上传日志] 请求完成，耗时: {end_time - start_time:.2f}秒")
            print(f"[上传日志] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"[上传日志] 上传成功: {result.get('message', '无消息')}")
                    if 'filepath' in result:
                        print(f"[上传日志] 服务器保存路径: {result['filepath']}")
                    elif 'recycle_path' in result and 'unrecycle_path' in result:
                        print(f"[上传日志] 服务器保存路径(回收站): {result['recycle_path']}")
                        print(f"[上传日志] 服务器保存路径(非回收站): {result['unrecycle_path']}")
                except json.JSONDecodeError:
                    print(f"[上传日志] 上传成功，但响应不是有效的JSON格式")
                    print(f"[上传日志] 响应内容: {response.text[:100]}...")
            else:
                print(f"[上传日志] 上传失败")
                print(f"[上传日志] 错误信息: {response.text}")
    except Exception as e:
        print(f"[上传日志] 上传文件时出错: {type(e).__name__}: {e}")
        import traceback
        print(f"[上传日志] 详细错误信息:\n{traceback.format_exc()}")

def check_existing_files():
    """
    检查目标文件是否已存在
    """
    print(f"[检查日志] 开始检查目标文件")
    glb_path = GLB_FILENAME
    json_path = JSON_FILENAME
    
    print(f"[检查日志] 检查GLB文件: {glb_path}")
    glb_exists = os.path.exists(glb_path)
    if glb_exists:
        glb_size = os.path.getsize(glb_path)
        glb_mtime = os.path.getmtime(glb_path)
        print(f"[检查日志] GLB文件存在，大小: {glb_size} 字节，修改时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(glb_mtime))}")
    else:
        print(f"[检查日志] GLB文件不存在")
    
    print(f"[检查日志] 检查JSON文件: {json_path}")
    json_exists = os.path.exists(json_path)
    if json_exists:
        json_size = os.path.getsize(json_path)
        json_mtime = os.path.getmtime(json_path)
        print(f"[检查日志] JSON文件存在，大小: {json_size} 字节，修改时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(json_mtime))}")
        
        # 尝试解析JSON文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print(f"[检查日志] JSON文件格式正确")
            if 'type' in json_data:
                print(f"[检查日志] JSON文件包含type字段: {json_data['type']}")
            else:
                print(f"[检查日志] 警告: JSON文件不包含type字段")
        except json.JSONDecodeError as e:
            print(f"[检查日志] 警告: JSON文件格式错误: {e}")
    else:
        print(f"[检查日志] JSON文件不存在")

    if glb_exists and json_exists:
        print(f"[检查日志] 两个目标文件都存在，准备上传")
        
        # 根据JSON内容确定文件类型
        file_type = determine_file_type(json_path)
        print(f"[检查日志] 根据JSON内容确定文件类型: {file_type}")
        
        upload_files(glb_path, json_path, file_type)
        return True
    elif glb_exists:
        print(f"[检查日志] 仅发现GLB文件: {glb_path}")
        return False
    elif json_exists:
        print(f"[检查日志] 仅发现JSON文件: {json_path}")
        return False
    else:
        print(f"[检查日志] 未找到目标文件")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ClientC 启动中...")
    print("=" * 60)
    print(f"[启动日志] 监控目录: {WATCH_PATH}")
    print(f"[启动日志] 目标JSON文件: {JSON_FILENAME}")
    print(f"[启动日志] 目标GLB文件: {GLB_FILENAME}")
    print(f"[启动日志] 服务器地址: {SERVER_URL}")
    print(f"[启动日志] 检查间隔: {CHECK_INTERVAL}秒")
    
    # 检查目标文件是否已存在
    print("\n[启动日志] 检查目标文件...")
    check_existing_files()
    
    # 设置文件系统监控
    print("\n[启动日志] 初始化文件监控器...")
    event_handler = FileHandler()
    observer = Observer()
    
    # 获取文件所在目录进行监控
    glb_dir = os.path.dirname(GLB_FILENAME)
    json_dir = os.path.dirname(JSON_FILENAME)
    
    print(f"[启动日志] GLB文件所在目录: {glb_dir}")
    print(f"[启动日志] JSON文件所在目录: {json_dir}")
    
    # 如果两个文件在不同目录，则分别监控
    if glb_dir != json_dir:
        print(f"[启动日志] 设置监控两个目录: {glb_dir} 和 {json_dir}")
        observer.schedule(event_handler, glb_dir, recursive=False)
        observer.schedule(event_handler, json_dir, recursive=False)
    else:
        # 如果在同一目录，只监控一个
        print(f"[启动日志] 设置监控单个目录: {glb_dir}")
        observer.schedule(event_handler, glb_dir, recursive=False)
    
    observer.start()
    print("[启动日志] 文件监控器已启动")
    print("[启动日志] 等待文件更新...")
    print("按 Ctrl+C 停止监控")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n[停止日志] 收到停止信号，正在关闭监控器...")
        observer.stop()
        print("[停止日志] 监控器已停止")
    observer.join()
    print("[停止日志] ClientC 已退出")
