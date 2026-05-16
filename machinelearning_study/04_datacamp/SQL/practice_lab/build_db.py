import sqlite3

# 1. 强行锁定你的本地文件路径（物理闭环）
db_path = r"D:\projects\machinelearning_study\raw_data\datacamp_study\SQL\world.db"

# 2. 物理连接数据库文件
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("正在强行在硬盘中建立表结构...")

# 3. 强行砸入創表 SQL
cursor.executescript("""
DROP TABLE IF EXISTS cities;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    code TEXT PRIMARY KEY,
    name TEXT,
    continent TEXT
);

CREATE TABLE cities (
    name TEXT,
    country_code TEXT,
    population INTEGER,
    urbanarea_pop INTEGER,
    capital TEXT
);
""")

# 4. 灌入国家与城市测试数据
countries_data = [
    ('CHN', 'China', 'Asia'),
    ('IND', 'India', 'Asia'),
    ('USA', 'United States', 'North America'),
    ('SGP', 'Singapore', 'Asia'),
    ('MCO', 'Monaco', 'Europe')
]

cities_data = [
    ('Beijing', 'CHN', 21000000, 21000000, 'Beijing'),
    ('Shanghai', 'CHN', 24000000, 24000000, ''),
    ('New Delhi', 'IND', 16000000, 16000000, 'New Delhi'),
    ('Mumbai', 'IND', 12000000, 12000000, ''),
    ('New York', 'USA', 8000000, 8000000, ''),
    ('Washington DC', 'USA', 700000, 700000, 'Washington DC'),
    ('Singapore', 'SGP', 5600000, 5600000, 'Singapore'),
    ('Monaco', 'MCO', 38000, 38000, 'Monaco')
]

cursor.executemany("INSERT INTO countries VALUES (?, ?, ?);", countries_data)
cursor.executemany("INSERT INTO cities VALUES (?, ?, ?, ?, ?);", cities_data)

# 5. 提交并锁定到硬盘，关闭通道
conn.commit()
conn.close()

print("🎉 恭喜！本地测试数据科学实验舱已被 Python 物理砸入成功！")