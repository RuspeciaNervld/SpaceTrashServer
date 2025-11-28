# Space Trash Python 服务器

## 简介

服务器是一个为 Space Trash 设计的 Python 服务器，部署于comfy ui服务器，用于trigger comfy ui的工作流以及将工作流生成的文件发送给客户端。

## 项目结构

```
SpaceTrashServer/
├── README.md
├── requirements.txt
├── config.py          # 全局配置文件
├── server/
│   └── app.py         # 服务器端代码
├── clientA/
│   └── client.py      # 客户端A代码
└── clientB/
    └── client.py      # 客户端B代码
```

## 流程

1. 客户端A监控特定文件名的文件变化，当目标文件更新时，将其发送给服务器。
2. 服务器接收客户端A发来的图片，将图片发送给OpenAI的API，将API返回的图片放入指定路径，然后trigger ComfyUI的工作流。
3. 在工作流执行完后，客户端B发送的同步请求才被处理（否则返回，无更新），然后服务器将工作流新生成的文件发送给客户端B。
4. 客户端B反复向服务器发送同步请求，如果服务器有新的文件，则返回给客户端B，否则返回无更新。

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

服务器需要OpenAI API密钥，可以通过环境变量设置：

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

或者在Windows上：

```cmd
set OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 启动服务

#### 启动服务器

```bash
cd server
python app.py
```

服务器将在 http://localhost:5000 上运行。

#### 启动客户端A

```bash
cd clientA
python client.py
```

客户端A将监控 `./clientA/images` 目录下的特定文件（默认为 `target_image.png`），当该文件更新时上传到服务器。您可以通过修改配置文件中的 `CLIENT_A_WATCH_PATH` 和 `CLIENT_A_TARGET_FILENAME` 变量来更改监控路径和目标文件名。

#### 启动客户端B

```bash
cd clientB
python client.py
```

客户端B将定期向服务器发送同步请求，并根据文件名后缀将下载的文件保存到不同目录：
- 包含 `_recycle` 后缀的文件将保存到 `./clientB/outputs` 目录
- 包含 `_unrecycle` 后缀的文件将保存到 `./clientB/outputs_unrecycle` 目录

您可以通过修改配置文件中的 `CLIENT_B_OUTPUT_PATH_RecycleBin` 和 `CLIENT_B_OUTPUT_PATH_UnrecycleBin` 变量来更改下载路径。

## 注意事项

1. 确保ComfyUI服务器在 http://127.0.0.1:8188 上运行。
2. 服务器代码中的ComfyUI工作流配置可能需要根据您的实际工作流进行调整。
3. 确保OpenAI API密钥有效且有足够的配额。

## 配置文件

项目使用 `config.py` 作为全局配置文件，统一管理所有关键配置。您可以通过修改此文件来自定义项目行为，而无需修改各个组件的代码。

主要配置项包括：

- 服务器配置：主机地址、端口
- API配置：OpenAI API地址和密钥、ComfyUI API地址
- 文件路径配置：上传文件夹、输出文件夹
- 客户端A配置：监控路径、服务器地址、检查间隔
- 客户端B配置：服务器地址、回收站文件下载路径、非回收站文件下载路径、检查间隔

## 自定义配置

您可以通过修改 `config.py` 文件来自定义项目行为。所有组件都会从此文件读取配置，确保配置的一致性。如果您需要针对特定环境使用不同的配置，可以创建多个配置文件（如 `config_dev.py`, `config_prod.py`），并在导入时指定使用哪个配置文件。
