
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
CLIENT_A_TARGET_FILENAMES = ["capture.png", "capture2.png"]  # 监控的特定文件名列表


# 客户端B配置
CLIENT_B_SERVER_URL = 'http://localhost:5000/sync'
CLIENT_B_OUTPUT_PATH_RecycleBin = './clientB/recycle_bin'
CLIENT_B_OUTPUT_PATH_UnrecycleBin = './clientB/unrecycle_bin'
CLIENT_B_CHECK_INTERVAL = 5  # 检查间隔（秒）

# 客户端C配置
CLIENT_C_SERVER_URL = 'http://183.172.25.74:5001/upload'  # serverB的端口
CLIENT_C_CHECK_INTERVAL = 5  # 检查间隔（秒）
CLIENT_C_JSON_FILENAME = "./clientC/data.json"  # 监控的JSON文件名
CLIENT_C_GLB_FILENAME = "./clientC/model.glb"  # 监控的GLB文件名

# 服务器B配置
SERVER_B_HOST = '0.0.0.0'
SERVER_B_PORT = 5001
SERVER_B_OUTPUT_PATH_RecycleBin = os.path.abspath(os.path.join(os.path.dirname(__file__), 'serverB/recycle_bin'))
SERVER_B_OUTPUT_PATH_UnrecycleBin = os.path.abspath(os.path.join(os.path.dirname(__file__), 'serverB/recycle_bin'))
