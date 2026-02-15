import base64
import requests
import json

# --- 配置区 ---
# LM Studio 默认本地地址
API_URL = "http://localhost:1234/v1/chat/completions"
# 你要测试的照片路径
IMAGE_PATH = "test.jpg" 

def encode_image(image_path):
    """将图片转换为 base64 编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_qwen_vl():
    print(f"正在读取并编码图片: {IMAGE_PATH}...")
    try:
        base64_image = encode_image(IMAGE_PATH)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {IMAGE_PATH}，请确保图片放在同一目录下。")
        return

    # 构造请求载荷 (OpenAI 兼容格式)
    payload = {
        "model": "qwen2-vl-8b", 
        "messages": [
            {
                "role": "system",
                "content": "You are a memory curator. Analyze images and provide a poetic English caption. "
                           "Strictly limit to 16-30 characters. No punctuation. No Chinese."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this memory in one short sentence."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100 # 稍微增加 max_tokens 防止 AI 没说完就断了
    }

    print("正在发送请求到 LM Studio (本地图片处理可能需要 1-2 分钟，请耐心等待)...")
    try:
        # 将 timeout 显著增加到 300 秒，以适配本地视觉模型的推理速度
        response = requests.post(API_URL, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        caption = result['choices'][0]['message']['content'].strip()
        
        print("\n" + "="*30)
        print(f"AI 生成的英文金句: \n>>> {caption} <<<")
        print(f"字符长度: {len(caption)}")
        print("="*30)
        
        if len(caption) > 32:
            print("注意: 长度超过 32 字符，1602A 屏幕需要滚动显示。")
        elif len(caption) == 0:
            print("提示: AI 返回内容为空。请检查 LM Studio 里的模型是否加载正确，或尝试重启 Server。")
            
    except requests.exceptions.Timeout:
        print("\n[ERROR] 请求超时！即便设置了 300 秒模型仍未响应，请检查 GPU 显存是否溢出。")
    except Exception as e:
        print(f"\n请求失败！详细错误信息: {e}")

if __name__ == "__main__":
    test_qwen_vl()