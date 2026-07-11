# 03_cumulative_analysis

本文件夹用于练习窗口函数中的 **Cumulative Analysis（累计统计问题）**。

这一类问题的核心是：

> 在每个分组内部，按照某种顺序排列，计算截至当前行的累计值。

它解决的不是“谁排第几”，而是：

> 到当前这一条记录为止，累计发生了多少？

---

## 一、适用业务场景

Cumulative Analysis 在真实业务中非常常见，典型场景包括：

- 用户截至当前订单的累计消费金额
- 用户截至当前日期的累计订单次数
- 设备截至当前时间的累计报警次数
- 某产品截至当前日期的累计销售额
- 某机场设备截至当前时间的累计故障次数
- 每日新增数据转化为累计数据
- 截至当前时间的累计访问量、累计注册数、累计成交额

这一类问题的关键词通常是：

```text
累计
截至当前
到目前为止
running total
running count
累计金额
累计次数
累计报警数
累计销售额
```

## 二、核心Pattern

`Cumulative Analysis` 的基本流程是：

按对象分组
↓
按时间或顺序排序
↓
从组内第一行累计到当前行
↓
生成累计指标

SQL 中主要使用：

`SUM() OVER(...)`
`COUNT() OVER(...)`
`AVG() OVER(...)`

Pandas 中主要使用：

`groupby().cumsum()`
`groupby().cumcount()`
`expanding()`
`rolling()`

## 01_running_total

题型名称

`Running Total`

中文理解：

`累计求和问题`

题目目标:

给定一张用户订单表，计算：

每个用户每次下单后的累计消费金额。

字段包括：

|字段名|	含义|
|-----|--------|
user_id|	用户 ID
order_time	|下单时间
order_id	|订单 ID
amount	|当前订单金额

最终输出：

字段名	|含义
-------|----
user_id	|用户 ID
order_time	|下单时间
order_id	|订单 ID
amount|	当前订单金额
running_total_amount	|截至当前订单的累计消费金额

三、SQL / Pandas 双轨对应
目的	|SQL	|Pandas
--------|-------|------
按用户分组	|PARTITION BY user_id|	groupby('user_id')
按时间排序|	ORDER BY order_time	|sort_values(['user_id', 'order_time'])
累计求和|	SUM(amount) OVER(...)	|groupby('user_id')['amount'].cumsum()
从第一行累计到当前行|	ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW	|cumsum() 默认从组内第一行累计到当前行
最终排序|	ORDER BY user_id, order_time	|.reset_index(drop=True)

## 四、SQL 模板
```sql
SELECT
    user_id,
    order_time,
    order_id,
    amount,
    SUM(amount) OVER(
        PARTITION BY user_id
        ORDER BY order_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total_amount
FROM df
ORDER BY user_id, order_time;
```

核心理解：

`PARTITION BY user_id`
= 每个用户单独累计

`ORDER BY order_time`
= 每个用户内部按时间顺序累计

`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
= 从组内第一条记录累计到当前记录

## 五、Pandas 模板
```python
df_pd = (
    df
    .sort_values(by=['user_id', 'order_time'])
    .assign(
        running_total_amount=lambda x: (
            x.groupby('user_id')['amount'].cumsum()
        )
    )
    .reset_index(drop=True)
)
```

核心理解：

`sort_values(['user_id', 'order_time'])`
= 先按用户排序，再按时间排序

`groupby('user_id')`
= 每个用户单独计算

`cumsum()`
= 对 amount 做累计求和

## 六、本题注意点
1. Pandas 中不要在 assign 内部 reset_index

错误写法：
```python
.assign(
    running_total_amount=lambda x: (
        x.groupby('user_id')['amount']
         .cumsum()
         .reset_index(drop=True)
    )
)
```
原因：

`cumsum()` 的结果会按照当前 `DataFrame` 的索引对齐。
如果在 `assign` 内部提前 `reset_index(drop=True)`，可能导致索引错位。

推荐写法：
```python
.assign(
    running_total_amount=lambda x: (
        x.groupby('user_id')['amount'].cumsum()
    )
)
.reset_index(drop=True)
```

**原则：**

`assign` 里面负责生成新列；
`reset_index` 放在链式处理最后统一执行。

2. SQL 最终排序要写完整

不只写：

`ORDER BY user_id`

推荐写：

`ORDER BY user_id, order_time`

因为累计统计依赖顺序，最终展示也应该保持和累计逻辑一致。

3. 如果同一用户同一时间有多笔订单

真实业务中可能出现同一用户同一时间多笔订单。

这时 SQL 建议写成：

`ORDER BY order_time, order_id`

Pandas 对应：

`.sort_values(by=['user_id', 'order_time', 'order_id'])`

这样累计顺序更稳定。

## 七、记忆点
```sql
SQL:
SUM() OVER(
    PARTITION BY 分组字段
    ORDER BY 排序字段
)
```
```python
Pandas:
sort_values()
+ groupby()
+ cumsum()
```

看到“累计”“截至当前”“到目前为止”，优先判断为：

`Cumulative Analysis`

# 02_running_count

## 题型名称

Running Count

中文理解：

> 累计计数问题

---

## 题目目标

给定一张用户订单表，计算：

> 每个用户每次下单后，当前是该用户的第几次下单。

最终输出字段：

| 字段名 | 含义 |
|---|---|
| user_id | 用户 ID |
| order_time | 下单时间 |
| order_id | 订单 ID |
| amount | 当前订单金额 |
| running_order_count | 截至当前订单的累计下单次数 |

---

## SQL / Pandas 双轨对应

| 目的 | SQL | Pandas |
|---|---|---|
| 按用户分组 | `PARTITION BY user_id` | `groupby('user_id')` |
| 按下单时间排序 | `ORDER BY order_time, order_id` | `sort_values(['user_id', 'order_time', 'order_id'])` |
| 累计计数 | `COUNT(*) OVER(...)` | `groupby('user_id').cumcount() + 1` |
| 从第一行累计到当前行 | `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | `cumcount()` 默认按组内顺序累计 |
| 最终整理索引 | SQL 不需要 | `reset_index(drop=True)` |

---

## SQL 模板

```sql
SELECT
    user_id,
    order_time,
    order_id,
    amount,
    COUNT(*) OVER(
        PARTITION BY user_id
        ORDER BY order_time, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_order_count
FROM df
ORDER BY user_id, order_time, order_id;
```
## Pandas 模板

```python
df_pd = (
    df
    .sort_values(by=['user_id', 'order_time', 'order_id'])
    .assign(
        running_order_count=lambda x: (
            x.groupby('user_id').cumcount() + 1
        )
    )
    .reset_index(drop=True)
)
```

---

## 本题注意点

### 1. 优先使用 `COUNT(*)`，不要用 `COUNT(amount)`

不推荐：

```sql
COUNT(amount) OVER(...)
```

原因：

```text
COUNT(amount) 只统计 amount 非空的行。
如果某一笔订单 amount 为空，它不会被计入。
```

本题目标是统计“第几次下单”，应该统计订单行数，所以推荐：

```sql
COUNT(*) OVER(...)
```

---

### 2. 排序最好加上 `order_id`

如果同一个用户在同一时间有多笔订单，只按 `order_time` 排序可能不稳定。

SQL 推荐：

```sql
ORDER BY order_time, order_id
```

Pandas 对应：

```python
.sort_values(by=['user_id', 'order_time', 'order_id'])
```

---

## 记忆点

```text
SQL:
COUNT(*) OVER(
    PARTITION BY 分组字段
    ORDER BY 排序字段
)

Pandas:
sort_values()
+ groupby()
+ cumcount() + 1
```

看到“第几次”“累计次数”“截至当前发生了几次”，优先判断为：

> Cumulative Analysis / Running Count

# 03_running_average

## 题型名称

Running Average

中文理解：

> 累计平均值问题

---

## 题目目标

给定一张用户订单表，计算：

> 每个用户每次下单后，截至当前订单的平均消费金额。

最终输出字段：

| 字段名 | 含义 |
|---|---|
| user_id | 用户 ID |
| order_time | 下单时间 |
| order_id | 订单 ID |
| amount | 当前订单金额 |
| running_avg_amount | 截至当前订单的累计平均消费金额 |

---

## 一、核心理解

累计平均值本质上可以拆成两个指标：

```text
累计平均值 = 累计金额 / 累计次数
```

所以 Pandas 中可以先计算：

```text
running_sum
running_count
```

再得到：

```text
running_avg_amount = running_sum / running_count
```

这比直接使用 `expanding().mean()` 更容易理解，也能和前两题联系起来：

| 题目 | 核心指标 | SQL | Pandas |
|---|---|---|---|
| 01_running_total | 累计金额 | `SUM() OVER(...)` | `groupby().cumsum()` |
| 02_running_count | 累计次数 | `COUNT(*) OVER(...)` | `groupby().cumcount() + 1` |
| 03_running_average | 累计平均值 | `AVG() OVER(...)` | `running_sum / running_count` 或 `expanding().mean()` |

---

## 二、SQL / Pandas 双轨对应

| 目的 | SQL | Pandas |
|---|---|---|
| 按用户分组 | `PARTITION BY user_id` | `groupby('user_id')` |
| 按时间排序 | `ORDER BY order_time, order_id` | `sort_values(['user_id', 'order_time', 'order_id'])` |
| 累计平均值 | `AVG(amount) OVER(...)` | `groupby().expanding().mean()` |
| 累计金额 | `SUM(amount) OVER(...)` | `groupby()['amount'].cumsum()` |
| 累计次数 | `COUNT(*) OVER(...)` | `groupby().cumcount() + 1` |
| 平均值公式 | `AVG(amount)` | `running_sum / running_count` |

---

## 三、SQL 模板

```sql
SELECT
    user_id,
    order_time,
    order_id,
    amount,
    AVG(amount) OVER(
        PARTITION BY user_id
        ORDER BY order_time, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_avg_amount
FROM df
ORDER BY user_id, order_time, order_id;
```

核心理解：

```text
PARTITION BY user_id
= 每个用户单独计算累计平均值

ORDER BY order_time, order_id
= 每个用户内部按订单顺序计算

ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
= 从组内第一条订单计算到当前订单
```

---

## 四、Pandas 模板一：累计金额 / 累计次数

推荐优先掌握这一版。

```python
df_pd = (
    df
    .sort_values(by=['user_id', 'order_time', 'order_id'])
    .assign(
        running_sum=lambda x: (
            x.groupby('user_id')['amount'].cumsum()
        ),
        running_count=lambda x: (
            x.groupby('user_id').cumcount() + 1
        ),
        running_avg_amount=lambda x: (
            x['running_sum'] / x['running_count']
        )
    )
    .reset_index(drop=True)
)
```

核心理解：

```text
running_sum
= 截至当前订单的累计金额

running_count
= 截至当前订单的累计订单次数

running_avg_amount
= 累计金额 / 累计次数
```

这一版的优点：

```text
逻辑直观；
容易检查中间结果；
能复用 running_total 和 running_count 两道题的思路。
```

---

## 五、Pandas 模板二：expanding().mean()

```python
df_pd2 = (
    df
    .sort_values(by=['user_id', 'order_time', 'order_id'])
    .assign(
        running_avg_amount=lambda x: (
            x.groupby('user_id')['amount']
             .expanding()
             .mean()
             .reset_index(level=0, drop=True)
        )
    )
    .reset_index(drop=True)
)
```

核心理解：

```text
groupby('user_id')
= 每个用户单独计算

expanding()
= 从组内第一条记录开始，窗口不断扩大

mean()
= 对当前 expanding window 计算平均值

reset_index(level=0, drop=True)
= 去掉 groupby 产生的外层 user_id 索引，使结果可以对齐回原 DataFrame
```

---

## 六、expanding() 是什么

`expanding()` 可以理解为：

> 从第一行开始，不断扩大的窗口。

例如某个用户的订单金额是：

```text
100
80
120
60
```

那么：

```python
expanding().mean()
```

计算过程是：

```text
第 1 行：[100]                  → 100
第 2 行：[100, 80]              → 90
第 3 行：[100, 80, 120]         → 100
第 4 行：[100, 80, 120, 60]     → 90
```

所以 `expanding()` 适合处理：

```text
截至当前的平均值
截至当前的最大值
截至当前的最小值
截至当前的标准差
```

---

## 七、groupby 后的索引问题总结

本题最容易混淆的是：

> 为什么有些 `groupby()` 结果可以直接放进 `assign()`，有些不行？

关键不是有没有 `groupby()`，而是：

> groupby 后面的操作是否改变了索引结构。

---

### 1. 可以直接 assign 的情况

以下操作通常会保留原始行索引，所以可以直接放回原 DataFrame。

| 写法 | 返回结果 | 能否直接 assign |
|---|---|---|
| `groupby().cumsum()` | 每行一个结果，保留原索引 | 可以 |
| `groupby().cumcount()` | 每行一个结果，保留原索引 | 可以 |
| `groupby().rank()` | 每行一个结果，保留原索引 | 可以 |
| `groupby().transform()` | 每行一个结果，保留原索引 | 可以 |

例如：

```python
df.assign(
    running_sum=lambda x: (
        x.groupby('user_id')['amount'].cumsum()
    )
)
```

这里不需要 `reset_index()`，因为 `cumsum()` 返回的结果仍然和原 DataFrame 一行对一行。

---

### 2. 不能直接 assign 的情况

以下操作容易改变索引结构，不能直接放回原 DataFrame。

| 写法 | 返回结果 | 问题 |
|---|---|---|
| `groupby().sum()` | 每组一行，索引变成分组字段 | 行数变少，不能直接对齐 |
| `groupby().mean()` | 每组一行，索引变成分组字段 | 行数变少，不能直接对齐 |
| `groupby().agg()` | 每组一行，索引变成分组字段 | 行数变少，不能直接对齐 |
| `groupby().expanding().mean()` | 每行一个结果，但索引变成 MultiIndex | 索引结构不一致 |

---

## 八、为什么 expanding 需要 reset_index(level=0, drop=True)

这段代码：

```python
s = (
    df_sorted
    .groupby('user_id')['amount']
    .expanding()
    .mean()
)
```

结果会产生 MultiIndex，大概长这样：

```text
user_id   
A        0    100.000000
         1     90.000000
         2    100.000000
         3     90.000000
B        4     60.000000
         5     75.000000
         6    100.000000
C        7    200.000000
         8    125.000000
         9    108.333333
Name: amount, dtype: float64
```

它有两层索引：

```text
第 0 层：user_id
第 1 层：原始行索引
```

而原 DataFrame 的索引只有：

```text
原始行索引
```

所以不能直接 assign。

需要去掉第 0 层索引：

```python
s.reset_index(level=0, drop=True)
```

含义是：

```text
level=0
= 操作第 0 层索引，也就是 user_id 这一层

drop=True
= 直接丢掉这一层索引，不要把它变成普通列
```

如果少了 `drop=True`：

```python
s.reset_index(level=0)
```

结果会变成一个 DataFrame，包含两列：

```text
user_id
amount
```

而 assign 新列时只能接收一维 Series，不能把一个两列 DataFrame 塞进一个字段里，所以会报错。

---

## 九、本题犯过的错误

### 1. 字段名拼写错误

错误写法：

```python
running_avg_amount=lambda x: (
    x['running_tatal_sum'] / x['running_total_count']
)
```

问题：

```text
running_tatal_sum 拼写错误。
前面创建的是 running_total_sum。
```

建议变量名不要过长，可以使用：

```text
running_sum
running_count
running_avg
```

减少拼写错误。

---

### 2. expanding 结果不能直接 assign

错误写法：

```python
df_pd2 = (
    df
    .sort_values(by=['user_id', 'order_time', 'order_id'])
    .assign(
        running_avg_amount=lambda x: (
            x.groupby('user_id')['amount']
             .expanding()
             .mean()
        )
    )
)
```

问题：

```text
groupby().expanding().mean() 返回 MultiIndex。
它的索引结构和原 DataFrame 不一致，无法直接作为新列插入。
```

正确写法：

```python
df_pd2 = (
    df
    .sort_values(by=['user_id', 'order_time', 'order_id'])
    .assign(
        running_avg_amount=lambda x: (
            x.groupby('user_id')['amount']
             .expanding()
             .mean()
             .reset_index(level=0, drop=True)
        )
    )
    .reset_index(drop=True)
)
```

---

## 十、记忆点

```text
SQL:
AVG(amount) OVER(
    PARTITION BY 分组字段
    ORDER BY 排序字段
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)

Pandas 方式一：
running_avg = running_sum / running_count

Pandas 方式二：
groupby()
+ expanding()
+ mean()
+ reset_index(level=0, drop=True)
```

看到“截至当前的平均值”“累计平均值”“到目前为止的平均金额”，优先判断为：

> Cumulative Analysis / Running Average