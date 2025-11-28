import requests
import os
import json
import time

# 服务器地址
SERVER_URL = "http://localhost:5000"

def test_classify(image_path):
    """
    测试垃圾分类接口
    """
    url = f"{SERVER_URL}/test/classify"

    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(url, files=files)

    print("垃圾分类测试结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def test_comfyui(image_path):
    """
    测试ComfyUI工作流接口
    """
    url = f"{SERVER_URL}/test/comfyui"

    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(url, files=files)

    print("ComfyUI工作流测试结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def check_status():
    """
    检查测试状态
    """
    url = f"{SERVER_URL}/test/status"
    response = requests.get(url)

    print("当前状态:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def main():
    """
    主测试函数
    """
    # 创建测试图片目录（如果不存在）
    test_images_dir = "test_images"
    if not os.path.exists(test_images_dir):
        os.makedirs(test_images_dir)
        print(f"已创建测试图片目录: {test_images_dir}")
        print("请将测试图片放入该目录后重新运行测试脚本")
        return

    # 获取测试图片列表
    test_images = [f for f in os.listdir(test_images_dir) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not test_images:
        print(f"在 {test_images_dir} 目录中没有找到测试图片")
        print("请添加 .png, .jpg 或 .jpeg 格式的测试图片")
        return

    print(f"找到 {len(test_images)} 张测试图片")

    # 测试垃圾分类
    print("===== 开始测试垃圾分类 =====")
    for i, image_name in enumerate(test_images[:2]):  # 只测试前两张图片
        image_path = os.path.join(test_images_dir, image_name)
        print(f"测试图片 {i+1}: {image_name}")
        test_classify(image_path)

    # 测试ComfyUI工作流
    print("===== 开始测试ComfyUI工作流 =====")
    image_path = os.path.join(test_images_dir, test_images[0])  # 使用第一张图片测试
    print(f"使用图片: {test_images[0]}")
    test_comfyui(image_path)

    # 检查状态
    print("===== 检查工作流状态 =====")
    for _ in range(5):  # 检查5次状态
        check_status()
        time.sleep(2)  # 等待2秒

if __name__ == "__main__":
    main()
