# SpaceTrashServer 测试指南

本文档介绍如何使用SpaceTrashServer的测试功能，包括测试垃圾分类和ComfyUI工作流。

## 测试接口

服务器已添加以下测试接口：

### 1. 垃圾分类测试接口
- **URL**: `/test/classify`
- **方法**: POST
- **参数**: 
  - `image`: 图片文件
- **功能**: 测试垃圾分类功能，返回图片中的物品及其分类结果

### 2. ComfyUI工作流测试接口
- **URL**: `/test/comfyui`
- **方法**: POST
- **参数**: 
  - `image`: 图片文件
- **功能**: 测试ComfyUI工作流处理图片的功能

### 3. 测试状态查询接口
- **URL**: `/test/status`
- **方法**: GET
- **功能**: 查询当前工作流状态和未发送文件列表

## 使用测试脚本

我们提供了一个简单的测试脚本 `test_client.py`，用于测试上述接口。

### 准备工作

1. 在项目根目录下创建 `test_images` 文件夹
2. 将测试图片放入该文件夹中（支持PNG、JPG、JPEG格式）

### 运行测试

确保服务器已启动后，运行以下命令：

```bash
python test_client.py
```

测试脚本将执行以下操作：
1. 检查 `test_images` 目录中是否有测试图片
2. 使用前两张图片测试垃圾分类功能
3. 使用第一张图片测试ComfyUI工作流
4. 多次查询工作流状态，直到完成或超时

## 手动测试

您也可以使用Postman、curl或其他HTTP客户端工具手动测试这些接口。

### 示例：使用curl测试垃圾分类

```bash
curl -X POST -F "image=@test_images/sample.jpg" http://localhost:5000/test/classify
```

### 示例：使用curl测试ComfyUI工作流

```bash
curl -X POST -F "image=@test_images/sample.jpg" http://localhost:5000/test/comfyui
```

### 示例：使用curl查询状态

```bash
curl http://localhost:5000/test/status
```

## 注意事项

1. 测试前请确保服务器已正确配置并启动
2. 确保ComfyUI服务正在运行且可访问
3. 确保OpenAI API密钥已正确配置
4. 测试图片应包含明显的垃圾物品，以便于分类识别

## 测试结果解读

### 垃圾分类测试结果

```json
{
  "filename": "test_1234567890.png",
  "classification": "recyclable",
  "message": "测试完成"
}
```

- `filename`: 保存的测试文件名
- `classification`: 分类结果（"recyclable"或"non-recyclable"）
- `message`: 测试状态信息

### ComfyUI工作流测试结果

```json
{
  "message": "ComfyUI工作流已启动",
  "filename": "test_comfyui_1234567890.png",
  "status": "processing"
}
```

- `message`: 状态信息
- `filename`: 保存的测试文件名
- `status`: 工作流状态（"processing"表示正在处理）

### 状态查询结果

```json
{
  "workflow_running": false,
  "unsent_files_count": 1,
  "unsent_files": [
    "output/1234567890_recycle.png"
  ],
  "result_file": "output/1234567890_recycle.png"
}
```

- `workflow_running`: 工作流是否正在运行
- `unsent_files_count`: 未发送文件数量
- `unsent_files`: 未发送文件列表
- `result_file`: 最新结果文件路径（如果有）
