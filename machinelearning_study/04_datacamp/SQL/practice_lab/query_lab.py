import sqlite3
import pandas as pd

# 1. 链接物理路径
db_path = r"C:\projects\machinelearning_study\raw_data\datacamp\SQL\world.db"
conn = sqlite3.connect(db_path)

# ==================== 轨道一：SQL 端精准猎杀 ====================
sql_query = """
SELECT DISTINCT co.code,MIN(la.lang_name) AS representative_lang
FROM languages AS la
INNER JOIN countries AS co
ON la.country_code = co.code
GROUP BY co.code;
"""
sql_result = pd.read_sql_query(sql_query, conn)
print(f"打印国家语言表")
print(sql_result)                    # 打印前10行看看是谁

print("\n" + "="*60 + "\n")

# ==================== 轨道二：Pandas 端内存清洗 ====================
df_languages = pd.read_sql_query("SELECT * FROM languages;", conn)
df_countries = pd.read_sql_query("SELECT * FROM countries;", conn)

# 1. 物理合并
df_pandas_merged = pd.merge(
    df_languages,                             
    df_countries,                                
    left_on='country_code', 
    right_on='code', 
    how='inner',
).drop('country_code', axis=1)

df_pandas_merged_cleaned = df_pandas_merged.drop_duplicates(subset=['code'])
print(df_pandas_merged_cleaned)



# 关闭物理连接
conn.close()