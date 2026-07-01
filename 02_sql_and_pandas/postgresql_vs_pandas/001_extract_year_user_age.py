"""
课程章节: Chapter 1.2 - Date/Time Functions
核心函数: EXTRACT() vs .dt.component
业务场景: 提取用户注册年份，计算精准账期
"""
import duckdb
import pandas as pd
import numpy as np

# =====================================================================
# 📦 1. 原始靶场投料 (Raw Data Input)
# =====================================================================
raw_df = pd.DataFrame({
    'user_id': [1, 2, 3],
    'signup_time': ['2026-01-15 08:00:00', '2026-03-20 12:30:00', '2026-06-01 18:45:00']
})

# =====================================================================
# ⚔️ 2. 轨道一：PostgreSQL 纯内存轰炸 (DuckDB)
# =====================================================================

sql_query = """
SELECT user_id,
       signup_time::TIMESTAMP AS signup_time,
       EXTRACT(YEAR FROM signup_time::TIMESTAMP)::INTEGER AS signup_year
FROM raw_df;
"""
df_sql_res = duckdb.query(sql_query).df()

# =====================================================================
# 🐼 3. 轨道二：Pandas 刚性平替对账 (Pandas Vectorization)
# =====================================================================
# 提示：在这里用 Pandas 的向量化算子物理还原上面的 SQL 逻辑
df_pd_res = raw_df.copy()
df_pd_res['signup_time'] = pd.to_datetime(df_pd_res['signup_time'])
df_pd_res['signup_year'] = df_pd_res['signup_time'].dt.year

# =====================================================================
# 🚨 4. 终极断言对账大闸 (刚性防御)
# =====================================================================
# 利用 Pandas 官方的测试工具，强制断言两个轨道的计算结果（包括数据类型）必须 100% 完全对齐
try:
    pd.testing.assert_frame_equal(
        df_sql_res.reset_index(drop=True), 
        df_pd_res.reset_index(drop=True),
        check_dtype=False # 允许整型细微差异(int32/int64)，但数值必须严格相等
    )
    print("✅【对账全绿通过】PostgreSQL 与 Pandas 在数据矩阵上完美会师！")
except AssertionError as e:
    print(f"❌【🚨 发现账目断层】双轨计算结果发生物理偏离:\n{e}")