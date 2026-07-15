# 05_join_and_subquery

## 章节名称

Join and Subquery

中文理解：

> 多表关联与子查询

---

## 一、章节目标

本章主要学习在数据分散于多张表时，如何通过关联关系把数据组合起来，再进行分析。

前面几个 Pattern 大多是在一张表内部完成分析，例如：

```text
Gap & Island：连续区间
Ranking：分组排名
Cumulative Analysis：累计统计
Time Comparison：前后时间比较
```

而本章开始处理真实业务中更常见的问题：

```text
一张表存业务明细；
另一张表存基础信息；
需要先关联，再分析。
```

例如：

```text
设备日志表 + 设备信息表
订单表 + 用户表
销售表 + 商品表
故障记录表 + 设备台账表
```

---

## 二、核心知识点

本章主要包括：

```text
1. INNER JOIN / LEFT JOIN
2. Join 后聚合分析
3. EXISTS / NOT EXISTS
4. 子查询
5. 多表分析中的数据质量问题
```

---

## 三、当前练习目录

```text
05_join_and_subquery/
├── 01_basic_join_device_info.ipynb
├── 02_multi_table_analysis.ipynb
├── 03_exists_and_not_exists.ipynb
└── README.md
```

---

## 四、SQL / Pandas 基本对应关系

| 目的 | SQL | Pandas |
|---|---|---|
| 内连接 | `INNER JOIN` | `merge(..., how='inner')` |
| 左连接 | `LEFT JOIN` | `merge(..., how='left')` |
| 按单字段关联 | `ON a.id = b.id` | `on='id'` |
| 按多字段关联 | `ON a.id=b.id AND a.date=b.date` | `on=['id', 'date']` |
| Join 后聚合 | `JOIN + GROUP BY` | `merge + groupby + agg` |
| 找左表有、右表没有 | `LEFT JOIN + WHERE right.id IS NULL` | `merge(..., indicator=True)` |

---

# 01_basic_join_device_info

## 题型名称

Basic Join Device Info

中文理解：

> 设备日志表与设备信息表基础关联

---

## 题型目标

学习 `INNER JOIN` 和 `LEFT JOIN` 的区别。

核心问题是：

```text
两张表按 device_id 关联时，
哪些记录会被保留？
哪些记录会被删除？
匹配不到的字段会如何显示？
```

---

## 核心记忆

```text
INNER JOIN：
只保留两张表都能匹配上的记录。
看交集。

LEFT JOIN：
保留左表所有记录。
右表匹配不上时，右表字段为 NULL / NaN。
```

---

# 02_multi_table_analysis

## 题型名称

Multi Table Analysis

中文理解：

> 多表关联后的聚合分析

---

## 题型目标

学习先关联多张表，再按维度字段做统计分析。

核心流程是：

```text
日志明细表
↓
INNER JOIN 设备信息表
↓
得到 site、device_type、model 等维度字段
↓
GROUP BY 维度字段
↓
计算 SUM / COUNT / AVG 等指标
```

---

## Task 1：按站点统计总报警次数

### 题目目标

统计每个站点的总报警次数。

输出字段：

```text
site
total_alarm_count
```

要求：

```text
只统计能够匹配到设备信息的日志记录。
无法匹配到 site 的日志记录不要计入统计。
```

### SQL 解法

```sql
WITH join_table AS (
    SELECT
        dv.site,
        lo.alarm_count
    FROM df_log AS lo
    INNER JOIN df_device AS dv
        ON lo.device_id = dv.device_id
)

SELECT
    site,
    SUM(alarm_count)::INTEGER AS total_alarm_count
FROM join_table
GROUP BY site
ORDER BY site;
```

### Pandas 解法

```python
df_pd = (
    df_log
    .merge(
        df_device,
        how='inner',
        on='device_id'
    )
    .groupby('site', as_index=False)
    .agg(
        total_alarm_count=('alarm_count', 'sum')
    )
    .sort_values(by='site')
    .reset_index(drop=True)
)

df_pd
```

---

## Task 2：按 site + device_type 做综合统计

### 题目目标

按站点和设备类型做综合统计。

输出字段：

```text
site
device_type
total_alarm_count
error_days
avg_alarm_count
```

要求：

```text
只统计能够匹配到设备信息的日志记录。

按 site 和 device_type 两个字段分组。

total_alarm_count：
该站点、该设备类型的总报警次数。

error_days：
该站点、该设备类型下 status = 'ERROR' 的记录数。

avg_alarm_count：
该站点、该设备类型的平均每日报警次数，保留 2 位小数。
```

### SQL 解法

```sql
WITH merge_table AS (
    SELECT
        lo.device_id,
        lo.stat_date,
        lo.status,
        lo.alarm_count,
        dv.site,
        dv.device_type
    FROM df_log AS lo
    INNER JOIN df_device AS dv
        ON lo.device_id = dv.device_id
)

SELECT 
    site,
    device_type,
    SUM(alarm_count)::INTEGER AS total_alarm_count,
    SUM(
        CASE
            WHEN status = 'ERROR' THEN 1
            ELSE 0
        END
    )::INTEGER AS error_days,
    ROUND(AVG(alarm_count), 2) AS avg_alarm_count
FROM merge_table
GROUP BY site, device_type
ORDER BY site, device_type;
```

### Pandas 解法

```python
df_pd = (
    df_log
    .merge(
        df_device,
        how='inner',
        on='device_id'
    )
    .assign(
        is_error=lambda x: x['status'] == 'ERROR'
    )
    .groupby(['site', 'device_type'], as_index=False)
    .agg(
        total_alarm_count=('alarm_count', 'sum'),
        error_days=('is_error', 'sum'),
        avg_alarm_count=('alarm_count', 'mean')
    )
    .assign(
        avg_alarm_count=lambda x: x['avg_alarm_count'].round(2)
    )
    .sort_values(by=['site', 'device_type'])
    .reset_index(drop=True)
)

df_pd
```

---

## Pandas 重点：groupby(..., as_index=False)

Pandas 的 `groupby()` 默认是：

```python
as_index=True
```

也就是说，分组字段会变成索引。

例如：

```python
df.groupby('site').agg(
    total_alarm_count=('alarm_count', 'sum')
)
```

结果中 `site` 会变成索引，不是普通列。

如果写成：

```python
df.groupby('site', as_index=False).agg(
    total_alarm_count=('alarm_count', 'sum')
)
```

那么 `site` 会保留为普通列。

这通常更接近 SQL 的输出形式：

```sql
SELECT
    site,
    SUM(alarm_count) AS total_alarm_count
FROM table
GROUP BY site;
```

记忆：

```text
as_index=False
=
分组字段不要变成索引，保留为普通列。
```

它基本等价于：

```python
.groupby(...).agg(...).reset_index()
```

当前阶段建议默认使用：

```python
.groupby(..., as_index=False)
```

这样后续排序、筛选、merge、导出都会更方便。

---

## 条件计数注意点

SQL 中不要写：

```sql
COUNT(status = 'ERROR')
```

原因是：

```text
COUNT(expression) 统计的是 expression 非 NULL 的行数，
不是统计 TRUE 的行数。
```

正确写法：

```sql
SUM(
    CASE
        WHEN status = 'ERROR' THEN 1
        ELSE 0
    END
) AS error_days
```

Pandas 中可以先构造布尔列：

```python
.assign(
    is_error=lambda x: x['status'] == 'ERROR'
)
```

然后：

```python
error_days=('is_error', 'sum')
```

因为 Pandas 中：

```text
True = 1
False = 0
```

---

# 03_exists_and_not_exists

## Task 1：找出日志表中有、设备信息表中没有的设备日志

### 题目目标

找出：

```text
df_log 中存在，
但 df_device 中不存在的 device_id。
```

输出字段：

```text
device_id
stat_date
status
alarm_count
```

业务要求：

```text
只输出无法匹配到设备信息的日志记录。
```

根据当前数据，应该能找出设备 `E` 的日志记录。

---

### Pattern 分类

本题属于：

```text
EXISTS / NOT EXISTS
存在性判断
反关联查询
```

本质问题是：

```text
左表有，右表没有。
```

也就是：

```text
df_log 有这个 device_id，
但 df_device 没有这个 device_id。
```

---

## SQL 解法一：LEFT JOIN + 右表 key IS NULL

### SQL 代码

```sql
WITH compare_table AS (
    SELECT
        lo.device_id AS log_device_id,
        lo.stat_date,
        lo.status,
        lo.alarm_count,
        dv.device_id AS dv_device_id
    FROM df_log AS lo
    LEFT JOIN df_device AS dv
        ON lo.device_id = dv.device_id
)

SELECT
    log_device_id AS device_id,
    stat_date,
    status,
    alarm_count
FROM compare_table
WHERE dv_device_id IS NULL
ORDER BY device_id, stat_date;
```

也可以写成更简洁的形式：

```sql
SELECT
    lo.device_id,
    lo.stat_date,
    lo.status,
    lo.alarm_count
FROM df_log AS lo
LEFT JOIN df_device AS dv
    ON lo.device_id = dv.device_id
WHERE dv.device_id IS NULL
ORDER BY lo.device_id, lo.stat_date;
```

---

### 逻辑说明

```sql
FROM df_log AS lo
LEFT JOIN df_device AS dv
    ON lo.device_id = dv.device_id
```

含义是：

```text
保留 df_log 中的所有日志记录。
如果 df_device 中找不到对应 device_id，
右表字段会变成 NULL。
```

然后：

```sql
WHERE dv.device_id IS NULL
```

表示：

```text
只保留右表没有匹配成功的记录。
```

所以这个模式可以记成：

```text
LEFT JOIN + 右表 key IS NULL
=
找左表有、右表没有。
```

---

## SQL 解法二：NOT EXISTS

### SQL 代码

```sql
SELECT
    lo.device_id,
    lo.stat_date,
    lo.status,
    lo.alarm_count
FROM df_log AS lo
WHERE NOT EXISTS (
    SELECT
        1
    FROM df_device AS dv
    WHERE dv.device_id = lo.device_id
)
ORDER BY lo.device_id, lo.stat_date;
```

---

### 逻辑说明

```sql
WHERE NOT EXISTS (
    SELECT
        1
    FROM df_device AS dv
    WHERE dv.device_id = lo.device_id
)
```

可以理解成：

```text
对 df_log 当前这一行 lo，
去 df_device 中查找有没有相同 device_id 的记录。

如果找得到：
EXISTS 为 TRUE，
NOT EXISTS 为 FALSE，
这一行不要。

如果找不到：
EXISTS 为 FALSE，
NOT EXISTS 为 TRUE，
这一行保留。
```

这里的：

```sql
SELECT 1
```

不是为了真的取出数字 `1`，而是表示：

```text
我不关心右表返回什么字段；
我只关心右表中是否存在匹配记录。
```

---

## SQL 两种写法对比

| 写法 | 思路 | 适合理解成 |
|---|---|---|
| `LEFT JOIN + IS NULL` | 先连接，再找右表为空的记录 | 连完再找空 |
| `NOT EXISTS` | 不拼表，只判断右表是否存在匹配记录 | 查不到就保留 |

两种写法在本题中结果相同。

核心记忆：

```text
LEFT JOIN + IS NULL：
先把两张表连起来，再筛选右表没匹配上的行。

NOT EXISTS：
对左表每一行，检查右表是否存在匹配记录；
不存在就保留。
```

---

# Pandas 解法一：merge(..., indicator=True)

### Pandas 代码

```python
df_pd = (
    df_log
    .merge(
        df_device,
        how='left',
        on='device_id',
        indicator=True
    )
    .loc[lambda x: x['_merge'] == 'left_only']
    [
        [
            'device_id',
            'stat_date',
            'status',
            'alarm_count'
        ]
    ]
    .sort_values(by=['device_id', 'stat_date'])
    .reset_index(drop=True)
)

df_pd
```

---

### 逻辑说明

```python
.merge(
    df_device,
    how='left',
    on='device_id',
    indicator=True
)
```

表示：

```text
以 df_log 为左表做 left merge；
并生成一列 _merge，用来标记每一行的匹配来源。
```

`indicator=True` 会生成 `_merge` 字段，它有三种可能值：

| `_merge` 值 | 含义 |
|---|---|
| `left_only` | 只在左表中存在 |
| `right_only` | 只在右表中存在 |
| `both` | 两边都匹配成功 |

因此：

```python
.loc[lambda x: x['_merge'] == 'left_only']
```

表示：

```text
只保留 df_log 中存在、df_device 中不存在的记录。
```

这对应 SQL 中的：

```sql
LEFT JOIN ... WHERE right.key IS NULL
```

---

## Pandas 解法二：isin() / ~isin()

### Pandas 代码

```python
df_pd = (
    df_log
    .loc[
        lambda x: ~x['device_id'].isin(df_device['device_id'])
    ]
    [
        [
            'device_id',
            'stat_date',
            'status',
            'alarm_count'
        ]
    ]
    .sort_values(by=['device_id', 'stat_date'])
    .reset_index(drop=True)
)

df_pd
```

---

### 逻辑说明

```python
x['device_id'].isin(df_device['device_id'])
```

表示：

```text
判断 df_log 中的 device_id 是否存在于 df_device['device_id'] 中。
```

前面加 `~`：

```python
~x['device_id'].isin(df_device['device_id'])
```

表示取反：

```text
保留那些不在 df_device 中的 device_id。
```

所以这句的含义是：

```text
找 df_log 中有，
但 df_device 中没有的 device_id。
```

这更接近 SQL 中的：

```sql
NOT EXISTS
```

---

## Pandas 两种写法对比

| 写法 | 思路 | 对应 SQL |
|---|---|---|
| `merge(..., indicator=True)` | 先 merge，再看 `_merge` 标记 | `LEFT JOIN + IS NULL` |
| `~isin()` | 直接判断 key 是否不在另一张表中 | `NOT EXISTS` |

当前阶段更推荐先掌握：

```python
merge(..., indicator=True)
```

原因是它能清楚显示匹配状态：

```text
left_only
right_only
both
```

这对排查数据质量问题很有用。

---

## 为什么 Pandas 不建议随便用右表字段 isna 判断

在 SQL 中，可以写：

```sql
WHERE dv.device_id IS NULL
```

因为 SQL 查询中可以明确保留：

```text
左表 device_id
右表 device_id
```

但在 Pandas 中，如果使用：

```python
merge(..., on='device_id')
```

合并后 `device_id` 只会保留一列，不会自动生成：

```text
device_id_x
device_id_y
```

所以不能直接判断“右表的 device_id 是否为空”。

有时也可以用右表字段判断，例如：

```python
site.isna()
```

但这种写法有风险。

原因是：

```text
某个设备可能确实匹配到了右表，
但它的 site 字段本身就是缺失值。
```

这时如果用：

```python
site.isna()
```

就会误判为“右表没有匹配上”。

因此 Pandas 中判断匹配来源，推荐使用：

```python
indicator=True
```

再筛选：

```python
_merge == 'left_only'
```

这是更稳妥的写法。

---

## SQL / Pandas 对应关系

| 目的 | SQL | Pandas |
|---|---|---|
| 找左表有、右表没有 | `LEFT JOIN + WHERE right.key IS NULL` | `merge(..., indicator=True)` 后筛选 `_merge == 'left_only'` |
| 判断另一张表不存在匹配记录 | `NOT EXISTS` | `~isin()` |
| 判断是否匹配成功 | 右表 key 是否为 `NULL` | `_merge` 是否为 `both` / `left_only` |

---

## 核心记忆点

```text
找左表有、右表没有：
LEFT JOIN + 右表 key IS NULL。
```

```text
NOT EXISTS：
右表查不到匹配记录，就保留左表当前行。
```

```text
Pandas 中 merge(on='key') 后，key 只保留一列。
不要随便用右表普通字段 isna 判断是否匹配失败。
```

```text
Pandas 判断匹配来源：
merge(..., indicator=True)
然后看 _merge。
```

```text
~isin()
可以理解成 Pandas 版 NOT EXISTS。
```

## Task 2:(省略)


## Task 3：找出从未出现过 ERROR 的设备

### 题目目标

从设备信息表 `df_device` 出发，找出：

```text
在设备信息表中登记过，
但在日志表 df_log 中从未出现过 ERROR 状态的设备。
```

输出字段：

```text
device_id
site
device_type
model
```

---

### 业务要求

```text
只看 df_device 中登记过的设备。

如果某个设备出现过 ERROR 日志，
则不输出。

如果某个设备只有 NORMAL 日志，
但从未出现过 ERROR，
则需要输出。

如果某个设备完全没有任何日志，
也算作从未出现过 ERROR，
也需要输出。
```

本题的关键不是判断：

```text
设备有没有日志
```

而是判断：

```text
设备有没有 ERROR 日志
```

所以设备可以分成三类：

| 设备情况 | 是否输出 |
|---|---|
| 出现过 ERROR | 不输出 |
| 只有 NORMAL，从未 ERROR | 输出 |
| 没有任何日志 | 输出 |

---

## SQL 解法：NOT EXISTS

### SQL 代码

```sql
SELECT
    dv.device_id,
    dv.site,
    dv.device_type,
    dv.model
FROM df_device AS dv
WHERE NOT EXISTS (
    SELECT
        1
    FROM df_log AS lo
    WHERE lo.device_id = dv.device_id
      AND lo.status = 'ERROR'
)
ORDER BY dv.device_id;
```

---

### 逻辑说明

外层查询：

```sql
FROM df_device AS dv
```

表示最终筛选对象是设备表中的设备。

内层子查询：

```sql
SELECT
    1
FROM df_log AS lo
WHERE lo.device_id = dv.device_id
  AND lo.status = 'ERROR'
```

表示：

```text
对当前设备 dv，
去日志表 df_log 中查找：
是否存在同一个 device_id 且 status = 'ERROR' 的记录。
```

如果查得到 ERROR 记录：

```text
EXISTS = TRUE
NOT EXISTS = FALSE
当前设备不保留
```

如果查不到 ERROR 记录：

```text
EXISTS = FALSE
NOT EXISTS = TRUE
当前设备保留
```

因此这段 SQL 的完整含义是：

```text
从 df_device 中保留那些不存在 ERROR 日志的设备。
```

---

### NOT EXISTS 的核心理解

`NOT EXISTS` 不是把子查询里的数据删除。

它的作用是：

```text
判断子查询是否查得到结果。
```

也就是说：

```text
子查询查得到结果：
NOT EXISTS 为 FALSE，外层当前行不要。

子查询查不到结果：
NOT EXISTS 为 TRUE，外层当前行保留。
```

本题中，外层当前行是：

```text
df_device 中的一台设备
```

不是：

```text
df_log 中的一条日志
```

所以要记住：

```text
外层 FROM 是谁，WHERE 筛的就是谁。
```

本题外层是：

```sql
FROM df_device AS dv
```

所以被筛选的是设备，不是日志行。

---

## SQL 等价理解：先找 ERROR 设备，再排除

上面的 `NOT EXISTS` 也可以理解成下面这个过程：

```sql
WITH error_devices AS (
    SELECT DISTINCT
        device_id
    FROM df_log
    WHERE status = 'ERROR'
)

SELECT
    dv.device_id,
    dv.site,
    dv.device_type,
    dv.model
FROM df_device AS dv
LEFT JOIN error_devices AS ed
    ON dv.device_id = ed.device_id
WHERE ed.device_id IS NULL
ORDER BY dv.device_id;
```

这个版本的逻辑更直观：

```text
第一步：
从 df_log 中找出出现过 ERROR 的设备名单。

第二步：
从 df_device 中排除这些设备。

第三步：
剩下的就是从未出现过 ERROR 的设备。
```

---

## Pandas 解法：筛选 ERROR 设备后使用 ~isin()

### Pandas 代码

```python
error_devices = (
    df_log
    .loc[
        lambda x: x['status'] == 'ERROR',
        'device_id'
    ]
    .drop_duplicates()
)

df_pd = (
    df_device
    .loc[
        lambda x: ~x['device_id'].isin(error_devices)
    ]
    [
        [
            'device_id',
            'site',
            'device_type',
            'model'
        ]
    ]
    .sort_values(by='device_id')
    .reset_index(drop=True)
)

df_pd
```

---

### 逻辑说明

先构造出现过 ERROR 的设备名单：

```python
error_devices = (
    df_log
    .loc[
        lambda x: x['status'] == 'ERROR',
        'device_id'
    ]
    .drop_duplicates()
)
```

含义是：

```text
从 df_log 中筛选 status = 'ERROR' 的记录，
只取 device_id，
并去重。
```

得到的是：

```text
出现过 ERROR 的设备集合
```

然后：

```python
~x['device_id'].isin(error_devices)
```

表示：

```text
保留那些不在 ERROR 设备集合中的设备。
```

所以完整逻辑是：

```text
从 df_device 中，
排除所有出现过 ERROR 的设备，
剩下的就是从未出现过 ERROR 的设备。
```

---

## Pandas 原理对应 SQL

| 目的 | SQL | Pandas |
|---|---|---|
| 找出现过 ERROR 的设备 | `SELECT DISTINCT device_id FROM df_log WHERE status = 'ERROR'` | `df_log.loc[df_log['status'] == 'ERROR', 'device_id'].drop_duplicates()` |
| 从设备表中排除这些设备 | `WHERE NOT EXISTS (...)` | `~df_device['device_id'].isin(error_devices)` |
| 输出从未 ERROR 的设备 | 外层查询 `df_device` | 从 `df_device` 中筛选 |

---

## 本题和 Task 2 的区别

Task 2 判断的是：

```text
设备有没有任何日志
```

Task 3 判断的是：

```text
设备有没有 ERROR 日志
```

所以 Task 2 的条件是：

```sql
WHERE lo.device_id = dv.device_id
```

Task 3 的条件是：

```sql
WHERE lo.device_id = dv.device_id
  AND lo.status = 'ERROR'
```

多出的这一句：

```sql
AND lo.status = 'ERROR'
```

改变了业务含义。

Task 2 保留的是：

```text
完全没有日志的设备
```

Task 3 保留的是：

```text
从未出现过 ERROR 的设备
```

因此 Task 3 会同时包含：

```text
只有 NORMAL 日志的设备
完全没有日志的设备
```

---

## 核心记忆点

```text
NOT EXISTS 不是删除子查询里的数据，
而是判断子查询是否查得到结果。
```

```text
子查询查得到：
EXISTS = TRUE，NOT EXISTS = FALSE，外层当前行不要。

子查询查不到：
EXISTS = FALSE，NOT EXISTS = TRUE，外层当前行保留。
```

```text
外层 FROM 是谁，WHERE 筛的就是谁。
```

```text
条件 NOT EXISTS：
在子查询里加业务条件，
例如 status = 'ERROR'，
表示判断是否存在满足该条件的记录。
```

```text
Pandas 版条件 NOT EXISTS：
先构造满足条件的 key 集合，
再用 ~isin() 从主表中排除。
```