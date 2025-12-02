
import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify

# 导入配置文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SERVER_B_HOST, 
    SERVER_B_PORT, 
    SERVER_B_OUTPUT_PATH_RecycleBin, 
    SERVER_B_OUTPUT_PATH_UnrecycleBin
)

app = Flask(__name__)

# 确保目录存在
os.makedirs(SERVER_B_OUTPUT_PATH_RecycleBin, exist_ok=True)
os.makedirs(SERVER_B_OUTPUT_PATH_UnrecycleBin, exist_ok=True)

def parse_json_and_save(glb_file, json_file):
    """
    解析JSON文件内容，识别某个字段，然后给GLB文件修改命名后保存在两个文件夹下
    """
    try:
        # 获取文件名，判断类型
        glb_filename = glb_file.filename
        print(f"[服务器日志] 接收到GLB文件名: {glb_filename}")
        
        # 从文件名中提取类型
        if '_recycle.glb' in glb_filename:
            file_type = 'recycle'
            output_path = SERVER_B_OUTPUT_PATH_RecycleBin
            print(f"[服务器日志] 从文件名识别类型: 可回收垃圾")
        elif '_unrecycle.glb' in glb_filename:
            file_type = 'unrecycle'
            output_path = SERVER_B_OUTPUT_PATH_UnrecycleBin
            print(f"[服务器日志] 从文件名识别类型: 不可回收垃圾")
        elif '_harmful.glb' in glb_filename:
            file_type = 'harmful'
            output_path = SERVER_B_OUTPUT_PATH_UnrecycleBin  # 有害垃圾也放在非回收站文件夹
            print(f"[服务器日志] 从文件名识别类型: 有害垃圾")
        else:
            # 无法从文件名识别类型，尝试从JSON内容识别
            print(f"[服务器日志] 无法从文件名识别类型，尝试从JSON内容识别")
            
            # 读取JSON内容
            json_content = json_file.read().decode('utf-8')
            json_data = json.loads(json_content)
            
            # 打印JSON内容以便调试
            print(f"[服务器日志] 接收到JSON数据: {json_data}")
            
            # 检查JSON数据格式
            if not isinstance(json_data, list) or len(json_data) == 0:
                print(f"[服务器日志] JSON数据格式不正确，使用默认类型")
                file_type = 'unrecycle'
                output_path = SERVER_B_OUTPUT_PATH_UnrecycleBin
            else:
                # 获取第一个元素
                item = json_data[0]
                if 'output' not in item or 'tag' not in item['output'] or 'harmfulness' not in item['output']:
                    print(f"[服务器日志] JSON数据缺少必要字段，使用默认类型")
                    file_type = 'unrecycle'
                    output_path = SERVER_B_OUTPUT_PATH_UnrecycleBin
                else:
                    tags = item['output']['tag']
                    harmfulness = item['output']['harmfulness']
                    
                    print(f"[服务器日志] 标签: {tags}")
                    print(f"[服务器日志] 危害性: {harmfulness}")
                    
                    # 判断类型
                    if 'Harmful' in harmfulness:
                        file_type = 'harmful'
                        output_path = SERVER_B_OUTPUT_PATH_UnrecycleBin
                        print(f"[服务器日志] 从JSON内容识别类型: 有害垃圾")
                    elif 'Recyclable' in tags and 'Non-recyclable' not in tags:
                        file_type = 'recycle'
                        output_path = SERVER_B_OUTPUT_PATH_RecycleBin
                        print(f"[服务器日志] 从JSON内容识别类型: 可回收垃圾")
                    else:
                        file_type = 'unrecycle'
                        output_path = SERVER_B_OUTPUT_PATH_UnrecycleBin
                        print(f"[服务器日志] 从JSON内容识别类型: 不可回收垃圾")
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 根据类型决定文件名
        if file_type == 'recycle':
            filename = f"model_{timestamp}_recycle.glb"
        elif file_type == 'harmful':
            filename = f"model_{timestamp}_harmful.glb"
        else:  # unrecycle
            filename = f"model_{timestamp}_unrecycle.glb"
        
        # 保存文件
        filepath = os.path.join(output_path, filename)
        
        # 如果之前已经读取了JSON内容，需要重置文件指针
        if 'json_content' in locals():
            glb_file.seek(0)
        
        with open(filepath, 'wb') as f:
            f.write(glb_file.read())
        
        print(f"[服务器日志] 已保存GLB文件: {filepath}")
        return {
            "success": True,
            "message": f"文件已保存到{output_path}",
            "filepath": filepath,
            "type": file_type
        }
    except Exception as e:
        print(f"[服务器日志] 处理文件时出错: {e}")
        import traceback
        print(f"[服务器日志] 详细错误信息:\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/upload', methods=['POST'])
def upload_files():
    """
    接收客户端C上传的GLB和JSON文件
    """
    # 检查是否有文件上传
    if 'glb' not in request.files or 'json' not in request.files:
        return jsonify({"error": "缺少GLB文件或JSON文件"}), 400

    glb_file = request.files['glb']
    json_file = request.files['json']

    # 检查文件名是否为空
    if glb_file.filename == '' or json_file.filename == '':
        return jsonify({"error": "文件名不能为空"}), 400

    # 处理文件
    result = parse_json_and_save(glb_file, json_file)

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/status', methods=['GET'])
def status():
    """
    获取服务器状态
    """
    status_info = {
        "server": "ServerB",
        "status": "running",
        "recycle_bin_path": SERVER_B_OUTPUT_PATH_RecycleBin,
        "unrecycle_bin_path": SERVER_B_OUTPUT_PATH_UnrecycleBin,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return jsonify(status_info), 200

if __name__ == '__main__':
    print(f"服务器B启动，监听地址: {SERVER_B_HOST}:{SERVER_B_PORT}")
    print(f"回收站文件保存路径: {SERVER_B_OUTPUT_PATH_RecycleBin}")
    print(f"非回收站文件保存路径: {SERVER_B_OUTPUT_PATH_UnrecycleBin}")
    app.run(host=SERVER_B_HOST, port=SERVER_B_PORT)
