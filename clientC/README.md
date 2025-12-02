# ClientC 使用说明

ClientC 是一个文件监控客户端，它会监控两个文件：
1. data.json - 包含模型信息的JSON文件
2. model.glb - 3D模型文件

当这两个文件都更新时，ClientC会将GLB文件和JSON文件一起发送给ServerB。

## 启动方法

1. 首先启动ServerB：
   ```
   cd serverB
   python app.py
   ```

2. 然后启动ClientC：
   ```
   cd clientC
   python client.py
   ```

## 工作流程

1. ClientC监控指定目录下的data.json和model.glb文件
2. 当两个文件都更新时，ClientC会将它们一起发送给ServerB
3. ServerB解析JSON文件中的"type"字段
4. 根据"type"字段的值，ServerB会：
   - 如果为"recyclable"，将GLB文件保存到回收站文件夹
   - 如果为"non-recyclable"或"nonrecyclable"，将GLB文件保存到非回收站文件夹
   - 如果为其他值或不存在，将GLB文件同时保存到两个文件夹
5. 保存的文件名会包含时间戳和类型标识

## 配置说明

所有配置都在项目根目录的config.py文件中，可以修改以下参数：

- CLIENT_C_WATCH_PATH: ClientC监控的目录路径
- CLIENT_C_SERVER_URL: ServerB的URL地址
- CLIENT_C_CHECK_INTERVAL: 文件检查间隔（秒）
- CLIENT_C_JSON_FILENAME: 监控的JSON文件名
- CLIENT_C_GLB_FILENAME: 监控的GLB文件名
