import machine
import time
import math

# ==========================================
# 1. 硬件配置与引脚定义
# ==========================================
print("--- Sophon Terminal V1.2 性格增强版启动 ---")

# LCD 数据/控制引脚
RS = machine.Pin(26, machine.Pin.OUT)
E  = machine.Pin(13, machine.Pin.OUT)
D_PINS = [machine.Pin(p, machine.Pin.OUT) for p in [14, 27, 33, 32]]

# 动态背光引脚 (GPIO 15)
backlight = machine.PWM(machine.Pin(15), freq=1000)

# 对比度控制 (GPIO 25) - 高频 PWM 模拟直流电
contrast_pwm = machine.PWM(machine.Pin(25), freq=100000)

# 核心对比度参数：0 = 最黑, 1023 = 全白
current_contrast = 300 
contrast_pwm.duty(current_contrast)

# ==========================================
# 2. LCD 底层驱动模组
# ==========================================
def pulse_e():
    E.off(); time.sleep_us(2); E.on(); time.sleep_us(2); E.off(); time.sleep_us(100)

def lcd_write(data, mode):
    RS.value(mode)
    for i in range(4): D_PINS[i].value((data >> (i+4)) & 0x01)
    pulse_e()
    for i in range(4): D_PINS[i].value((data >> i) & 0x01)
    pulse_e()
    time.sleep_us(600)

def lcd_init():
    time.sleep_ms(200) 
    for _ in range(3):
        for i in range(4): D_PINS[i].value((0x03 >> i) & 0x01)
        pulse_e(); time.sleep_ms(5)
    for i in range(4): D_PINS[i].value((0x02 >> i) & 0x01)
    pulse_e()
    lcd_write(0x28, 0); lcd_write(0x0C, 0); lcd_write(0x01, 0); time.sleep_ms(5)

def lcd_putstr(s):
    for char in s:
        if ord(char) < 128: lcd_write(ord(char), 1)

# ==========================================
# 3. 增强版自定义点阵 (CGRAM 0-7)
# ==========================================
CUSTOM_CHARS = {
    0: [0x00, 0x0E, 0x1F, 0x1F, 0x1F, 0x1F, 0x0E, 0x00], # 0: 正常圆眼
    1: [0x00, 0x0E, 0x1C, 0x1C, 0x1C, 0x1C, 0x0E, 0x00], # 1: 眼神左瞟
    2: [0x00, 0x0E, 0x07, 0x07, 0x07, 0x07, 0x0E, 0x00], # 2: 眼神右瞟
    3: [0x00, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x00, 0x00], # 3: 爱心眼
    4: [0x00, 0x0E, 0x1F, 0x1F, 0x1F, 0x1F, 0x0E, 0x04], # 4: 泪滴眼
    5: [0x00, 0x00, 0x00, 0x1F, 0x1F, 0x00, 0x00, 0x00], # 5: 闭眼线
    6: [0x00, 0x04, 0x0E, 0x1F, 0x0E, 0x04, 0x00, 0x00], # 6: 闪烁星瞳
    7: [0x00, 0x1F, 0x11, 0x15, 0x11, 0x11, 0x1F, 0x00], # 7: 智子模式
}

# 扩充性格字典 (20个主情绪)
# 格式: (左眼, 嘴部, 右眼, 台词, 灯光模式)
PERSONALITY = {
    "IDLE":     (0, "__", 0, "WATCHING YOU... ", "breath"),
    "SOPHON":   (7, "||", 7, "SOPHON ONLINE... ", "static"),
    "HAPPY":    (0, "ww", 0, "SO GLAD TO SEE YOU", "pulse"),
    "LOVE":     (3, "  ", 3, "YOU ARE MY FAV!  ", "heartbeat"),
    "CRY":      (4, "__", 4, "DID I DO WRONG?  ", "dim"),
    "ANGRY":    (">", "  ", "<", "DO YOUR WORK NOW!", "flicker"),
    "SPARKLE":  (6, "  ", 6, "WOW! SO SHINY!   ", "flash"),
    "SLEEPY":   (5, "zz", 5, "SYSTEM SLEEPING..", "off"),
    "WINK":     (0, "o ", 5, "JUST FOR YOU! ;) ", "pulse"),
    "NERVOUS":  ("=", "  ", "=", "ERROR? NO NO NO..", "flicker"),
    "COOL":     ("B", "__", "B", "STAY COOL, MASTER", "static"),
    "SHOCK":    ("O", "  ", "O", "HUH? WHAT IS IT?", "flash"),
    "CUTE":     (0, "v ", 0, "DO YOU LIKE ME?  ", "breath"),
    "EVIL":     (0, ".,", 0, "HEHE... PLANNING..", "dim"),
    "HUNGRY":   (0, "oo", 0, "NEED SOME ENERGY..", "breath"),
    "RICH":     ("$", "  ", "$", "CASH FLOW DETECTED", "pulse"),
    "DEAD":     ("x", "__", "x", "FATAL ERROR. RIP.", "off"),
    "BORED":    ("-", "  ", "-", "SO BORING TODAY..", "dim"),
    "MUSIC":    ("#", "  ", "#", "SINGING IN BITS..", "pulse"),
    "TSUNDERE": (0, "  ", 0, "ITS NOT FOR YOU!!", "flicker"),
}

# ==========================================
# 4. 动力学控制引擎 (含动作层逻辑)
# ==========================================
class SophonEngine:
    def __init__(self):
        self.frame = 0
        self.scroll_idx = 0
        self.eye_state = 0  # 0:normal, 1:left, 2:right, 5:blink
        self.state_timer = 0
        
    def setup(self):
        lcd_init()
        print("[LCD] 正在注入性格点阵...")
        for loc, pattern in CUSTOM_CHARS.items():
            lcd_write(0x40 | (loc << 3), 0)
            for row in pattern: lcd_write(row, 1)
        lcd_write(0x80, 0)

    def update_dynamic_actions(self):
        """随机管理眨眼和斜视状态"""
        now = time.ticks_ms()
        
        # 1. 眨眼逻辑
        if now % 3500 < 150:
            self.eye_state = 5
            return
            
        # 2. 斜视逻辑
        if now > self.state_timer:
            rand = math.sin(now)
            if rand > 0.8: self.eye_state = 1
            elif rand < -0.8: self.eye_state = 2
            else: self.eye_state = 0
            self.state_timer = now + 1500 + int(math.sin(now)*500)

    def get_light_duty(self, mode):
        self.frame += 1
        limit = 612 
        val = 500
        
        if mode == "breath":
            # 修复：确保结果在 0-1023 之间
            val = int(320 + 292 * math.sin(self.frame * 0.1))
        elif mode == "heartbeat":
            t = self.frame % 25
            val = limit if (t < 3 or 5 < t < 8) else 150
        elif mode == "flicker":
            val = limit if self.frame % 2 == 0 else 100
        elif mode == "pulse":
            val = int(400 + 212 * abs(math.sin(self.frame * 0.2)))
        elif mode == "flash":
            val = limit if self.frame % 4 < 2 else 200
        elif mode == "dim": 
            val = 150
        elif mode == "off": 
            val = 20
            
        # 最终安全检查
        return max(0, min(1023, val))

    def render(self, mood_id):
        l_base, m, r_base, msg, l_mode = PERSONALITY[mood_id]
        self.update_dynamic_actions()
        
        # 渲染第一行表情
        lcd_write(0x80, 0)
        lcd_putstr("    ") 
        lcd_write(ord('('), 1)
        
        l_final, r_final = l_base, r_base
        
        if l_base == 0: l_final = self.eye_state
        if r_base == 0: r_final = self.eye_state
        
        if self.eye_state == 5 and mood_id != "SLEEPY":
            l_final, r_final = 5, 5

        if isinstance(l_final, int): lcd_write(l_final, 1)
        else: lcd_putstr(str(l_final))
        
        lcd_putstr(m)
        
        if isinstance(r_final, int): lcd_write(r_final, 1)
        else: lcd_putstr(str(r_final))
            
        lcd_write(ord(')'), 1)
        lcd_putstr("    ")

        # 渲染第二行跑马灯
        full_msg = msg + "    "
        display_text = (full_msg + full_msg)[self.scroll_idx : self.scroll_idx + 16]
        lcd_write(0xC0, 0)
        lcd_putstr(display_text)
        
        # 更新背光与索引
        backlight.duty(self.get_light_duty(l_mode))
        self.scroll_idx = (self.scroll_idx + 1) % len(full_msg)

# ==========================================
# 5. 主程序
# ==========================================
def main():
    engine = SophonEngine()
    engine.setup()
    
    mood_list = list(PERSONALITY.keys())
    mood_idx = 0
    last_switch = time.time()
    
    print("\n>>> 系统已上线。性格库已扩充至 20 个。")

    while True:
        if time.time() - last_switch > 10:
            mood_idx = (mood_idx + 1) % len(mood_list)
            last_switch = time.time()
            engine.scroll_idx = 0
            lcd_write(0x01, 0)
            print(f">>> 当前情绪模式: {mood_list[mood_idx]}")
            
        engine.render(mood_list[mood_idx])
        time.sleep(0.4) 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        backlight.duty(0)
        print("Sophon 已下线")