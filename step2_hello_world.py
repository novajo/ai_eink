import machine
import time

# ==========================================
# 1. 对比度软件调节 (从 DAC 切换为 PWM 模式)
# 理由：PWM 在低占空比下比 DAC 更接近真正的 GND (0V)
# ==========================================
contrast_pin = machine.Pin(25)
# 设置频率为 10kHz，这样人眼和液晶感应不到闪烁
contrast_pwm = machine.PWM(contrast_pin, freq=10000)

# ==========================================
# 2. 引脚定义与驱动逻辑
# ==========================================
RS = machine.Pin(26, machine.Pin.OUT)
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
    send_byte(0x28, 0) # 4位模式
    send_byte(0x0C, 0) # 显示开，光标关
    send_byte(0x01, 0) # 清屏
    time.sleep_ms(5)

def lcd_putstr(string):
    for char in string:
        send_byte(ord(char), 1)

# ==========================================
# 3. PWM 对比度扫描 (寻找正面看最清晰的点)
# ==========================================
def find_best_contrast_pwm():
    print("\n--- 切换至 PWM 对比度扫描模式 ---")
    lcd_init()
    send_byte(0x80, 0)
    lcd_putstr("PWM Tuning...")
    
    # ESP32 PWM 占空比范围是 0 - 1023
    # 0 代表最黑 (接近 GND)，1023 代表最白 (3.3V)
    # 既然你之前接 GND 太黑，接 DAC 0 又太白，
    # 那么最佳值一定在 PWM 0 到 300 之间。
    for duty in range(0, 400, 10):
        print(f"当前 PWM 占空比 (Duty): {duty}")
        contrast_pwm.duty(duty)
        
        send_byte(0xC0, 0) # 移动到第二行
        lcd_putstr(f"Duty Value: {duty}  ")
        
        time.sleep(0.6)

try:
    find_best_contrast_pwm()
    
    # 演示一段文字
    # 如果你发现 120 效果最好，扫描结束后可以手动执行 contrast_pwm.duty(120)
    
except KeyboardInterrupt:
    print("停止")
    # 保持在 0，也就是你之前能看到字的 GND 状态
    contrast_pwm.duty(0)