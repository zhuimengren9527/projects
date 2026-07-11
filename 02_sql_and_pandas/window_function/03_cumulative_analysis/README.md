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