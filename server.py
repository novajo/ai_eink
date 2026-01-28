import uvicorn
from fastapi import FastAPI, Response
from PIL import Image
import io
import os

app = FastAPI()

# 模拟：一张存放在服务器上的图片
# 你可以在当前目录下放一个名为 "test.jpg" 的图片
TEST_IMAGE_PATH = "test.jpg"

@app.get("/")
def read_root():
    return {"status": "InkTime Server is running"}

@app.get("/get_image")
async def get_image():
    """
    提供给 ESP32 下载的接口。
    目前先简单返回原始图片，后续我们将在这里集成 Dithering (抖动) 算法。
    """
    if not os.path.exists(TEST_IMAGE_PATH):
        # 如果没有 test.jpg，我们创建一个灰色的占位图
        img = Image.new('RGB', (800, 480), color = (73, 109, 137))
        d = io.BytesIO()
        img.save(d, format="JPEG")
        return Response(content=d.getvalue(), media_type="image/jpeg")
    
    with open(TEST_IMAGE_PATH, "rb") as f:
        image_data = f.read()
    
    print("ESP32 来取图了！发送字节数:", len(image_data))
    return Response(content=image_data, media_type="image/jpeg")

if __name__ == "__main__":
    # 启动服务器。注意：ESP32 访问时需要使用你电脑的局域网 IP (如 192.168.x.x)
    uvicorn.run(app, host="0.0.0.0", port=8000)
