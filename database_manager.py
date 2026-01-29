import sqlite3
import datetime

class PhotoDB:
    def __init__(self, db_path="photos.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """创建照片元数据表"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                capture_date TEXT,      -- 格式: YYYY-MM-DD
                description TEXT,       -- AI 生成的描述
                caption TEXT,           -- AI 生成的文案
                score_aesthetic INTEGER, -- 美观分 (0-100)
                score_memory INTEGER     -- 回忆分 (0-100)
            )
        ''')
        self.conn.commit()

    def add_mock_data(self):
        """模拟插入一些数据，方便现在调试选片逻辑"""
        today = datetime.date.today().strftime("%m-%d") # 获取月-日
        # 插入一张“历史上的今天”的照片数据
        test_data = (
            "test.jpg", 
            f"2022-{today}", 
            "一家人在海边的合影", 
            "海浪带走了沙滩的脚印，却留下了那年的笑声。", 
            85, 95
        )
        self.cursor.execute('''
            INSERT OR REPLACE INTO photos (file_path, capture_date, description, caption, score_aesthetic, score_memory)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', test_data)
        self.conn.commit()

    def get_best_photo_of_today(self):
        """核心选片逻辑：筛选出历史上的今天，并按回忆分排序"""
        today_md = datetime.date.today().strftime("-%m-%d")
        self.cursor.execute('''
            SELECT * FROM photos 
            WHERE capture_date LIKE ? 
            ORDER BY score_memory DESC LIMIT 1
        ''', (f"%{today_md}",))
        return self.cursor.fetchone()

# 调试运行
if __name__ == "__main__":
    db = PhotoDB()
    db.add_mock_data()
    print("选中的今日照片:", db.get_best_photo_of_today())
