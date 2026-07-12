# 04_time_comparison

本文件夹用于练习窗口函数中的 **Time Comparison（前后记录比较问题）**。

这一类问题的核心是：

> 在同一个分组内部，按照时间顺序，取当前行的上一条或下一条记录，然后进行比较。

常见业务场景包括：

- 当前温度与上一条温度的差值
- 当前订单金额与上一笔订单金额的变化
- 当前状态与上一状态是否发生变化
- 当前能见度与上一分钟能见度的差值
- 当前故障值与上一次正常值的比较
- 环比变化
- 前后记录差异检测

这一类问题的关键词通常是：

```text
上一条
上一次
前一笔
前一天
相比上次
变化了多少
当前值 - 上一个值
```

---

# 01_previous_record_comparison

## 题型名称

Previous Record Comparison

中文理解：

> 与上一条记录比较

---

## 题目目标

给定一张设备温度记录表，计算：

> 每个设备当前记录与上一条记录的温度差。

最终输出字段：

| 字段名 | 含义 |
|---|---|
| device_id | 设备 ID |
| collect_time | 采集时间 |
| temp_value | 当前温度 |
| previous_temp_value | 上一条温度 |
| temp_diff | 当前温度与上一条温度的差值 |

---

## 一、核心理解

这道题的核心流程是：

```text
按设备分组
↓
按时间排序
↓
取上一条记录的温度
↓
当前温度 - 上一条温度
```

这一类问题的核心不是聚合，而是：

> 让当前行能够看到上一行的数据。

---

## 二、SQL / Pandas 双轨对应

| 目的 | SQL | Pandas |
|---|---|---|
| 按设备分组 | `PARTITION BY device_id` | `groupby('device_id')` |
| 按时间排序 | `ORDER BY collect_time` | `sort_values(['device_id', 'collect_time'])` |
| 取上一条记录 | `LAG(temp_value, 1)` | `shift(1)` |
| 计算差值 | `temp_value - previous_temp_value` | `x['temp_value'] - x['previous_temp_value']` |
| 第一条无上一条 | `NULL` | `NaN` |

---

## 三、SQL 模板

```sql
WITH previous_temp AS (
    SELECT
        device_id,
        collect_time,
        temp_value,
        LAG(temp_value, 1) OVER(
            PARTITION BY device_id
            ORDER BY collect_time
        ) AS previous_temp_value
    FROM df
)

SELECT
    device_id,
    collect_time,
    temp_value,
    previous_temp_value,
    temp_value - previous_temp_value AS temp_diff
FROM previous_temp
ORDER BY device_id, collect_time;
```

核心理解：

```text
PARTITION BY device_id
= 每个设备单独比较

ORDER BY collect_time
= 每个设备内部按时间顺序比较

LAG(temp_value, 1)
= 取当前行上一条记录的 temp_value
```

---

## 四、Pandas 模板

```python
df_pd = (
    df
    .sort_values(by=['device_id', 'collect_time'])
    .assign(
        previous_temp_value=lambda x: (
            x.groupby('device_id')['temp_value'].shift(1)
        ),
        temp_diff=lambda x: (
            x['temp_value'] - x['previous_temp_value']
        )
    )
    .reset_index(drop=True)
)
```

核心理解：

```text
groupby('device_id')
= 每个设备单独处理

shift(1)
= 取上一条记录

temp_value - previous_temp_value
= 当前值与上一条值的差
```

---

## 五、本题注意点

### 1. 不要随便把上一条缺失值填成 0

不推荐：

```sql
COALESCE(
    LAG(temp_value, 1) OVER(...),
    0
)
```

也不推荐：

```python
.shift(1).fillna(0)
```

原因：

```text
每个设备第一条记录本来没有上一条记录。
如果填成 0，就会变成“上一条温度是 0”，这会改变业务含义。
```

第一条记录更合理的结果是：

```text
previous_temp_value = NULL / NaN
temp_diff = NULL / NaN
```

因为它表达的是：

> 没有可比较对象。

只有业务明确规定“没有上一条时按 0 处理”，才应该使用 `COALESCE(..., 0)` 或 `.fillna(0)`。

---

### 2. 排序字段必须可靠

`LAG()` 和 `shift()` 都依赖当前数据顺序。

如果排序不正确，上一条记录就会取错。

SQL 推荐：

```sql
ORDER BY collect_time
```

如果同一设备同一时间可能有多条记录，应增加次级排序字段：

```sql
ORDER BY collect_time, record_id
```

Pandas 对应：

```python
.sort_values(by=['device_id', 'collect_time', 'record_id'])
```

---

## 六、记忆点

```text
SQL:
LAG(value, 1) OVER(
    PARTITION BY 分组字段
    ORDER BY 时间字段
)

Pandas:
sort_values()
+ groupby()
+ shift(1)
```

看到以下关键词，优先判断为：

> Time Comparison / Previous Record Comparison

```text
上一条
上一次
相比上次
当前值减上一值
前后变化
变化幅度
```

# 02_status_change_detection

## 题型名称

Status Change Detection

中文理解：

> 状态变化检测

---

## 题目目标

给定一张设备状态记录表，找出每个设备中：

> 当前状态和上一条状态不同的记录。

也就是判断：

```text
当前 status != 上一条 status
```

但每个设备的第一条记录没有上一条记录，因此不应该算作状态变化。

最终输出字段：

| 字段名 | 含义 |
|---|---|
| device_id | 设备 ID |
| collect_time | 采集时间 |
| status | 当前状态 |
| previous_status | 上一条状态 |
| is_status_changed | 是否发生状态变化 |

---

## 一、核心理解

这道题的核心流程是：

```text
按设备分组
↓
按时间排序
↓
取上一条状态
↓
判断当前状态是否不同于上一条状态
↓
排除没有上一条记录的第一行
```

这类问题本质上属于：

> Time Comparison / 前后记录比较

它不是做数值差值，而是做状态变化检测。

---

## 二、SQL / Pandas 双轨对应

| 目的 | SQL | Pandas |
|---|---|---|
| 按设备分组 | `PARTITION BY device_id` | `groupby('device_id')` |
| 按时间排序 | `ORDER BY collect_time` | `sort_values(['device_id', 'collect_time'])` |
| 取上一条状态 | `LAG(status)` | `shift(1)` |
| 判断存在上一条记录 | `previous_status IS NOT NULL` | `previous_status.notna()` |
| 判断状态不同 | `status <> previous_status` | `status != previous_status` |
| 筛选状态变化记录 | `WHERE is_status_changed = TRUE` | `.loc[lambda x: x['is_status_changed']]` |

---

## 三、SQL 模板

```sql
WITH previous_status_table AS (
    SELECT
        device_id,
        collect_time,
        status,
        LAG(status) OVER(
            PARTITION BY device_id
            ORDER BY collect_time
        ) AS previous_status
    FROM df
),

status_compare AS (
    SELECT
        device_id,
        collect_time,
        status,
        previous_status,
        CASE
            WHEN previous_status IS NOT NULL
             AND status <> previous_status
            THEN TRUE
            ELSE FALSE
        END AS is_status_changed
    FROM previous_status_table
)

SELECT
    device_id,
    collect_time,
    status,
    previous_status,
    is_status_changed
FROM status_compare
WHERE is_status_changed = TRUE
ORDER BY device_id, collect_time;
```

核心理解：

```text
LAG(status)
= 取上一条状态

previous_status IS NOT NULL
= 必须存在上一条记录

status <> previous_status
= 当前状态和上一条状态不同
```

---

## 四、Pandas 模板

```python
df_pd = (
    df
    .sort_values(by=['device_id', 'collect_time'])
    .assign(
        previous_status=lambda x: (
            x.groupby('device_id')['status'].shift(1)
        ),
        is_status_changed=lambda x: (
            x['previous_status'].notna()
            & (x['status'] != x['previous_status'])
        )
    )
    .loc[lambda x: x['is_status_changed']]
    .reset_index(drop=True)
)
```

核心理解：

```text
groupby('device_id')
= 每个设备单独比较

shift(1)
= 取上一条状态

previous_status.notna()
= 排除每个设备的第一条记录

status != previous_status
= 判断状态是否发生变化
```

---

## 五、本题注意点

### 1. SQL 中 `value <> NULL` 不是 True

在 SQL 里，`NULL` 表示未知值，不是普通值。

所以：

```sql
'NORMAL' <> NULL
```

结果不是：

```text
TRUE
```

而是：

```text
UNKNOWN / NULL
```

在 `CASE WHEN` 中，只有条件明确为 `TRUE`，才会进入 `THEN`。

因此下面这种写法：

```sql
CASE
    WHEN status <> previous_status THEN TRUE
    ELSE FALSE
END
```

当 `previous_status` 是 `NULL` 时，会走 `ELSE FALSE`。

更严谨的写法是：

```sql
CASE
    WHEN previous_status IS NOT NULL
     AND status <> previous_status
    THEN TRUE
    ELSE FALSE
END
```

---

### 2. Pandas 中要主动排除第一条记录

在 Pandas 中：

```python
x['status'] != x['previous_status']
```

如果 `previous_status` 是 `NaN`，可能会被判断为 `True`。

所以不能只写：

```python
x['status'] != x['previous_status']
```

应该写完整业务逻辑：

```python
x['previous_status'].notna()
& (x['status'] != x['previous_status'])
```

含义是：

```text
必须存在上一条状态
并且当前状态不同于上一条状态
```

---

### 3. 不要把 previous_status 填成固定值再比较

不推荐：

```python
.shift(1).fillna('UNKNOWN')
```

也不推荐在 SQL 中写：

```sql
COALESCE(previous_status, 'UNKNOWN')
```

原因：

```text
第一条记录没有上一条状态。
如果强行填成 UNKNOWN，可能会把第一条记录误判为状态变化。
```

第一条记录更合理的含义是：

```text
没有可比较对象
```

---

## 六、记忆点

```text
SQL:
LAG(status) OVER(
    PARTITION BY 分组字段
    ORDER BY 时间字段
)

判断变化：
previous_status IS NOT NULL
AND status <> previous_status
```

```text
Pandas:
sort_values()
+ groupby()
+ shift(1)

判断变化：
previous_status.notna()
& (status != previous_status)
```

看到以下关键词，优先判断为：

> Time Comparison / Status Change Detection

```text
状态变化
状态切换
从 NORMAL 变成 ERROR
从 ERROR 恢复 NORMAL
当前状态是否不同于上一条
前后状态是否一致
```