# 文本列数据清洗（白名单 / 黑名单过滤）

## 🧹 基础预处理

```python
df['col'] = df['col'].str.strip().str.lower()
```

* 去除首尾空格
* 统一大小写（避免匹配误差）

---

## ⚔️ 一级防御：数据结构优化（In-Memory）

### ❌ 常见误区：使用 List

```python
valid_list = ['A', 'B', 'C', ...]
mask = df['account_status'].isin(valid_list)
```

* 底层为线性查找
* 时间复杂度：O(M × N)
* 大数据量下性能差

---

### ✅ 推荐做法：使用 Set

```python
valid_set = set(['A', 'B', 'C', ...])
mask = df['account_status'].isin(valid_set)
```

* 基于哈希表
* 平均时间复杂度：O(1)
* 总体复杂度：O(M)

> 注意：
>
> * 极端情况下可能退化（哈希冲突）
> * Pandas 对 `isin` 已有优化，set 通常更快但不是绝对

---

## 📥 白名单加载方式

### 1️⃣ 本地文件加载（Offline）

```python
import pandas as pd

df_whitelist = pd.read_csv('dict/global_whitelist.csv')
valid_set = set(df_whitelist['valid_id'])
```

特点：

* 稳定
* 易维护（业务侧可修改）

---

### 2️⃣ 数据库加载（Database）

```python
import sqlite3

conn = sqlite3.connect('risk_db.sqlite')

query = "SELECT active_status_name FROM dim_status_whitelist"
df_whitelist = pd.read_sql(query, conn)

conn.close()

valid_set = set(df_whitelist['active_status_name'])
```

特点：

* 支持动态更新
* 适合中等规模

---

### 3️⃣ API 获取（微服务）

```python
import requests

response = requests.get('http://internal-api/whitelist')
whitelist_data = response.json()

valid_set = set(whitelist_data)
```

特点：

* 解耦数据来源
* 常见于大型系统

---

## ⚔️ 二级防御：计算下推（SQL）

当白名单无法放入内存时：

### ❌ 错误方式

* 拉入 Pandas 再过滤

---

### ✅ 正确方式：数据库 JOIN

```sql
SELECT a.*
FROM fact_table a
INNER JOIN dim_whitelist b
ON a.status = b.status
```

或：

```sql
SELECT *
FROM fact_table a
WHERE EXISTS (
  SELECT 1
  FROM dim_whitelist b
  WHERE a.status = b.status
)
```

优势：

* 利用数据库索引（B+ 树）
* 避免内存瓶颈
* 适合大规模数据

---

## 🚀 进阶方向

### 3️⃣ 布隆过滤器（Bloom Filter）

* 内存占用极低
* 特性：

  * 不存在 → 100% 准确
  * 存在 → 可能误判

用途：

* 作为第一层过滤
* 减少后续计算压力

---

### 4️⃣ 分布式广播（Spark Broadcast）

* 用于分布式计算（如 Spark）

机制：

* 将白名单广播到各节点
* 每个节点本地过滤

优势：

* 避免网络通信开销
* 提升并行效率

---

## 🧠 核心原则

1. 控制时间复杂度
   O(M × N) → O(M)

2. 控制数据位置
   内存 / 数据库 / 分布式

3. 控制数据流动
   少搬数据，多就地计算

---

## 🔧 实战优化技巧

### ✅ 使用 merge（替代 isin）

```python
df = df.merge(df_whitelist, how='inner', on='status')
```

---

### ✅ 使用 category 类型

```python
df['status'] = df['status'].astype('category')
```

* 降低内存
* 提升匹配效率

---

### ✅ 去重

```python
df_whitelist = df_whitelist.drop_duplicates()
```

避免重复计算
