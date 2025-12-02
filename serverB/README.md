# ServerB 使用说明

ServerB 是一个接收和处理GLB模型文件的服务器，它会接收来自ClientC的GLB文件和JSON文件，并根据JSON文件中的"type"字段决定如何处理GLB文件。

## 启动方法

1. 确保已安装Flask：
   ```
   pip install flask
   ```

2. 启动ServerB：
   ```
   cd serverB
   python app.py
   ```

3. 服务器将在5001端口启动（可在config.py中修改）

## API接口

### POST /upload

接收GLB和JSON文件，并根据JSON内容处理GLB文件。

请求参数：
- glb: GLB模型文件
- json: JSON描述文件

响应：
- 成功：返回处理结果和文件路径
- 失败：返回错误信息

### GET /status

获取服务器状态信息。

响应：
- 服务器状态
- 文件保存路径
- 当前时间戳

## 文件处理逻辑

1. 解析JSON文件中的"type"字段
2. 根据"type"字段的值：
   - 如果为"recyclable"，将GLB文件保存到回收站文件夹，文件名格式为"model_时间戳_recycle.glb"
   - 如果为"non-recyclable"或"nonrecyclable"，将GLB文件保存到非回收站文件夹，文件名格式为"model_时间戳_unrecycle.glb"
   - 如果为其他值或不存在，将GLB文件同时保存到两个文件夹，分别添加"_recycle"和"_unrecycle"后缀

## 配置说明

所有配置都在项目根目录的config.py文件中，可以修改以下参数：

- SERVER_B_HOST: 服务器监听地址
- SERVER_B_PORT: 服务器监听端口
- SERVER_B_OUTPUT_PATH_RecycleBin: 回收站文件保存路径
- SERVER_B_OUTPUT_PATH_UnrecycleBin: 非回收站文件保存路径
