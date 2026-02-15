import base64
import requests
import json
import time

# --- 配置区 ---
API_URL = "http://localhost:1234/v1/chat/completions"
IMAGE_PATH = "test.jpg" 

def encode_image(image_path):
    """将图片转换为 base64 编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def simulate_1602_scroll(text):
    """
    模拟 1602A 屏幕的水平滚动效果
    屏幕只有 16 位，多出的部分会平滑滚过
    """
    print("\n[1602A 屏幕滚动预览 - 模拟真机节奏]")
    print("+----------------+")
    
    # 1602A 只有 16 列。如果文本短，直接显示
    if len(text) <= 16:
        print(f"|{text:<16}|")
        print(f"|{' ' * 16}|") # 第二行为空
        print("+----------------+")
    else:
        # 模拟滚动：循环平移字符串
        # 为了让显示更自然，我们在末尾加几个空格，防止首尾相连太紧
        display_text = text + "    " 
        try:
            print("预览滚动中 (按 Ctrl+C 停止预览)...")
            # 模拟滚动 2 圈
            for _ in range(2):
                for i in range(len(display_text)):
                    window = (display_text[i:] + display_text[:i])[:16]
                    # 我们固定显示在第一行，第二行可以显示日期或固定文案
                    # \r 表示回到行首，不换行
                    print(f"\r|{window}|", end="")
                    time.sleep(0.3) # 模拟真实屏幕滚动的速度
            print("\r|测试预览结束    |")
        except KeyboardInterrupt:
            print("\n停止预览")
    print("+----------------+")

def test_qwen_vl():
    print(f"正在读取并编码图片: {IMAGE_PATH}...")
    try:
        base64_image = encode_image(IMAGE_PATH)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {IMAGE_PATH}，请确保图片放在同一目录下。")
        return

    # 构造请求载荷
    payload = {
        "model": "qwen2-vl-8b", 
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a memory curator for a tiny 16x2 character display. "
                    "Analyze the image and provide a poetic English caption. "
                    "CRITICAL RULES: "
                    "1. LENGTH LIMIT: 16 to 60 characters. Not too long. " # 适度放宽
                    "2. NO PUNCTUATION (no dots, no commas). "
                    "3. NO CHINESE. "
                    "4. Use vivid but simple words."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this memory in a short sentence for a scrolling 1602 LCD."},
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
        "max_tokens": 100
    }

    print("正在发送请求到 LM Studio (模型正在处理图片推理)...")
    try:
        # 增加超时以应对本地推理
        response = requests.post(API_URL, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        caption = result['choices'][0]['message']['content'].strip()
        
        # 清洗文本：移除引号和多余空格
        caption = caption.replace('"', '').replace("'", "").strip()
        
        print("\n" + "="*40)
        print(f"AI 生成结果: {caption}")
        print(f"字符长度: {len(caption)}")
        
        # 运行滚动模拟
        simulate_1602_scroll(caption)
        print("="*40)
            
    except Exception as e:
        print(f"\n请求失败！详细错误信息: {e}")

if __name__ == "__main__":
    test_qwen_vl()
