import os
import sys
import io
import base64
import json
import time
import requests
import threading
import shutil
from flask import Flask, request, jsonify, send_file
from PIL import Image

# 导入配置文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

app = Flask(__name__)

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 全局变量，用于跟踪工作流状态和未发送的文件
workflow_status = {"running": False, "result": None}
unsent_files = []  # 记录还未发送给客户端的文件列表

def process_comfyui_output():
    """
    处理ComfyUI的输出文件
    """
    try:
        # 检查ComfyUI默认输出路径是否存在文件
        if os.path.exists(COMFYUI_OUTPUT_PATH):
            # 生成带时间戳的新文件名
            timestamp = int(time.time())
            filename = f"output_{timestamp}.png"
            output_path = os.path.join(OUTPUT_FOLDER, filename)

            # 复制文件到输出目录
            shutil.copy2(COMFYUI_OUTPUT_PATH, output_path)

            # 判断垃圾分类
            is_recyclable = classify_image(output_path)

            # 根据垃圾分类结果添加后缀
            if is_recyclable:
                final_filename = f"output_{timestamp}_recycle.png"
            else:
                final_filename = f"output_{timestamp}_unrecycle.png"

            final_path = os.path.join(OUTPUT_FOLDER, final_filename)

            # 重命名文件
            os.rename(output_path, final_path)

            print(f"处理完成，垃圾分类结果: {'可回收' if is_recyclable else '不可回收'}")
            # 将文件添加到未发送列表
            unsent_files.append(final_path)
            return final_path
    except Exception as e:
        print(f"处理ComfyUI输出文件出错: {e}")

    return None

def trigger_comfyui_workflow(image_path):
    """
    触发ComfyUI工作流
    """
    # 这里应该是ComfyUI的工作流配置
    # 具体配置取决于你的ComfyUI工作流
    workflow = {
        "1": {
            "inputs": {
                "image": image_path,
                # 其他工作流参数
            },
            "class_type": "LoadImage",
        },
        # 其他工作流节点...
    }

    try:
        response = requests.post(COMFYUI_API_URL, json={"prompt": workflow})
        if response.status_code == 200:
            prompt_id = response.json().get("prompt_id")
            # 等待工作流完成
            while True:
                history_response = requests.get(f"{COMFYUI_HISTORY_URL}/{prompt_id}")
                if history_response.status_code == 200:
                    history = history_response.json()
                    if prompt_id in history:
                        # 工作流完成，处理ComfyUI的输出文件
                        result_path = process_comfyui_output()
                        if result_path:
                            workflow_status["result"] = result_path
                            break
                        else:
                            # 如果处理失败，尝试从API获取输出
                            outputs = history[prompt_id].get("outputs")
                            if outputs:
                                # 处理输出文件
                                for node_id, node_output in outputs.items():
                                    for image_data in node_output.get("images", []):
                                        output_filename = image_data.get("filename")
                                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                                        # 下载文件到输出目录
                                        file_response = requests.get(f"{COMFYUI_VIEW_URL}?filename={output_filename}")
                                        if file_response.status_code == 200:
                                            with open(output_path, "wb") as f:
                                                f.write(file_response.content)
                                        workflow_status["result"] = output_path
                                        # 将文件添加到未发送列表
                                        unsent_files.append(output_path)
                                        break
                            break
                time.sleep(1)  # 每秒检查一次
    except Exception as e:
        print(f"触发ComfyUI工作流出错: {e}")
    finally:
        workflow_status["running"] = False

def classify_image(image_path):
    """
    使用OpenAI API对图片进行垃圾分类判断
    """
    # 打印
    print(f"正在处理图片: {image_path}")
    try:
        # 读取图片
        with open(image_path, "rb") as f:
            image_data = f.read()

        # 转换为base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # 调用OpenAI API进行垃圾分类判断
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        # 使用n8n导出的垃圾分类prompt
        system_message = """## 角色 (Role)
You are a recycling police, your duty is to identify the rubbish that the user had just through, and is the rubbish a non-recyclable or a recyclable object. 

Follow the structured output format and output the result."""

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请识别图片中的物品，并判断它是可回收还是不可回收的垃圾。请按照以下JSON格式输出：{\n\t\"object\": \"What is the rubbish?\",\n\t\"tag\": [\"recyclable \", \"nonrecyclable\"]\n}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 200,
            "response_format": {"type": "json_object"}
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            try:
                # 尝试解析JSON响应
                json_result = json.loads(content)
                tag = json_result.get("tag", [])
                # 判断是否可回收
                is_recyclable = "recyclable" in str(tag).lower()
                print(f"垃圾分类结果: {json_result.get('object', '未知物品')} - {'可回收' if is_recyclable else '不可回收'}")
                return is_recyclable
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试简单文本判断
                is_recyclable = "recyclable" in content.lower()
                print(f"垃圾分类结果(文本解析): {'可回收' if is_recyclable else '不可回收'}")
                return is_recyclable
        else:
            print(f"OpenAI API请求失败，状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print(f"垃圾分类判断出错: {e}")
        # 默认返回不可回收
        return False

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    接收客户端A上传的图片
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 保存上传的图片
        filename = f"upload_{int(time.time())}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 直接触发ComfyUI工作流
        workflow_status["running"] = True
        workflow_status["result"] = None
        threading.Thread(target=trigger_comfyui_workflow, args=(filepath,)).start()

        return jsonify({"message": "Image uploaded successfully", "workflow_started": True}), 200

@app.route('/sync', methods=['GET'])
def sync():
    """
    客户端B同步请求
    """
    global unsent_files

    # 检查是否有未发送的文件
    if unsent_files:
        # 获取第一个未发送的文件
        file_path = unsent_files.pop(0)

        # 检查文件是否仍然存在
        if os.path.exists(file_path):
            # 获取原始文件名
            original_filename = os.path.basename(file_path)

            # 根据文件路径决定文件名后缀
            if "recycle" in file_path.lower():
                filename_with_suffix = f"{os.path.splitext(original_filename)[0]}_recycle.png"
            elif "unrecycle" in file_path.lower():
                filename_with_suffix = f"{os.path.splitext(original_filename)[0]}_unrecycle.png"
            else:
                # 如果没有特定标识，默认使用_unrecycle后缀
                filename_with_suffix = f"{os.path.splitext(original_filename)[0]}_unrecycle.png"

            # 返回文件，并设置文件名
            return send_file(file_path, as_attachment=True, download_name=filename_with_suffix)
        else:
            # 文件不存在，继续检查下一个
            return sync()

    # 检查工作流是否仍在运行
    if workflow_status["running"]:
        return jsonify({"status": "processing", "message": "Workflow is still running"}), 200

    # 没有新文件
    return jsonify({"status": "no_update", "message": "No new files available"}), 200

@app.route('/test/classify', methods=['POST'])
def test_classify():
    """
    测试垃圾分类接口
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 保存上传的图片
        filename = f"test_{int(time.time())}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 使用垃圾分类函数进行测试
        is_recyclable = classify_image(filepath)

        # 返回测试结果
        result = {
            "filename": filename,
            "classification": "recyclable" if is_recyclable else "non-recyclable",
            "message": "测试完成"
        }
        return jsonify(result), 200

@app.route('/test/comfyui', methods=['POST'])
def test_comfyui():
    """
    测试ComfyUI工作流接口
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 保存上传的图片
        filename = f"test_comfyui_{int(time.time())}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 触发ComfyUI工作流
        workflow_status["running"] = True
        workflow_status["result"] = None
        threading.Thread(target=trigger_comfyui_workflow, args=(filepath,)).start()

        return jsonify({
            "message": "ComfyUI工作流已启动",
            "filename": filename,
            "status": "processing"
        }), 200

@app.route('/test/status', methods=['GET'])
def test_status():
    """
    获取测试状态接口
    """
    status = {
        "workflow_running": workflow_status["running"],
        "unsent_files_count": len(unsent_files),
        "unsent_files": unsent_files
    }

    if workflow_status["result"]:
        status["result_file"] = workflow_status["result"]

    return jsonify(status), 200

if __name__ == '__main__':
    app.run(host=SERVER_HOST, port=SERVER_PORT)
