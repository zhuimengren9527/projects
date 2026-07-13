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

# 04_compare_with_previous_month_same_day

## 题型名称

Compare With Previous Month Same Day

中文理解：

> 与上个月同日比较 / 月环比比较

---

## 一、题目目标

给定一张设备每日报警统计表：

| 字段名 | 含义 |
|---|---|
| device_id | 设备 ID |
| stat_date | 统计日期 |
| alarm_count | 当天报警次数 |

现在需要计算：

> 每个设备当天报警次数，与上个月同一天相比变化了多少。

最终输出字段：

| 字段名 | 含义 |
|---|---|
| device_id | 设备 ID |
| stat_date | 当前日期 |
| alarm_count | 当前日期报警次数 |
| alarm_count_previous_month | 上个月同日报警次数 |
| alarm_count_diff_month | 当前报警次数 - 上个月同日报警次数 |

---

## 二、核心业务概念

### 1. 环比

环比的意思是：

```text
当前周期
和
上一个相邻周期
进行比较
```

常见环比包括：

| 类型 | 当前值 | 对比值 |
|---|---|---|
| 日环比 | 今天 | 昨天 |
| 周环比 | 本周 | 上周 |
| 月环比 | 本月 | 上个月 |
| 年环比 | 今年 | 去年 |

在本题中，数据粒度是“天”，业务要求是：

```text
当前日期 vs 上个月同一天
```

例如：

```text
2026-02-15 vs 2026-01-15
2026-03-15 vs 2026-02-15
2026-04-05 vs 2026-03-05
```

所以本题可以理解为：

```text
日级数据上的月环比
```

---

### 2. 同比

同比的意思是：

```text
当前周期
和
去年同期
进行比较
```

常见同比包括：

| 类型 | 当前值 | 对比值 |
|---|---|---|
| 日同比 | 今天 | 去年同一天 |
| 月同比 | 本月 | 去年同月 |
| 季度同比 | 本季度 | 去年同季度 |
| 年同比 | 今年 | 去年 |

例如：

```text
2026-07-01 vs 2025-07-01
2026-08 vs 2025-08
2026 Q2 vs 2025 Q2
```

同比常用于排除季节性影响。

例如机场、气象、销售、旅游、客流量等数据，往往存在明显季节周期，因此只看“上个月”不一定公平，还要看“去年同期”。

---

### 3. 自然月

自然月指日历上的真实月份。

例如：

```text
2026-01-01 到 2026-01-31
2026-02-01 到 2026-02-28
2026-03-01 到 2026-03-31
```

自然月不是固定 30 天。

所以：

```text
上个月
≠
30 天前
```

例如：

```text
2026-03-01 的上个月同日是 2026-02-01
```

但如果用 30 天前：

```text
2026-03-01 - 30 天 = 2026-01-30
```

这显然不是上个月同日。

因此做月环比时，不应该使用固定天数：

```python
pd.Timedelta(days=30)
```

而应该使用自然月偏移：

```python
pd.DateOffset(months=1)
```

---

### 4. 自然年

自然年指日历上的真实年份。

例如：

```text
2026-01-01 到 2026-12-31
```

自然年也不是简单固定 365 天，因为存在闰年。

所以：

```text
去年同期
≠
365 天前
```

做同比时，不建议使用：

```python
pd.Timedelta(days=365)
```

而应该使用：

```python
pd.DateOffset(years=1)
```

---

## 三、为什么不能用 Timedelta(days=30)

`Timedelta` 适合固定长度的时间差。

例如：

| 业务问题 | Pandas 写法 |
|---|---|
| 前一天 | `pd.Timedelta(days=1)` |
| 7 天前 | `pd.Timedelta(days=7)` |
| 30 分钟前 | `pd.Timedelta(minutes=30)` |
| 10 秒前 | `pd.Timedelta(seconds=10)` |

但“上个月”不是固定 30 天。

因为每个月天数不同：

| 月份 | 天数 |
|---|---:|
| 1 月 | 31 |
| 2 月 | 28 或 29 |
| 3 月 | 31 |
| 4 月 | 30 |
| 5 月 | 31 |

因此，月环比应该使用：

```python
pd.DateOffset(months=1)
```

年同比应该使用：

```python
pd.DateOffset(years=1)
```

---

## 四、Pandas 重要语法：DateOffset

### 1. 正确写法：months=1

```python
pd.DateOffset(months=1)
```

含义是：

```text
在原日期基础上增加 1 个自然月
```

例如：

```text
2026-01-15 + DateOffset(months=1) = 2026-02-15
2026-02-15 + DateOffset(months=1) = 2026-03-15
2026-03-05 + DateOffset(months=1) = 2026-04-05
```

---

### 2. 错误写法：month=1

```python
pd.DateOffset(month=1)
```

这不是“加 1 个月”。

它的含义是：

```text
把月份设置为 1 月
```

例如：

```text
2026-01-15 + DateOffset(month=1) = 2026-01-15
2026-02-15 + DateOffset(month=1) = 2026-01-15
2026-03-15 + DateOffset(month=1) = 2026-01-15
```

所以：

```text
months=1 是相对偏移
month=1 是指定月份
```

这是本题的重要易错点。

---

### 3. years=1 和 year=2026 的区别

同理：

```python
pd.DateOffset(years=1)
```

含义是：

```text
在原日期基础上增加 1 年
```

例如：

```text
2025-07-01 + DateOffset(years=1) = 2026-07-01
```

而：

```python
pd.DateOffset(year=2026)
```

含义是：

```text
把年份设置为 2026
```

例如：

```text
2024-07-01 + DateOffset(year=2026) = 2026-07-01
2025-07-01 + DateOffset(year=2026) = 2026-07-01
```

记忆：

```text
months / years 是加减偏移
month / year 是指定日期部件
```

---

## 五、核心解法思想

这道题和“前一天比较”的整体方法一样，都是：

```text
复制一张原表
↓
把复制表中的日期向后平移一个周期
↓
把指标字段改名为历史指标
↓
用 device_id + stat_date 合并回原表
↓
计算当前值 - 历史值
```

本题的区别在于：

```text
前一天比较：日期 + 1 天
上个月同日比较：日期 + 1 个自然月
去年同期比较：日期 + 1 个自然年
```

本题要把“上个月的数据”移动到“本月的位置”。

例如原始数据：

| device_id | stat_date | alarm_count |
|---|---|---:|
| A | 2026-01-15 | 10 |

把日期加 1 个自然月后：

| device_id | stat_date | alarm_count_previous_month |
|---|---|---:|
| A | 2026-02-15 | 10 |

这样它就可以和当前表中的这一行对齐：

| device_id | stat_date | alarm_count |
|---|---|---:|
| A | 2026-02-15 | 14 |

合并后：

| device_id | stat_date | alarm_count | alarm_count_previous_month |
|---|---|---:|---:|
| A | 2026-02-15 | 14 | 10 |

最后计算：

```text
alarm_count_diff_month = 14 - 10 = 4
```

---

## 六、Pandas 解法

```python
prev_month_df = (
    df
    .assign(
        stat_date=lambda x: (
            x['stat_date'] + pd.DateOffset(months=1)
        )
    )
    .rename(
        columns={
            'alarm_count': 'alarm_count_previous_month'
        }
    )
)

df_pd = (
    df
    .merge(
        prev_month_df[
            ['device_id', 'stat_date', 'alarm_count_previous_month']
        ],
        on=['device_id', 'stat_date'],
        how='left'
    )
    .assign(
        alarm_count_diff_month=lambda x: (
            x['alarm_count'] - x['alarm_count_previous_month']
        )
    )
    .sort_values(by=['device_id', 'stat_date'])
    .reset_index(drop=True)
)

df_pd
```

---

## 七、Pandas 逻辑拆解

### 第一步：构造上个月数据表

```python
prev_month_df = (
    df
    .assign(
        stat_date=lambda x: (
            x['stat_date'] + pd.DateOffset(months=1)
        )
    )
    .rename(
        columns={
            'alarm_count': 'alarm_count_previous_month'
        }
    )
)
```

这一步的含义是：

```text
把原始表中的每一条记录向后移动一个自然月。
```

原始记录：

```text
A | 2026-01-15 | 10
```

移动后：

```text
A | 2026-02-15 | alarm_count_previous_month = 10
```

---

### 第二步：合并回当前表

```python
df.merge(
    prev_month_df[
        ['device_id', 'stat_date', 'alarm_count_previous_month']
    ],
    on=['device_id', 'stat_date'],
    how='left'
)
```

匹配键是：

```text
device_id + stat_date
```

不能只按 `stat_date` 合并，否则不同设备之间会错误匹配。

使用 `how='left'` 是为了：

```text
保留当前表中的所有记录。
如果找不到上个月同日记录，就保留 NaN。
```

---

### 第三步：计算差值

```python
alarm_count_diff_month=lambda x: (
    x['alarm_count'] - x['alarm_count_previous_month']
)
```

如果 `alarm_count_previous_month` 是 `NaN`，那么差值也是 `NaN`。

这代表：

```text
上个月同日没有数据，无法计算月环比差值。
```

---

## 八、SQL 解法

### 1. DuckDB 写法

```sql
WITH previous_month_table AS (
    SELECT
        device_id,
        stat_date + INTERVAL 1 MONTH AS stat_date,
        alarm_count AS alarm_count_previous_month
    FROM df
)

SELECT
    cur.device_id,
    cur.stat_date,
    cur.alarm_count,
    prev.alarm_count_previous_month,
    cur.alarm_count - prev.alarm_count_previous_month AS alarm_count_diff_month
FROM df AS cur
LEFT JOIN previous_month_table AS prev
    ON cur.device_id = prev.device_id
   AND cur.stat_date = prev.stat_date
ORDER BY cur.device_id, cur.stat_date;
```

---

### 2. PostgreSQL 写法

PostgreSQL 常见写法：

```sql
WITH previous_month_table AS (
    SELECT
        device_id,
        stat_date + INTERVAL '1 month' AS stat_date,
        alarm_count AS alarm_count_previous_month
    FROM df
)

SELECT
    cur.device_id,
    cur.stat_date,
    cur.alarm_count,
    prev.alarm_count_previous_month,
    cur.alarm_count - prev.alarm_count_previous_month AS alarm_count_diff_month
FROM df AS cur
LEFT JOIN previous_month_table AS prev
    ON cur.device_id = prev.device_id
   AND cur.stat_date = prev.stat_date
ORDER BY cur.device_id, cur.stat_date;
```

---

### 3. SQLite 写法

SQLite 通常使用：

```sql
date(stat_date, '+1 month')
```

完整写法：

```sql
WITH previous_month_table AS (
    SELECT
        device_id,
        date(stat_date, '+1 month') AS stat_date,
        alarm_count AS alarm_count_previous_month
    FROM df
)

SELECT
    cur.device_id,
    cur.stat_date,
    cur.alarm_count,
    prev.alarm_count_previous_month,
    cur.alarm_count - prev.alarm_count_previous_month AS alarm_count_diff_month
FROM df AS cur
LEFT JOIN previous_month_table AS prev
    ON cur.device_id = prev.device_id
   AND date(cur.stat_date) = prev.stat_date
ORDER BY cur.device_id, cur.stat_date;
```

---

### 4. MySQL 写法

MySQL 常见写法：

```sql
DATE_ADD(stat_date, INTERVAL 1 MONTH)
```

完整写法：

```sql
WITH previous_month_table AS (
    SELECT
        device_id,
        DATE_ADD(stat_date, INTERVAL 1 MONTH) AS stat_date,
        alarm_count AS alarm_count_previous_month
    FROM df
)

SELECT
    cur.device_id,
    cur.stat_date,
    cur.alarm_count,
    prev.alarm_count_previous_month,
    cur.alarm_count - prev.alarm_count_previous_month AS alarm_count_diff_month
FROM df AS cur
LEFT JOIN previous_month_table AS prev
    ON cur.device_id = prev.device_id
   AND cur.stat_date = prev.stat_date
ORDER BY cur.device_id, cur.stat_date;
```

---

## 九、不同时间偏移语法总结

### Pandas

| 业务含义 | 推荐写法 |
|---|---|
| 前一天 | `pd.Timedelta(days=1)` |
| 7 天前 | `pd.Timedelta(days=7)` |
| 30 分钟前 | `pd.Timedelta(minutes=30)` |
| 上个月同日 | `pd.DateOffset(months=1)` |
| 去年同日 | `pd.DateOffset(years=1)` |
| 下一个自然月 | `pd.DateOffset(months=1)` |
| 下一个自然年 | `pd.DateOffset(years=1)` |

---

### SQL

| 数据库 | 加 1 天 | 加 1 个月 | 加 1 年 |
|---|---|---|---|
| DuckDB | `+ INTERVAL 1 DAY` | `+ INTERVAL 1 MONTH` | `+ INTERVAL 1 YEAR` |
| PostgreSQL | `+ INTERVAL '1 day'` | `+ INTERVAL '1 month'` | `+ INTERVAL '1 year'` |
| SQLite | `date(col, '+1 day')` | `date(col, '+1 month')` | `date(col, '+1 year')` |
| MySQL | `DATE_ADD(col, INTERVAL 1 DAY)` | `DATE_ADD(col, INTERVAL 1 MONTH)` | `DATE_ADD(col, INTERVAL 1 YEAR)` |

---

## 十、常见错误

### 错误一：把上个月理解为 30 天前

错误写法：

```python
df['stat_date'] + pd.Timedelta(days=30)
```

问题：

```text
自然月不是固定 30 天。
```

正确写法：

```python
df['stat_date'] + pd.DateOffset(months=1)
```

---

### 错误二：写成 DateOffset(month=1)

错误写法：

```python
pd.DateOffset(month=1)
```

问题：

```text
month=1 表示把月份设置为 1 月，不是加 1 个月。
```

正确写法：

```python
pd.DateOffset(months=1)
```

记忆：

```text
months=1：加 1 个月
month=1：设置为 1 月
```

---

### 错误三：用 LAG / shift 代替上个月同日

错误 SQL：

```sql
LAG(alarm_count) OVER(
    PARTITION BY device_id
    ORDER BY stat_date
)
```

错误 Pandas：

```python
df.groupby('device_id')['alarm_count'].shift(1)
```

问题：

```text
LAG / shift 取的是上一条记录。
上个月同日是指定日期条件。
```

只要中间缺少月份或日期，上一条记录就不等于上个月同日。

---

### 错误四：INNER JOIN 导致数据丢失

不推荐：

```sql
INNER JOIN previous_month_table
```

或者：

```python
merge(..., how='inner')
```

问题：

```text
如果当前日期找不到上个月同日记录，这一行会被直接删除。
```

本题要求保留所有当前记录，因此应该使用：

```text
LEFT JOIN / how='left'
```

---

### 错误五：把缺失的上月数据填成 0

不推荐：

```python
df_pd['alarm_count_previous_month'].fillna(0)
```

原因：

```text
上个月同日没有数据 ≠ 上个月同日报警次数为 0
```

两者业务含义不同：

| 情况 | 含义 |
|---|---|
| NaN / NULL | 不知道上个月同日是多少 |
| 0 | 明确知道上个月同日报警次数为 0 |

本题应该保留 `NaN / NULL`。

---

## 十一、月底日期的特殊情况

自然月比较有一个特殊问题：

```text
并不是每个月都有 29、30、31 号。
```

例如：

```text
2026-01-31 的下个月同日
```

理论上应该是：

```text
2026-02-31
```

但这个日期不存在。

不同工具和数据库可能会对月底日期做不同处理，例如调整到月底，或者按内部规则转换。

因此在真实业务中，遇到月底日期时必须先明确业务规则：

```text
如果上个月同日不存在，是否匹配到上个月最后一天？
还是直接认为没有可比日期？
```

常见业务规则有两种：

| 规则 | 含义 |
|---|---|
| 严格同日 | 只匹配同一天号，不存在就算缺失 |
| 月末对月末 | 如果当前是月末，则匹配上个月月末 |

本题暂时采用简单规则：

```text
只处理普通日期，不专门处理月底特殊情况。
```

后续如果做真实月度分析，需要单独处理月底逻辑。

---

## 十二、方法选择规则

### 1. 顺序相邻问题

如果业务说：

```text
上一条记录
上一笔订单
上一次状态
前一行
```

优先使用：

| 工具 | 方法 |
|---|---|
| SQL | `LAG()` |
| Pandas | `groupby().shift(1)` |

---

### 2. 固定时间差问题

如果业务说：

```text
前一天
7 天前
30 分钟前
10 秒前
```

优先使用：

| 工具 | 方法 |
|---|---|
| SQL | 日期偏移 + JOIN |
| Pandas | `pd.Timedelta()` + merge |

---

### 3. 自然周期问题

如果业务说：

```text
上个月
去年同期
自然月
自然年
月环比
同比
```

优先使用：

| 工具 | 方法 |
|---|---|
| SQL | `INTERVAL 1 MONTH / INTERVAL 1 YEAR` |
| Pandas | `pd.DateOffset(months=1 / years=1)` + merge |

---

## 十三、核心记忆点

```text
上一条记录，是顺序关系。
前一天 / 上个月 / 去年同期，是时间条件关系。
```

```text
顺序相邻，用 LAG / shift。
指定时间点，用 JOIN / merge。
```

```text
固定天数，用 Timedelta。
自然月 / 自然年，用 DateOffset。
```

```text
months=1 是加一个月。
month=1 是设置为 1 月。
```

```text
years=1 是加一年。
year=2026 是设置为 2026 年。
```

```text
上个月不等于 30 天前。
去年同期不等于 365 天前。
```

---

## 十四、和真实工作的关系

真实业务中，环比和同比非常常见。

例如：

```text
本日报警次数 vs 昨日报警次数
本周故障次数 vs 上周故障次数
本月销售额 vs 上月销售额
本月客流量 vs 去年同月客流量
当前能见度指标 vs 10 分钟前能见度指标
```

但这些问题不能只看语法，必须先判断业务定义：

```text
到底是上一条记录？
还是前一天？
还是上个月？
还是去年同期？
```

如果业务定义判断错了，即使代码能运行，结果也是错的。

本题的价值在于：

```text
从“会写 shift / LAG”
升级为
“能根据业务时间定义选择正确方法”
```

## Pandas 重点：为什么这里要用 where，而不是 loc

在增长率计算中，需要处理两种不能计算增长率的情况：

```text
previous_month_alarm_count 是 NaN
previous_month_alarm_count 等于 0
```

这两种情况下：

```text
growth_rate = NaN
growth_rate_pct = NaN
```

但是注意：

```text
不能删除这些行。
```

因为这些行本身仍然是有效的当前日期记录，只是没有可用的历史基准值。

---

### 一、错误写法：使用 loc 筛选

不推荐写法：

```python
.loc[
    lambda x: (
        x['previous_month_alarm_count'].notna()
        & (x['previous_month_alarm_count'] != 0)
    )
]
```

这句的含义是：

```text
只保留 previous_month_alarm_count 不是空，并且不等于 0 的行。
```

结果会导致：

```text
没有上个月数据的行被删除；
上个月值为 0 的行被删除。
```

但本题要求保留所有当前记录，因此不能用 `.loc[]` 来处理这个逻辑。

记忆：

```text
loc 是筛行。
不符合条件的行会被删除。
```

---

### 二、正确写法：使用 where 控制字段结果

推荐写法：

```python
growth_rate=lambda x: (
    (x['alarm_count_diff'] / x['previous_month_alarm_count'])
    .where(
        x['previous_month_alarm_count'].notna()
        & (x['previous_month_alarm_count'] != 0)
    )
)
```

这句的意思是：

```text
先计算 alarm_count_diff / previous_month_alarm_count
然后只在条件满足的地方保留结果；
条件不满足的地方自动变成 NaN。
```

也就是说：

```text
previous_month_alarm_count 不是空，并且不等于 0
→ 保留增长率

previous_month_alarm_count 是空，或者等于 0
→ growth_rate 变成 NaN
```

关键区别是：

```text
where 不删除行。
where 只是控制这个字段里的值。
```

---

### 三、完整 Pandas 模板

```python
df_prev_month = (
    df
    .assign(
        stat_date=lambda x: (
            x['stat_date'] + pd.DateOffset(months=1)
        )
    )
    .rename(
        columns={
            'alarm_count': 'previous_month_alarm_count'
        }
    )
)

df_pd = (
    df
    .merge(
        df_prev_month[
            ['device_id', 'stat_date', 'previous_month_alarm_count']
        ],
        on=['device_id', 'stat_date'],
        how='left'
    )
    .assign(
        alarm_count_diff=lambda x: (
            x['alarm_count'] - x['previous_month_alarm_count']
        ),
        growth_rate=lambda x: (
            (x['alarm_count_diff'] / x['previous_month_alarm_count'])
            .where(
                x['previous_month_alarm_count'].notna()
                & (x['previous_month_alarm_count'] != 0)
            )
        ),
        growth_rate_pct=lambda x: (
            (x['alarm_count_diff'] * 100 / x['previous_month_alarm_count'])
            .where(
                x['previous_month_alarm_count'].notna()
                & (x['previous_month_alarm_count'] != 0)
            )
        )
    )
    .sort_values(by=['device_id', 'stat_date'])
    .reset_index(drop=True)
)

df_pd
```

---

### 四、where 的基本理解

```python
series.where(condition)
```

可以理解成：

```text
条件为 True：
保留原来的值。

条件为 False：
变成 NaN。
```

例如：

```python
s.where(s > 0)
```

含义是：

```text
只保留大于 0 的值；
小于等于 0 的位置变成 NaN；
但行不会被删除。
```

如果想把不满足条件的位置改成指定值，也可以写：

```python
s.where(s > 0, other=0)
```

含义是：

```text
大于 0 的地方保留原值；
不大于 0 的地方改成 0。
```

但本题不建议填 0，因为：

```text
不能计算增长率
不等于
增长率为 0
```

所以这里让它保持 `NaN` 更符合业务含义。

---

### 五、loc 和 where 的区别

| 方法 | 作用 | 是否删除行 | 适用场景 |
|---|---|---:|---|
| `.loc[condition]` | 筛选行 | 会删除行 | 只想保留满足条件的记录 |
| `.where(condition)` | 控制字段值 | 不删除行 | 保留全部记录，但让部分结果变成 NaN |

本题应该使用：

```text
where
```

因为业务要求是：

```text
保留所有日期记录；
只是不计算无效增长率。
```

---

### 六、和 SQL CASE WHEN 的对应关系

Pandas 的 `.where()` 在这里相当于 SQL 中的：

```sql
CASE
    WHEN previous_month_alarm_count IS NULL
      OR previous_month_alarm_count = 0
    THEN NULL
    ELSE alarm_count_diff * 1.0 / previous_month_alarm_count
END AS growth_rate
```

对应关系：

| SQL | Pandas |
|---|---|
| `CASE WHEN ... THEN NULL ELSE ... END` | `.where(condition)` |
| 条件不满足返回 `NULL` | 条件不满足返回 `NaN` |
| 不删除行 | 不删除行 |

Pandas 写法：

```python
(
    x['alarm_count_diff'] / x['previous_month_alarm_count']
).where(
    x['previous_month_alarm_count'].notna()
    & (x['previous_month_alarm_count'] != 0)
)
```

这里的 condition 是“可以正常计算增长率”的条件：

```text
previous_month_alarm_count 不是空
并且
previous_month_alarm_count 不等于 0
```

---

### 七、核心记忆点

```text
要删除行，用 loc。
要保留行但控制结果是否有效，用 where。
```

```text
增长率不能计算时，应该让 growth_rate 为 NaN，
而不是把整行删除。
```

```text
previous_month_alarm_count = NaN：
没有比较基准。

previous_month_alarm_count = 0：
有基准值，但不能作为除数。
```

```text
无法计算增长率
不等于
增长率为 0。
```