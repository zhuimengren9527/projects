# import sqlite3

# # 1. 强行锁定你的本地文件路径（物理闭环）
# db_path = r"C:\projects\machinelearning_study\raw_data\datacamp\SQL\world.db"

# # 2. 物理连接数据库文件
# conn = sqlite3.connect(db_path)
# cursor = conn.cursor()

# print("正在强行在硬盘中建立表结构...")

# # 3. 强行砸入創表 SQL
# cursor.executescript("""
# DROP TABLE IF EXISTS cities;
# DROP TABLE IF EXISTS countries;

# CREATE TABLE countries (
#     code TEXT PRIMARY KEY,
#     name TEXT,
#     continent TEXT
# );

# CREATE TABLE cities (
#     name TEXT,
#     country_code TEXT,
#     population INTEGER,
#     urbanarea_pop INTEGER,
#     capital TEXT
# );
# """)

# # 4. 灌入国家与城市测试数据
# countries_data = [
#     ('CHN', 'China', 'Asia'),
#     ('IND', 'India', 'Asia'),
#     ('USA', 'United States', 'North America'),
#     ('SGP', 'Singapore', 'Asia'),
#     ('MCO', 'Monaco', 'Europe')
# ]

# cities_data = [
#     ('Beijing', 'CHN', 21000000, 21000000, 'Beijing'),
#     ('Shanghai', 'CHN', 24000000, 24000000, ''),
#     ('New Delhi', 'IND', 16000000, 16000000, 'New Delhi'),
#     ('Mumbai', 'IND', 12000000, 12000000, ''),
#     ('New York', 'USA', 8000000, 8000000, ''),
#     ('Washington DC', 'USA', 700000, 700000, 'Washington DC'),
#     ('Singapore', 'SGP', 5600000, 5600000, 'Singapore'),
#     ('Monaco', 'MCO', 38000, 38000, 'Monaco')
# ]

# cursor.executemany("INSERT INTO countries VALUES (?, ?, ?);", countries_data)
# cursor.executemany("INSERT INTO cities VALUES (?, ?, ?, ?, ?);", cities_data)

# # 5. 提交并锁定到硬盘，关闭通道
# conn.commit()
# conn.close()

# print("🎉 恭喜！本地测试数据科学实验舱已被 Python 物理砸入成功！")






import sqlite3

db_path = r"C:\projects\machinelearning_study\raw_data\datacamp\SQL\world.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("开始在硬盘上锻造 languages 表...")

# 1. 物理建表
cursor.execute("""
CREATE TABLE IF NOT EXISTS languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code TEXT,
    lang_name TEXT
);
""")

# 2. 清理历史遗留（保证每次运行结果一致）
cursor.execute("DELETE FROM languages;")

# 3. 投毒：精准制造 1对多 的关联基数
mock_languages_sql = """
INSERT INTO languages (country_code, lang_name) 
VALUES 
    ('CHN', 'Mandarin'), ('CHN', 'Cantonese'), ('CHN', 'Tibetan'),  -- 中国：3行
    ('IND', 'Hindi'), ('IND', 'English'), ('IND', 'Bengali'),       -- 印度：3行
    ('USA', 'English'), ('USA', 'Spanish'),                         -- 美国：2行
    ('SGP', 'English'), ('SGP', 'Malay'), ('SGP', 'Mandarin'), ('SGP', 'Tamil'), -- 新加坡：4行
    ('MCO', 'French');                                              -- 摩纳哥：1行
    -- 注意：我们故意没给 ATL, WKD, LIL 这三个孤岛国家分配语言
"""

cursor.execute(mock_languages_sql)
conn.commit() # 必须落盘！

# 验证资产
cursor.execute("SELECT COUNT(*) FROM languages;")
total_langs = cursor.fetchone()[0]
print(f"投毒完成！ languages 表现已存在，共包含 {total_langs} 行极其危险的一对多记录。")

conn.close()