import sqlite3
import pandas as pd

# 1. 锁定你刚才灌好数据的硬盘文件
db_path = r"D:\projects\machinelearning_study\raw_data\datacamp_study\SQL\world.db"
conn = sqlite3.connect(db_path)

# ========================================================
# 2. 【你的 SQL 练习区】把你的 SQL 代码丢进下面这个三引号里
# ========================================================

sql_query = """
SELECT main_c.name,main_c.country_code,main_c.population
FROM cities AS main_c
WHERE main_c.population > (
SELECT AVG(population)
FROM cities
WHERE country_code = main_c.country_code 
-- 限制子查询计算的人口平均值为外层城市(main_c)所在国家的人口平均值，如果不限制，计算出来的人口平均值就是全球人口平均值
)

"""
# ========================================================

# 3. 用 Pandas 把数据捞出来并打印成漂亮的表格
try:
    df = pd.read_sql_query(sql_query, conn)
    print("\n📊 【查询结果】:")
    print(df.to_string(index=False)) # 不打印行索引，保持最干净的 SQL 形状
except Exception as e:
    print(f"\n❌ 【SQL 语法报错】: {e}")

conn.close()