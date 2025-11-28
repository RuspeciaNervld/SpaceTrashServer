
import os

# 服务器配置
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000

# OpenAI API配置
OPENAI_API_URL = "https://api.openai.com/v1/images/edits"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key_here")

# ComfyUI配置
COMFYUI_API_URL = "http://127.0.0.1:8188/prompt"
COMFYUI_HISTORY_URL = "http://127.0.0.1:8188/history"
COMFYUI_VIEW_URL = "http://127.0.0.1:8188/view"
COMFYUI_OUTPUT_PATH = "./comfyui/outputs/temp.glb"

# 文件路径配置
UPLOAD_FOLDER = './server/uploads'
OUTPUT_FOLDER = './server/outputs'

# 客户端A配置
CLIENT_A_WATCH_PATH = './clientA/images'
CLIENT_A_SERVER_URL = 'http://localhost:5000/upload'
CLIENT_A_CHECK_INTERVAL = 5  # 检查间隔（秒）
CLIENT_A_TARGET_FILENAME = "capture.png"  # 监控的特定文件名

# 客户端B配置
CLIENT_B_SERVER_URL = 'http://localhost:5000/sync'
CLIENT_B_OUTPUT_PATH_RecycleBin = './clientB/recycle_bin'
CLIENT_B_OUTPUT_PATH_UnrecycleBin = './clientB/unrecycle_bin'
CLIENT_B_CHECK_INTERVAL = 5  # 检查间隔（秒）
