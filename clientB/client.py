
import os
import sys
import time
import requests
from datetime import datetime

# 导入配置文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CLIENT_B_SERVER_URL as SERVER_URL, CLIENT_B_OUTPUT_PATH_RecycleBin as RECYCLE_PATH, CLIENT_B_OUTPUT_PATH_UnrecycleBin as UNRECYCLE_PATH, CLIENT_B_CHECK_INTERVAL as CHECK_INTERVAL

# 确保输出目录存在
os.makedirs(RECYCLE_PATH, exist_ok=True)
os.makedirs(UNRECYCLE_PATH, exist_ok=True)

def sync_with_server():
    """
    与服务器同步，获取新文件
    """
    try:
        response = requests.get(SERVER_URL)

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')

            # 检查返回的是文件还是JSON状态
            if 'application/json' in content_type:
                result = response.json()
                print(f"服务器状态: {result['status']}")
                if result['status'] == 'no_update':
                    print("没有新文件")
                elif result['status'] == 'processing':
                    print("工作流仍在处理中")
            else:
                # 返回的是文件，保存文件
                # 从响应头获取原始文件名，如果没有则使用默认命名
                content_disposition = response.headers.get('content-disposition', '')
                if content_disposition and 'filename=' in content_disposition:
                    # 提取文件名
                    original_filename = content_disposition.split('filename=')[1].strip('"')
                    # 获取不带后缀的文件名
                    base_name = os.path.splitext(original_filename)[0]
                else:
                    # 如果没有获取到文件名，使用默认命名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_name = f"output_{timestamp}"
                
                # 根据文件名后缀决定保存路径
                if "_recycle" in base_name.lower():
                    output_path = RECYCLE_PATH
                    # 移除后缀，使用干净的文件名
                    clean_name = base_name.replace("_recycle", "")
                elif "_unrecycle" in base_name.lower():
                    output_path = UNRECYCLE_PATH
                    # 移除后缀，使用干净的文件名
                    clean_name = base_name.replace("_unrecycle", "")
                else:
                    # 如果没有特定后缀，默认保存到回收站文件夹
                    output_path = RECYCLE_PATH
                    clean_name = base_name
                
                # 添加时间戳确保文件名唯一
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{clean_name}_{timestamp}.png"
                filepath = os.path.join(output_path, filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"已下载新文件: {filepath}")
        else:
            print(f"同步失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"同步过程中出错: {e}")

if __name__ == "__main__":
    print(f"开始同步，服务器地址: {SERVER_URL}")
    print(f"回收站文件保存路径: {RECYCLE_PATH}")
    print(f"非回收站文件保存路径: {UNRECYCLE_PATH}")
    print(f"检查间隔: {CHECK_INTERVAL}秒")

    try:
        while True:
            sync_with_server()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("停止同步")
