import sqlite3
import pandas as pd

# 1. 锁定你刚才灌好数据的硬盘文件
db_path = r"D:\projects\machinelearning_study\raw_data\datacamp_study\SQL\world.db"
conn = sqlite3.connect(db_path)

# ========================================================
# 2. 【你的 SQL 练习区】把你的 SQL 代码丢进下面这个三引号里
# ========================================================
sql_query = """
SELECT country_code,AVG(population) AS avg_pop
FROM cities
GROUP BY country_code
HAVING AVG(population) > 10000000
ORDER BY avg_pop DESC;
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