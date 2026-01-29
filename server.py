import uvicorn
from fastapi import FastAPI, Response
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
from database_manager import PhotoDB

app = FastAPI()
db = PhotoDB()

# 配置区
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FONT_PATH = "simhei.ttf" # 你需要准备一个中文字体文件在同级目录

def create_layout(image_path, caption, date_str):
    """
    排版引擎：将照片、文案、日期合成为一张墨水屏海报
    """
    # 1. 创建画布
    canvas = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    # 2. 处理照片 (留出白边，类似拍立得效果)
    photo = Image.open(image_path).convert('RGB')
    photo.thumbnail((700, 350)) # 缩放照片
    photo_x = (SCREEN_WIDTH - photo.width) // 2
    photo_y = 30
    canvas.paste(photo, (photo_x, photo_y))
    
    # 3. 绘制文字 (日期和文案)
    try:
        font_main = ImageFont.truetype(FONT_PATH, 24)
        font_date = ImageFont.truetype(FONT_PATH, 18)
    except:
        font_main = ImageFont.load_default()
        font_date = ImageFont.load_default()

    # 绘制文案
    text_w = draw.textlength(caption, font=font_main)
    draw.text(((SCREEN_WIDTH - text_w) // 2, 400), caption, fill=(0, 0, 0), font=font_main)
    
    # 绘制日期
    draw.text((650, 440), date_str, fill=(255, 0, 0), font=font_date) # 红色日期

    return canvas

def apply_4color_dithering(img):
    """应用抖动算法 (直接对 Image 对象处理)"""
    palette_data = [0,0,0, 255,255,255, 255,0,0, 255,255,0] + [0]*756
    palette_img = Image.new('P', (1, 1))
    palette_img.putpalette(palette_data)
    
    dithered = img.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)
    return dithered.convert('RGB')

@app.get("/get_image")
async def get_image():
    # 1. 从数据库选片
    record = db.get_best_photo_of_today()
    
    if record:
        img_path, date_str, caption = record[1], record[2], record[4]
    else:
        # 默认占位
        img_path, date_str, caption = "test.jpg", "Today", "今天没有发现值得回忆的瞬间。"

    # 2. 排版
    final_img = create_layout(img_path, caption, date_str)
    
    # 3. 抖动算法处理
    final_img = apply_4color_dithering(final_img)

    # 4. 返回
    buf = io.BytesIO()
    final_img.save(buf, format="JPEG", quality=85)
    return Response(content=buf.getvalue(), media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
