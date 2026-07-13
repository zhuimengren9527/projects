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

# 03_day_over_day_with_missing_dates

## 题型名称

Day Over Day Change With Missing Dates

中文理解：

> 存在缺失日期的日环比比较

---

## 一、题目目标

给定一张设备每日报警统计表：

| 字段名 | 含义 |
|---|---|
| device_id | 设备 ID |
| stat_date | 统计日期 |
| alarm_count | 当天报警次数 |

现在需要计算：

> 每个设备当天报警次数相比前一天变化了多少。

最终输出字段：

| 字段名 | 含义 |
|---|---|
| device_id | 设备 ID |
| stat_date | 当前日期 |
| alarm_count | 当前日期报警次数 |
| previous_day_alarm_count | 前一天报警次数 |
| alarm_count_diff | 当前报警次数 - 前一天报警次数 |

---

## 二、核心业务难点

这道题的关键不是计算差值，而是判断：

```text
前一天
```

不能简单理解成：

```text
上一条记录
```

如果数据每天都有记录，那么：

```text
上一条记录 = 前一天记录
```

但如果中间缺日期，那么：

```text
上一条记录 ≠ 前一天记录
```

例如：

| device_id | stat_date | alarm_count |
|---|---|---:|
| A | 2026-07-01 | 10 |
| A | 2026-07-02 | 12 |
| A | 2026-07-04 | 15 |

对于 `2026-07-04` 来说：

```text
上一条记录是：2026-07-02
前一天应该是：2026-07-03
```

但是 `2026-07-03` 没有数据。

所以 `2026-07-04` 这一行的结果应该是：

```text
previous_day_alarm_count = NULL / NaN
alarm_count_diff = NULL / NaN
```

而不是：

```text
15 - 12 = 3
```

---

## 三、为什么不能直接使用 LAG / shift

如果直接使用 SQL 的 `LAG()`：

```sql
LAG(alarm_count) OVER(
    PARTITION BY device_id
    ORDER BY stat_date
)
```

或者 Pandas 的 `shift(1)`：

```python
df.groupby('device_id')['alarm_count'].shift(1)
```

它们取到的是：

```text
上一条记录
```

而不是：

```text
前一天记录
```

所以在日期不连续的情况下，`LAG()` / `shift(1)` 会产生业务错误。

记忆：

```text
上一条 / 上一次 / 前一笔：
用 LAG / shift

前一天 / 上个月 / 去年同期 / 指定时间差：
优先考虑日期偏移 + join / merge
```

一句话总结：

```text
顺序相邻，用 shift。
时间指定，用 join。
```

---

## 四、核心解法思想

这道题的正确思路是：

```text
复制一张原表
↓
把复制表的日期整体往后推 1 天
↓
把 alarm_count 改名为 previous_day_alarm_count
↓
用 device_id + stat_date 合并回原表
↓
计算当前值 - 前一天值
```

为什么要把日期往后推 1 天？

因为我们要把“昨天的数据”移动到“今天的位置”。

例如原始数据：

| device_id | stat_date | alarm_count |
|---|---|---:|
| A | 2026-07-01 | 10 |

把日期加 1 天以后变成：

| device_id | stat_date | previous_day_alarm_count |
|---|---|---:|
| A | 2026-07-02 | 10 |

这样它就可以和当前表里的这一行对齐：

| device_id | stat_date | alarm_count |
|---|---|---:|
| A | 2026-07-02 | 12 |

合并后得到：

| device_id | stat_date | alarm_count | previous_day_alarm_count |
|---|---|---:|---:|
| A | 2026-07-02 | 12 | 10 |

然后计算：

```text
alarm_count_diff = 12 - 10 = 2
```

---

## 五、SQL 解法

### 版本一：DuckDB / PostgreSQL 风格

如果 SQL 环境支持 `INTERVAL 1 DAY`，可以使用下面写法。

```sql
WITH previous_day_table AS (
    SELECT
        device_id,
        stat_date + INTERVAL 1 DAY AS stat_date,
        alarm_count AS previous_day_alarm_count
    FROM df
)

SELECT
    cur.device_id,
    cur.stat_date,
    cur.alarm_count,
    prev.previous_day_alarm_count,
    cur.alarm_count - prev.previous_day_alarm_count AS alarm_count_diff
FROM df AS cur
LEFT JOIN previous_day_table AS prev
    ON cur.device_id = prev.device_id
   AND cur.stat_date = prev.stat_date
ORDER BY cur.device_id, cur.stat_date;
```

### SQL 逻辑拆解

第一步，构造前一天数据表：

```sql
WITH previous_day_table AS (
    SELECT
        device_id,
        stat_date + INTERVAL 1 DAY AS stat_date,
        alarm_count AS previous_day_alarm_count
    FROM df
)
```

这一步的含义是：

```text
把原表中的日期整体往后推一天。
```

例如：

```text
A | 2026-07-01 | 10
```

变成：

```text
A | 2026-07-02 | previous_day_alarm_count = 10
```

第二步，当前表和前一天表做 `LEFT JOIN`：

```sql
FROM df AS cur
LEFT JOIN previous_day_table AS prev
    ON cur.device_id = prev.device_id
   AND cur.stat_date = prev.stat_date
```

这里使用 `LEFT JOIN` 的原因是：

```text
保留当前表的所有日期记录。
如果前一天没有数据，previous_day_alarm_count 保持 NULL。
```

第三步，计算差值：

```sql
cur.alarm_count - prev.previous_day_alarm_count AS alarm_count_diff
```

如果 `previous_day_alarm_count` 是 `NULL`，那么差值自然也是 `NULL`。

这正好符合业务含义：

```text
前一天没有数据，就无法计算日环比差值。
```

---

## 六、SQLite 写法

如果使用 SQLite，通常不能直接写：

```sql
stat_date + INTERVAL 1 DAY
```

可以使用：

```sql
date(stat_date, '+1 day')
```

SQLite 版本：

```sql
WITH previous_day_table AS (
    SELECT
        device_id,
        date(stat_date, '+1 day') AS stat_date,
        alarm_count AS previous_day_alarm_count
    FROM df
)

SELECT
    cur.device_id,
    cur.stat_date,
    cur.alarm_count,
    prev.previous_day_alarm_count,
    cur.alarm_count - prev.previous_day_alarm_count AS alarm_count_diff
FROM df AS cur
LEFT JOIN previous_day_table AS prev
    ON cur.device_id = prev.device_id
   AND date(cur.stat_date) = prev.stat_date
ORDER BY cur.device_id, cur.stat_date;
```

注意：

```text
不同 SQL 引擎的日期加减语法不同。
但是核心思想不变：
复制一张表，把日期平移一天，再 join 回来。
```

---

## 七、Pandas 解法

```python
prev_df = (
    df
    .assign(
        stat_date=lambda x: x['stat_date'] + pd.Timedelta(days=1)
    )
    .rename(
        columns={
            'alarm_count': 'previous_day_alarm_count'
        }
    )
)

df_pd = (
    df
    .merge(
        prev_df[['device_id', 'stat_date', 'previous_day_alarm_count']],
        on=['device_id', 'stat_date'],
        how='left'
    )
    .assign(
        alarm_count_diff=lambda x: (
            x['alarm_count'] - x['previous_day_alarm_count']
        )
    )
    .sort_values(by=['device_id', 'stat_date'])
    .reset_index(drop=True)
)

df_pd
```

### Pandas 逻辑拆解

第一步，构造前一天数据表：

```python
prev_df = (
    df
    .assign(
        stat_date=lambda x: x['stat_date'] + pd.Timedelta(days=1)
    )
    .rename(
        columns={
            'alarm_count': 'previous_day_alarm_count'
        }
    )
)
```

这一步做了两件事：

```text
1. 把 stat_date 整体加 1 天
2. 把 alarm_count 改名为 previous_day_alarm_count
```

原始数据：

```text
A | 2026-07-01 | 10
```

变成：

```text
A | 2026-07-02 | previous_day_alarm_count = 10
```

第二步，合并回原表：

```python
df.merge(
    prev_df[['device_id', 'stat_date', 'previous_day_alarm_count']],
    on=['device_id', 'stat_date'],
    how='left'
)
```

含义是：

```text
用当前表的 device_id + stat_date
去匹配已经平移后的 prev_df
```

如果能匹配上，说明前一天有数据。

如果匹配不上，说明前一天缺数据。

第三步，计算差值：

```python
alarm_count_diff=lambda x: (
    x['alarm_count'] - x['previous_day_alarm_count']
)
```

如果 `previous_day_alarm_count` 是 `NaN`，那么 `alarm_count_diff` 也是 `NaN`。

---

## 八、结果示例

原始数据：

| device_id | stat_date | alarm_count |
|---|---|---:|
| A | 2026-07-01 | 10 |
| A | 2026-07-02 | 12 |
| A | 2026-07-04 | 15 |
| A | 2026-07-05 | 9 |
| B | 2026-07-01 | 5 |
| B | 2026-07-02 | 8 |
| B | 2026-07-03 | 8 |
| B | 2026-07-04 | 6 |
| C | 2026-07-01 | 20 |
| C | 2026-07-03 | 25 |
| C | 2026-07-04 | 22 |

预期结果：

| device_id | stat_date | alarm_count | previous_day_alarm_count | alarm_count_diff |
|---|---|---:|---:|---:|
| A | 2026-07-01 | 10 | NULL | NULL |
| A | 2026-07-02 | 12 | 10 | 2 |
| A | 2026-07-04 | 15 | NULL | NULL |
| A | 2026-07-05 | 9 | 15 | -6 |
| B | 2026-07-01 | 5 | NULL | NULL |
| B | 2026-07-02 | 8 | 5 | 3 |
| B | 2026-07-03 | 8 | 8 | 0 |
| B | 2026-07-04 | 6 | 8 | -2 |
| C | 2026-07-01 | 20 | NULL | NULL |
| C | 2026-07-03 | 25 | NULL | NULL |
| C | 2026-07-04 | 22 | 25 | -3 |

---

## 九、常见错误

### 错误一：直接使用 LAG / shift

错误 SQL：

```sql
LAG(alarm_count) OVER(
    PARTITION BY device_id
    ORDER BY stat_date
) AS previous_alarm_count
```

错误 Pandas：

```python
df.groupby('device_id')['alarm_count'].shift(1)
```

问题：

```text
它们取的是上一条记录，不一定是前一天记录。
```

只要日期有缺失，结果就可能错误。

---

### 错误二：用 INNER JOIN

不推荐：

```sql
INNER JOIN previous_day_table AS prev
```

或者 Pandas：

```python
merge(..., how='inner')
```

问题：

```text
INNER JOIN 只保留能匹配到前一天数据的记录。
前一天缺失的当前记录会被直接删掉。
```

但本题要求保留所有当前日期记录。

所以应该使用：

```text
LEFT JOIN / how='left'
```

---

### 错误三：把缺失的前一天报警次数填成 0

不推荐：

```python
previous_day_alarm_count.fillna(0)
```

原因：

```text
前一天没有数据 ≠ 前一天报警次数为 0
```

这两个业务含义完全不同。

- 没有数据：不知道前一天报警次数是多少。
- 0：明确知道前一天报警次数是 0。

所以本题中应该保留 `NULL / NaN`。

---

### 错误四：只按日期合并，不按设备合并

错误：

```python
merge(prev_df, on='stat_date', how='left')
```

问题：

```text
不同设备的同一天会互相匹配，导致 A 设备匹配到 B 设备的数据。
```

正确匹配键必须是：

```text
device_id + stat_date
```

对应代码：

```python
on=['device_id', 'stat_date']
```

---

## 十、方法选择规则

以后看到类似问题时，先判断业务语义。

### 1. 如果业务问“上一条记录”

例如：

```text
当前温度比上一条记录变化了多少？
当前状态是否不同于上一条状态？
当前订单比上一笔订单金额高多少？
```

优先使用：

| 工具 | 方法 |
|---|---|
| SQL | `LAG()` |
| Pandas | `groupby().shift(1)` |

---

### 2. 如果业务问“指定时间差”

例如：

```text
和前一天相比
和上个月相比
和去年同期相比
和 7 天前相比
和 30 分钟前相比
```

优先使用：

| 工具 | 方法 |
|---|---|
| SQL | 自连接 / 日期偏移 / JOIN |
| Pandas | 复制表 / 日期偏移 / merge |

---

## 十一、核心记忆点

```text
上一条记录，是顺序关系。
前一天记录，是时间条件关系。
```

```text
顺序相邻，用 LAG / shift。
时间指定，用 JOIN / merge。
```

```text
如果日期可能缺失，不要把上一条记录当作前一天。
```

```text
前一天没有数据，不等于前一天数值为 0。
```

```text
做时间比较时，先问清楚：
业务要的是上一条，还是指定时间点？
```

---

## 十二、和真实工作的关系

真实业务数据中，时间序列经常不是完美连续的。

常见原因包括：

```text
设备断采
系统漏报
采集延迟
数据入库失败
节假日无数据
某些时间段无业务发生
```

因此在做“日环比”“周环比”“同比”“前后对比”时，不能无脑使用 `LAG()` 或 `shift()`。

必须先判断：

```text
上一条记录是否真的代表前一天？
```

如果不能保证日期连续，就应该使用：

```text
日期偏移 + join / merge
```

这道题的价值就在于：

```text
从语法思维升级到业务语义思维。
```