import machine
import time
import network
import urequests

# ==========================================
# 0. 用户配置区 (请在此填写你的信息)
# ==========================================
WIFI_SSID = "ASUS"
WIFI_PASS = "19831126"

# 你的 Mac 电脑局域网 IP
SERVER_IP = "192.168.0.108" 
SERVER_PORT = "1234"

# 完整的 API 路径：这里包含了你提到的 /v1 等信息
# 最终 ESP32 会访问 http://192.168.x.x:1234/v1/chat/completions
API_ENDPOINT = "/v1/chat/completions"

# ==========================================
# 1. 对比度设置 (已固定为 260)
# ==========================================
contrast_pin = machine.Pin(25)
contrast_pwm = machine.PWM(contrast_pin, freq=10000)
contrast_pwm.duty(260) 

# ==========================================
# 2. 引脚定义与驱动逻辑
# ==========================================
RS = machine.Pin(26, machine.Pin.OUT) # 避开 GPIO 12
E  = machine.Pin(13, machine.Pin.OUT)
D4 = machine.Pin(14, machine.Pin.OUT)
D5 = machine.Pin(27, machine.Pin.OUT)
D6 = machine.Pin(33, machine.Pin.OUT)
D7 = machine.Pin(32, machine.Pin.OUT)

pins = [D4, D5, D6, D7]

def pulse_enable():
    E.off()
    time.sleep_us(1)
    E.on()
    time.sleep_us(1)
    E.off()
    time.sleep_us(100)

def send_nibble(data):
    for i in range(4):
        pins[i].value((data >> i) & 0x01)
    pulse_enable()

def send_byte(data, mode):
    RS.value(mode)
    send_nibble(data >> 4)
    send_nibble(data & 0x0F)
    time.sleep_ms(2)

def lcd_init():
    time.sleep_ms(50)
    RS.off()
    send_nibble(0x03)
    time.sleep_ms(5)
    send_nibble(0x03)
    time.sleep_us(150)
    send_nibble(0x03)
    send_nibble(0x02)
    send_byte(0x28, 0)
    send_byte(0x0C, 0)
    send_byte(0x01, 0)
    time.sleep_ms(5)

def lcd_putstr(string):
    for char in string:
        send_byte(ord(char), 1)

def show_static(line1, line2=""):
    send_byte(0x01, 0) # 清屏
    time.sleep_ms(5)
    lcd_putstr(line1[:16])
    if line2:
        send_byte(0xC0, 0)
        lcd_putstr(line2[:16])

# ==========================================
# 3. 联网功能
# ==========================================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"正在连接到 {WIFI_SSID}...")
        show_static("Connecting...", WIFI_SSID[:10])
        wlan.connect(WIFI_SSID, WIFI_PASS)
        
        attempt = 0
        while not wlan.isconnected() and attempt < 20:
            time.sleep(0.5)
            attempt += 1
            
    if wlan.isconnected():
        print("网络已连接!")
        show_static("WiFi Connected!", wlan.ifconfig()[0])
        time.sleep(2)
        return True
    else:
        show_static("Link Failed", "Check SSID/PASS")
        return False

# ==========================================
# 4. 获取 AI 内容
# ==========================================
def get_ai_caption():
    # 构造完整的请求 URL
    full_url = f"http://{SERVER_IP}:{SERVER_PORT}{API_ENDPOINT}"
    print(f"正在请求: {full_url}")
    
    payload = {
        "model": "qwen2-vl-8b", # 确保和你 LM Studio 加载的模型名一致
        "messages": [{"role": "user", "content": "One short poetic English sentence about memory."}],
        "max_tokens": 50
    }
    
    try:
        show_static("Fetching AI...", "Waiting...")
        res = urequests.post(full_url, json=payload, timeout=60)
        data = res.json()
        text = data['choices'][0]['message']['content'].strip()
        res.close()
        return text.replace("\n", " ")
    except Exception as e:
        print("API 请求失败:", e)
        return f"Err: {str(e)[:12]}"

def run_oracle():
    lcd_init()
    if connect_wifi():
        while True:
            caption = get_ai_caption()
            display_text = caption + "    "
            
            # 滚动显示 3 次
            for _ in range(3): 
                for i in range(len(display_text)):
                    window = (display_text[i:] + display_text[:i])[:16]
                    send_byte(0x80, 0)
                    lcd_putstr(window)
                    send_byte(0xC0, 0)
                    lcd_putstr("Memory Oracle   ")
                    time.sleep(0.4)
            
            show_static("Refreshing...", "")
            time.sleep(2)

# --- 启动 ---
try:
    run_oracle()
except KeyboardInterrupt:
    print("\n程序手动停止")
    contrast_pwm.deinit()