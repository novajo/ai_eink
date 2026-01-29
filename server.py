import uvicorn
from fastapi import FastAPI, Response
from PIL import Image
import io
import os
import numpy as np

app = FastAPI()

# 配置区
TEST_IMAGE_PATH = "test.jpg"
# 假设你的墨水屏是 7.3 寸，分辨率通常是 800x480
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

def apply_4color_dithering(image_path):
    """
    将图片转换为黑、白、红、黄四色，并应用抖动算法
    """
    # 1. 打开并调整大小（按比例裁剪填充）
    img = Image.open(image_path).convert('RGB')
    img = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.Resampling.LANCZOS)

    # 2. 定义墨水屏的 4 色调色板 (黑, 白, 红, 黄)
    # 每个颜色由 RGB 三个分量组成
    palette_data = [
        0,   0,   0,    # 黑
        255, 255, 255,  # 白
        255, 0,   0,    # 红
        255, 255, 0,    # 黄
    ]
    # 填充调色板到 256 种颜色（Pillow 要求的格式）
    palette_data += [0] * (768 - len(palette_data))
    
    # 创建一个调色板图像容器
    palette_img = Image.new('P', (1, 1))
    palette_img.putpalette(palette_data)

    # 3. 核心步骤：量化并应用 Floyd-Steinberg 抖动
    # dither=Image.FLOYDSTEINBERG 会自动处理误差扩散
    dithered_img = img.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)
    
    # 4. 转回 RGB 以便预览或以 JPG/PNG 格式发送给 ESP32
    return dithered_img.convert('RGB')

@app.get("/")
def read_root():
    return {"status": "InkTime Dithering Server is running"}

@app.get("/get_image")
async def get_image():
    """
    ESP32 调用此接口获取处理后的图片
    """
    if not os.path.exists(TEST_IMAGE_PATH):
        # 兜底：如果没有图片，返回一个黄色背景
        img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), color=(255, 255, 0))
    else:
        print(f"正在处理图片: {TEST_IMAGE_PATH} ...")
        img = apply_4color_dithering(TEST_IMAGE_PATH)

    # 将处理后的图片存入内存
    buf = io.BytesIO()
    # 为了让 ESP32 容易解析，我们先传 BMP 格式（无损且结构简单）
    # 或者为了节省流量传 JPEG
    img.save(buf, format="JPEG", quality=85)
    byte_data = buf.getvalue()
    
    print(f"处理完成！发送四色抖动图，大小: {len(byte_data)} 字节")
    return Response(content=byte_data, media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
