import os
import sqlite3

# 1. 锁死你的绝对路径
DB_PATH = r"C:\projects\machinelearning_study\raw_data\datacamp\SQL\world.db"

# 2. 自动检查并创建多层文件夹，防止因为文件夹不存在而报错
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)
    print(f"📁 已自动创建目标文件夹: {db_dir}")

# 3. 连接数据库（如果文件已存在，会直接覆盖重建表）
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 4. 安全清空旧表
cursor.execute("DROP TABLE IF EXISTS cities;")
cursor.execute("DROP TABLE IF EXISTS countries;")
cursor.execute("DROP TABLE IF EXISTS languages;")

# 5. 建立标准的表结构
cursor.execute(
    """
CREATE TABLE countries (
    code TEXT PRIMARY KEY,
    name TEXT,
    continent TEXT
);
"""
)

cursor.execute(
    """
CREATE TABLE cities (
    name TEXT,
    country_code TEXT,
    population INTEGER,
    urbanarea_pop INTEGER,
    capital TEXT
);
"""
)

cursor.execute(
    """
CREATE TABLE languages (
    id INTEGER PRIMARY KEY,
    country_code TEXT,
    lang_name TEXT
);
"""
)

# 6. 灌入包含“5大经典陷阱”的真实业务脏数据
countries_data = [
    ("CHN", "China", "Asia"),
    ("IND", "India", "Asia"),
    ("USA", "United States", "North America"),
    ("SGP", "Singapore", "Asia"),
    ("MCO", "Monaco", "Europe"),
    ("ATL", "Atlantis", None),  # 陷阱1：没有大洲的神秘国家
    ("WKD", "Wakanda", None),  # 陷阱2：完全没有城市和语言登记的国家
]

cities_data = [
    ("Beijing", "CHN", 21000000, 21000000, "Beijing"),
    ("Shanghai", "CHN", 24000000, 24000000, None),
    ("New Delhi", "IND", 16000000, 16000000, "New Delhi"),
    ("Mumbai", "IND", 12000000, 12000000, None),
    ("New York", "USA", 8000000, 8000000, None),
    ("Washington DC", "USA", 700000, 700000, "Washington DC"),
    ("Singapore", "SGP", 5600000, 5600000, "Singapore"),
    ("Monaco", "MCO", 38000, 38000, "Monaco"),
    ("Gotham", "XYZ", 10000000, 10000000, None),  # 陷阱3：孤儿城市，XYZ国家根本不存在
]

languages_data = [
    (1, "CHN", "Mandarin"),
    (2, "CHN", "Cantonese"),
    (3, "CHN", "Tibetan"),
    (4, "IND", "Hindi"),
    (5, "IND", "English"),
    (6, "IND", "Bengali"),
    (7, "USA", "English"),
    (8, "USA", "Spanish"),
    (9, "SGP", "English"),
    (10, "SGP", "Malay"),
    (11, "SGP", "Mandarin"),
    (12, "SGP", "Tamil"),
    (13, "MCO", "French"),
    (14, "MCO", "French"),  # 陷阱4：完全重复的语言录入记录
    (15, "atl", "Atlantian"),  # 陷阱5：小写的 'atl'，考验关联时的不规范输入
]

cursor.executemany("INSERT INTO countries VALUES (?, ?, ?);", countries_data)
cursor.executemany("INSERT INTO cities VALUES (?, ?, ?, ?, ?);", cities_data)
cursor.executemany("INSERT INTO languages VALUES (?, ?, ?);", languages_data)

conn.commit()
conn.close()

print(f"🔥 完美闭环！数据库已成功创建并在该绝对路径锁死:\n📍 {DB_PATH}")
print("所有的脏数据和多对多炸弹已经埋好，随时可以开炮。")