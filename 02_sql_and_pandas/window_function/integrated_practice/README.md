# 设备运行状态综合分析

## 一、练习背景

现有一张设备每日运行状态表，记录每台设备每天的运行状态和报警次数。

本练习分别使用 SQL 和 Pandas 完成以下分析任务：

1. 状态变化检测；
2. 连续异常区间识别；
3. 最新异常记录查询；
4. 累计报警情况统计；
5. 月度对比变化分析。

本练习的重点不是孤立记忆 SQL 和 Pandas 语法，而是建立同一分析逻辑在两种工具中的对应关系。

---

## 二、数据字段

| 字段名        | 含义         |
| ------------- | ------------ |
| `device_id`   | 设备 ID      |
| `stat_date`   | 统计日期     |
| `status`      | 当天设备状态 |
| `alarm_count` | 当天报警次数 |

---

## 三、分析任务

### Task 1：状态变化检测

#### 1. 分析目标

判断每台设备当前记录的状态，是否相比上一条记录发生变化。

输出字段：

- `device_id`
- `stat_date`
- `status`
- `previous_status`
- `is_status_changed`

#### 2. 核心思路

```text
按设备分组
→ 按日期排序
→ 获取上一条状态
→ 比较当前状态与上一条状态
```

每台设备的第一条记录没有上一条状态，因此将：

```text
is_status_changed = False
```

#### 3. SQL 实现思路

SQL 使用窗口函数 `LAG()`，获取同一设备的上一条状态：

```sql
LAG(status) OVER (
    PARTITION BY device_id
    ORDER BY stat_date
)
```

其中：

- `PARTITION BY device_id`：每台设备独立计算；
- `ORDER BY stat_date`：按照日期顺序排列；
- `LAG(status)`：获取上一条记录的状态。

状态变化判断条件为：

```sql
status != previous_status
AND previous_status IS NOT NULL
```

#### 4. Pandas 实现思路

Pandas 使用 `groupby()` 和 `shift()` 获取上一条状态：

```python
df.groupby('device_id')['status'].shift(1)
```

状态变化判断条件为：

```python
df['previous_status'].notna() & (
    df['status'] != df['previous_status']
)
```

#### 5. SQL 与 Pandas 对应关系

| 分析动作       | SQL                      | Pandas                 |
| -------------- | ------------------------ | ---------------------- |
| 按设备分组     | `PARTITION BY device_id` | `groupby('device_id')` |
| 按日期排序     | `ORDER BY stat_date`     | `sort_values()`        |
| 获取上一条记录 | `LAG(status)`            | `shift(1)`             |
| 判断状态变化   | `CASE WHEN`              | 布尔条件               |
| 判断非空       | `IS NOT NULL`            | `notna()`              |

#### 6. 边界条件

当前实现基于以下前提：

1. `status` 字段不存在缺失值；
2. 同一设备的 `stat_date` 唯一；
3. 每台设备的第一条记录不视为状态变化。

如果同一设备在同一天存在多条记录，需要增加唯一排序字段，例如：

```text
record_id
```

排序方式应调整为：

```text
device_id
→ stat_date
→ record_id
```

---

### Task 2：连续异常区间识别

#### 1. 分析目标

识别每台设备连续处于 `ERROR` 状态的区间，并筛选持续至少 2 条记录的异常区间。

输出字段：

- `device_id`
- `error_start_date`
- `error_end_date`
- `error_days`

#### 2. 核心思路

```text
将 ERROR 状态转换为布尔值
→ 获取上一条记录是否为 ERROR
→ 识别每段 ERROR 的起点
→ 对异常起点累计生成区间编号
→ 只保留 ERROR 记录
→ 按设备和区间编号聚合
→ 筛选 error_days >= 2
```

异常区间起点的判断条件为：

```text
当前记录是 ERROR
并且
上一条记录不是 ERROR
```

转换为布尔表达式：

```text
is_error = True
previous_is_error = False
```

#### 3. SQL 实现思路

首先将 `ERROR` 状态转换为布尔值：

```sql
status = 'ERROR' AS status_is_error
```

使用 `LAG()` 获取上一条记录是否为 `ERROR`：

```sql
LAG(status_is_error) OVER (
    PARTITION BY device_id
    ORDER BY stat_date
)
```

使用 `COALESCE()` 将每台设备第一条记录的上一状态设为 `FALSE`：

```sql
COALESCE(
    LAG(status_is_error) OVER (
        PARTITION BY device_id
        ORDER BY stat_date
    ),
    FALSE
)
```

异常区间起点的判断逻辑为：

```sql
CASE
    WHEN status_is_error = TRUE
         AND previous_is_error = FALSE
    THEN 1
    ELSE 0
END
```

使用累计窗口函数对异常起点进行编号：

```sql
SUM(error_start_sign) OVER (
    PARTITION BY device_id
    ORDER BY stat_date
)
```

每出现一个新的异常起点，累计值增加 `1`，从而生成新的异常区间编号。

#### 4. Pandas 实现思路

将 `ERROR` 状态转换为布尔值：

```python
df['is_error'] = df['status'].eq('ERROR')
```

获取上一条记录是否为 `ERROR`：

```python
df['previous_is_error'] = (
    df.groupby('device_id')['is_error']
      .shift(1, fill_value=False)
)
```

识别异常区间起点：

```python
df['error_start'] = (
    df['is_error']
    & ~df['previous_is_error']
).astype(int)
```

在每台设备内部，对异常起点进行累计编号：

```python
df['phase_sign'] = (
    df.groupby('device_id')['error_start']
      .cumsum()
)
```

不能直接使用全局累计：

```python
df['error_start'].cumsum()
```

因为不同设备的异常区间应当分别编号。

#### 5. SQL 与 Pandas 对应关系

| 分析动作       | SQL                            | Pandas                    |
| -------------- | ------------------------------ | ------------------------- |
| 标记 ERROR     | `status = 'ERROR'`             | `status.eq('ERROR')`      |
| 获取上一条状态 | `LAG()`                        | `shift()`                 |
| 填充第一条记录 | `COALESCE(..., FALSE)`         | `shift(fill_value=False)` |
| 标记区间起点   | `CASE WHEN`                    | 布尔条件                  |
| 生成区间编号   | `SUM() OVER`                   | `groupby().cumsum()`      |
| 筛选异常记录   | `WHERE status_is_error = TRUE` | `.loc[df['is_error']]`    |
| 区间聚合       | `GROUP BY`                     | `groupby().agg()`         |
| 获取开始时间   | `MIN(stat_date)`               | `('stat_date', 'min')`    |
| 获取结束时间   | `MAX(stat_date)`               | `('stat_date', 'max')`    |
| 区间记录数     | `COUNT(*)`                     | `size`                    |

#### 6. 连续区间识别模式

本题使用的是典型的 Gap and Island 分析模式。

基本步骤为：

```text
条件布尔化
→ 比较当前记录与上一条记录
→ 标记新区间起点
→ 对起点累计编号
→ 按区间编号聚合
```

其中：

- Gap：两个连续区间之间的间隔；
- Island：满足某种连续条件的一组记录。

本题中的 Island 就是每一段连续的 `ERROR` 记录。

#### 7. 边界条件

当前代码识别的是：

> 连续记录中的异常区间。

`error_days` 实际统计的是每个异常区间中的记录数量。

只有满足以下条件时，记录数量才等于连续自然日天数：

1. 每台设备每天只有一条记录；
2. 日期记录完整，没有缺失日期。

例如，某设备只有以下两条记录：

```text
2026-07-01  ERROR
2026-07-03  ERROR
```

当前逻辑会将它们识别为连续两条异常记录，并得到：

```text
error_days = 2
```

但从自然日角度看，它们并不是连续两天，因为缺少：

```text
2026-07-02
```

如果后续需要识别连续自然日，还需要获取上一条记录的日期，并判断：

```text
当前日期 - 上一条日期 = 1 天
```

---

## 四、当前进度

- [x] Task 1：状态变化检测
- [x] Task 2：连续异常区间识别
- [ ] Task 3：最新异常记录
- [ ] Task 4：累计报警情况
- [ ] Task 5：月度对比变化

---

## 五、本次练习总结

### 1. 当前记录与上一条记录比较

对应方法为：

```text
SQL：LAG()
Pandas：groupby() + shift()
```

适用场景包括：

- 状态变化检测；
- 数值增减判断；
- 相邻记录时间差计算；
- 异常起点识别；
- 用户行为变化分析；
- 设备状态切换分析。

### 2. 连续区间识别

基本分析流程为：

```text
条件布尔化
→ 标记区间起点
→ 累计起点编号
→ 按区间聚合
```

适用场景包括：

- 连续异常；
- 连续缺失；
- 连续停机；
- 连续高温；
- 连续超标；
- 连续登录；
- 连续未下单；
- 连续故障。

### 3. SQL 与 Pandas 的核心对应

```text
SQL 窗口分区
PARTITION BY
```

对应：

```text
Pandas 分组
groupby()
```

```text
SQL 上一条记录
LAG()
```

对应：

```text
Pandas 上一条记录
shift()
```

```text
SQL 累计窗口
SUM() OVER
```

对应：

```text
Pandas 分组累计
groupby().cumsum()
```

本次练习的核心不是分别记忆两套语法，而是理解它们背后的共同分析过程：

```text
先确定分组范围
→ 再确定记录顺序
→ 获取相邻记录关系
→ 构造业务标记
→ 完成聚合或筛选
```

## Task 3：每个设备最近一次 ERROR 记录

### 题目目标

找出每个设备最近一次 `ERROR` 状态记录。

输出字段：

```text
device_id
stat_date
status
alarm_count
```

本题需要先筛选出 `status = 'ERROR'` 的记录，然后在每个设备内部按照 `stat_date` 从新到旧排序，取最新日期对应的记录。

---

### Pattern 分类

本题属于：

```text
Ranking / 分组排名问题
```

核心逻辑是：

```text
按设备分组
↓
筛选 ERROR 记录
↓
按日期降序排名
↓
取每个设备排名第 1 的记录
```

---

### SQL 解法

```sql
WITH date_rank_table AS (
    SELECT
        device_id,
        stat_date,
        status,
        alarm_count,
        RANK() OVER(
            PARTITION BY device_id
            ORDER BY stat_date DESC
        ) AS date_rank
    FROM df
    WHERE status = 'ERROR'
)

SELECT
    device_id,
    stat_date,
    status,
    alarm_count
FROM date_rank_table
WHERE date_rank = 1
ORDER BY device_id;
```

---

### SQL 逻辑说明

```sql
WHERE status = 'ERROR'
```

先只保留异常状态记录。

```sql
RANK() OVER(
    PARTITION BY device_id
    ORDER BY stat_date DESC
)
```

表示：

```text
每个设备单独排名；
日期越新，排名越靠前；
最新日期的 ERROR 记录排名为 1。
```

最后：

```sql
WHERE date_rank = 1
```

保留每个设备最新的 ERROR 记录。

---

### Pandas 解法

```python
df_pd = (
    df
    .loc[lambda x: x['status'] == 'ERROR']
    .assign(
        date_rank=lambda x: (
            x.groupby('device_id')['stat_date']
             .rank(method='min', ascending=False)
             .astype(int)
        )
    )
    .loc[lambda x: x['date_rank'] == 1]
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

### Pandas 逻辑说明

```python
.loc[lambda x: x['status'] == 'ERROR']
```

先筛选出 `ERROR` 记录。

```python
.groupby('device_id')['stat_date'].rank(
    method='min',
    ascending=False
)
```

表示：

```text
每个设备内部按 stat_date 排名；
日期越新，排名越靠前；
如果同一个设备最新日期有多条 ERROR，它们会得到相同排名。
```

```python
.loc[lambda x: x['date_rank'] == 1]
```

保留每个设备最新日期的 ERROR 记录。

---

### RANK 和 ROW_NUMBER 的业务区别

本题需要特别注意：

```text
最近一次 ERROR
```

可能有两种业务口径。

#### 口径一：每个设备只保留一条最近 ERROR

如果业务要求：

```text
每个设备最多只输出一条 ERROR 记录
```

则使用：

| 工具 | 方法 |
|---|---|
| SQL | `ROW_NUMBER()` |
| Pandas | `sort_values()` + `groupby().cumcount() + 1` |

这种写法会强行编号，即使同一天有多条 ERROR，也只保留其中一条。

---

#### 口径二：最新日期的 ERROR 全部保留

如果业务要求：

```text
如果同一个设备最新日期有多条 ERROR，全部保留
```

则使用：

| 工具 | 方法 |
|---|---|
| SQL | `RANK()` 或 `DENSE_RANK()` |
| Pandas | `rank(method='min')` 或 `rank(method='dense')` |

本题当前采用第二种口径：

```text
保留每个设备最新日期的所有 ERROR 记录。
```

---

### SQL / Pandas 对应关系

| SQL | Pandas | 含义 |
|---|---|---|
| `ROW_NUMBER()` | `sort_values()` + `groupby().cumcount() + 1` | 强行编号，不保留并列 |
| `RANK()` | `rank(method='min')` | 并列同名次，后续跳号 |
| `DENSE_RANK()` | `rank(method='dense')` | 并列同名次，后续不跳号 |

---

### 常见错误

#### 错误一：用 cumcount 处理并列最新日期

```python
.groupby('device_id').cumcount() + 1
```

这个方法对应的是 `ROW_NUMBER()`，会强行编号。

如果同一个设备同一天有两条最新 `ERROR`，只会保留其中一条。

如果业务要求保留并列最新日期的所有记录，应该使用：

```python
.rank(method='min', ascending=False)
```

---

#### 错误二：在使用 rank 时多余排序

如果使用：

```python
rank(method='min', ascending=False)
```

前面的 `sort_values()` 不是必须的，因为 `rank()` 本身已经根据 `stat_date` 计算排名。

但如果使用：

```python
groupby().cumcount() + 1
```

则必须先排序，因为 `cumcount()` 依赖当前 DataFrame 的行顺序。

---

### 核心记忆点

```text
每组最新一条：
ROW_NUMBER / cumcount

每组最新日期全部保留：
RANK / rank(method='min')

并列名次不跳号：
DENSE_RANK / rank(method='dense')
```

```text
先判断业务口径：
是只要一条？
还是最新日期并列记录都要？
```

## Task 4：每个设备报警次数最高的前 2 天

### 题目目标

找出每个设备 `alarm_count` 最高的前 2 天。

输出字段：

```text
device_id
stat_date
status
alarm_count
rn
```

业务要求：

```text
每个设备最多输出 2 条记录。
如果 alarm_count 相同，stat_date 较晚的排前面。
```

---

### Pattern 分类

本题属于：

```text
Ranking / 分组排序取 Top N
```

核心逻辑是：

```text
按设备分组
↓
组内按 alarm_count 降序排序
↓
如果 alarm_count 相同，按 stat_date 降序排序
↓
生成行号 rn
↓
筛选 rn <= 2
```

---

### SQL 解法

```sql
WITH rank_table AS (
    SELECT
        device_id,
        stat_date,
        status,
        alarm_count,
        ROW_NUMBER() OVER(
            PARTITION BY device_id
            ORDER BY alarm_count DESC, stat_date DESC
        ) AS rn
    FROM df
)

SELECT
    device_id,
    stat_date,
    status,
    alarm_count,
    rn
FROM rank_table
WHERE rn <= 2
ORDER BY device_id, rn;
```

---

### SQL 逻辑说明

```sql
PARTITION BY device_id
```

表示每个设备单独排名。

```sql
ORDER BY alarm_count DESC, stat_date DESC
```

表示：

```text
报警次数越高，排名越靠前；
如果报警次数相同，日期越晚，排名越靠前。
```

```sql
ROW_NUMBER()
```

表示强行生成唯一行号。

所以每个设备筛选：

```sql
WHERE rn <= 2
```

就能保证：

```text
每个设备最多输出 2 条记录。
```

---

### Pandas 解法

```python
df_pd = (
    df
    .sort_values(
        by=['device_id', 'alarm_count', 'stat_date'],
        ascending=[True, False, False]
    )
    .assign(
        rn=lambda x: (
            x.groupby('device_id').cumcount() + 1
        )
    )
    .loc[lambda x: x['rn'] <= 2]
    [
        [
            'device_id',
            'stat_date',
            'status',
            'alarm_count',
            'rn'
        ]
    ]
    .reset_index(drop=True)
)

df_pd
```

---

### Pandas 逻辑说明

```python
.sort_values(
    by=['device_id', 'alarm_count', 'stat_date'],
    ascending=[True, False, False]
)
```

先把数据排成目标顺序：

```text
device_id 升序；
alarm_count 降序；
stat_date 降序。
```

然后：

```python
x.groupby('device_id').cumcount() + 1
```

在每个设备内部按当前顺序生成行号。

最后：

```python
.loc[lambda x: x['rn'] <= 2]
```

保留每个设备前 2 条记录。

---

### 为什么这里不用 RANK

本题要求：

```text
每个设备最多输出 2 条。
```

这说明要取的是：

```text
Top 2 条记录
```

而不是：

```text
Top 2 档报警次数
```

所以应该使用：

| 业务口径 | SQL | Pandas |
|---|---|---|
| 每组最多取 N 条记录 | `ROW_NUMBER()` | `sort_values()` + `groupby().cumcount() + 1` |
| 每组取前 N 档数值，保留并列 | `RANK()` / `DENSE_RANK()` | `rank(method='min')` / `rank(method='dense')` |

如果使用 `RANK()`，当报警次数并列时，可能会输出超过 2 条记录。

例如某设备报警次数为：

```text
10
10
9
```

如果取 `RANK <= 2`，结果可能只得到两个 10；如果数据是：

```text
10
9
9
```

取 `RANK <= 2` 会得到三条记录。

但本题明确要求：

```text
每个设备最多输出 2 条。
```

因此应使用 `ROW_NUMBER()`。

---

### 常见错误

#### 错误一：误筛选 ERROR

错误写法：

```sql
WHERE status = 'ERROR'
```

或：

```python
.loc[lambda x: x['status'] == 'ERROR']
```

本题要求是：

```text
每个设备报警次数最高的前 2 天
```

不是：

```text
每个设备 ERROR 状态下报警次数最高的前 2 天
```

所以不应该先筛选 `ERROR`。

---

#### 错误二：用 rank 代替 cumcount

错误写法：

```python
x.groupby('device_id')['alarm_count'].rank(method='min', ascending=False)
```

这个写法适合“按报警次数分档排名”，不适合“每个设备最多取 2 条记录”。

本题应该使用：

```python
x.groupby('device_id').cumcount() + 1
```

前提是必须先完成正确排序。

---

#### 错误三：先 rank 后 sort

如果先用 `rank()` 生成排名，再在后面排序：

```python
.assign(...)
.sort_values(...)
```

后面的排序不会改变已经生成好的排名。

所以如果排名依赖多个排序条件，例如：

```text
alarm_count DESC
stat_date DESC
```

应该先 `sort_values()`，再用 `cumcount()` 生成行号。

---

### 核心记忆点

```text
Top N 条记录：
ROW_NUMBER / cumcount

Top N 档数值：
RANK / DENSE_RANK / rank
```

```text
题目说“最多输出 N 条”：
优先用 ROW_NUMBER。

题目说“前 N 名，允许并列都保留”：
考虑 RANK 或 DENSE_RANK。
```

```text
cumcount 依赖当前 DataFrame 行顺序；
所以必须先 sort_values，再 cumcount。
```

## Task 5：累计报警次数

### 题目目标

计算每个设备截至当天的累计报警次数。

输出字段：

```text
device_id
stat_date
status
alarm_count
running_alarm_count
```

业务要求：

```text
每个设备内部按 stat_date 从早到晚累计 alarm_count。
```

---

### Pattern 分类

本题属于：

```text
Cumulative Analysis / 累计统计
```

核心逻辑是：

```text
按设备分组
↓
按日期排序
↓
从每个设备的第一条记录开始
↓
一直累计到当前行
```

---

### SQL 解法

```sql
SELECT
    device_id,
    stat_date,
    status,
    alarm_count,
    SUM(alarm_count) OVER(
        PARTITION BY device_id
        ORDER BY stat_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_alarm_count
FROM df
ORDER BY device_id, stat_date;
```

---

### SQL 逻辑说明

```sql
PARTITION BY device_id
```

表示：

```text
每个设备单独累计。
A 设备和 B 设备之间不会互相影响。
```

```sql
ORDER BY stat_date
```

表示：

```text
每个设备内部按日期从早到晚排序。
累计值必须依赖明确的时间顺序。
```

```sql
SUM(alarm_count) OVER(...)
```

表示：

```text
在窗口范围内对 alarm_count 求和。
```

---

## 重点：ROWS BETWEEN ... AND ... 的理解

窗口函数里的：

```sql
ROWS BETWEEN 起点 AND 终点
```

表示：

```text
当前行计算时，窗口从哪里开始，到哪里结束。
```

它不是筛选最终结果，而是定义“当前这一行能看到哪些行”。

---

### 1. UNBOUNDED PRECEDING

```sql
UNBOUNDED PRECEDING
```

意思是：

```text
从当前分组的第一行开始。
```

例如：

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

意思是：

```text
从本设备第一条记录
一直到当前行
```

这就是累计统计最常用的窗口范围。

例如设备 A：

| stat_date | alarm_count | 窗口范围 | running_alarm_count |
|---|---:|---|---:|
| 2026-01-01 | 2 | 2 | 2 |
| 2026-01-02 | 5 | 2 + 5 | 7 |
| 2026-01-03 | 6 | 2 + 5 + 6 | 13 |

---

### 2. CURRENT ROW

```sql
CURRENT ROW
```

意思是：

```text
当前这一行。
```

所以：

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

就是：

```text
从第一行累计到当前行。
```

它不会看到当前行之后的数据。

---

### 3. N PRECEDING

```sql
1 PRECEDING
```

意思是：

```text
当前行的前 1 行。
```

```sql
2 PRECEDING
```

意思是：

```text
当前行的前 2 行。
```

注意：

```text
N PRECEDING 只表示当前行之前的 N 行。
如果终点是 CURRENT ROW，那么窗口总行数 = N + 1。
```

例如：

```sql
ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
```

表示：

```text
上一行 + 当前行
```

窗口最多 2 行。

这通常用于最近 2 条记录的移动平均。

---

### 4. N FOLLOWING

```sql
1 FOLLOWING
```

意思是：

```text
当前行的后 1 行。
```

例如：

```sql
ROWS BETWEEN CURRENT ROW AND 1 FOLLOWING
```

表示：

```text
当前行 + 下一行
```

这种在普通累计统计中不常用，但在向后观察、未来窗口分析中会出现。

---

## 常见窗口范围对照表

| SQL 写法 | 中文理解 | 常见用途 |
|---|---|---|
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | 从第一行到当前行 | 累计和、累计次数、累计平均 |
| `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` | 上一行 + 当前行 | 最近 2 条移动平均 |
| `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` | 前 2 行 + 当前行 | 最近 3 条移动平均 |
| `ROWS BETWEEN CURRENT ROW AND 1 FOLLOWING` | 当前行 + 下一行 | 向后窗口 |
| `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` | 整个分组所有行 | 每组总和、每组均值 |

---

## 一个容易混淆的点

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

不是“最近 2 行”。

它表示：

```text
前 2 行 + 当前行
```

所以窗口最多是：

```text
3 行
```

如果你想算“最近 2 条记录”，应该写：

```sql
ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
```

对应关系：

| 业务说法 | SQL 写法 |
|---|---|
| 最近 2 条，包括当前行 | `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` |
| 最近 3 条，包括当前行 | `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` |
| 最近 N 条，包括当前行 | `ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW` |

---

## ROWS 和 RANGE 的区别

窗口函数里有时会看到：

```sql
ROWS BETWEEN ...
```

也可能看到：

```sql
RANGE BETWEEN ...
```

当前阶段建议优先使用：

```sql
ROWS
```

原因是：

```text
ROWS 是按物理行数计算窗口。
RANGE 是按排序字段的值范围计算窗口。
```

如果 `ORDER BY stat_date` 中存在重复日期，`RANGE` 可能会把相同日期的多行一起纳入窗口，结果和你想象的不一样。

而：

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

含义更明确：

```text
按排序后的行，一行一行累计。
```

所以在做累计统计、移动平均时，建议显式写 `ROWS BETWEEN ... AND ...`。

---

## Pandas 解法

```python
df_pd = (
    df
    .sort_values(by=['device_id', 'stat_date'])
    .assign(
        running_alarm_count=lambda x: (
            x.groupby('device_id')['alarm_count'].cumsum()
        )
    )
    [
        [
            'device_id',
            'stat_date',
            'status',
            'alarm_count',
            'running_alarm_count'
        ]
    ]
    .reset_index(drop=True)
)

df_pd
```

---

### Pandas 逻辑说明

```python
.sort_values(by=['device_id', 'stat_date'])
```

先保证每个设备内部按日期从早到晚排列。

```python
.groupby('device_id')['alarm_count'].cumsum()
```

表示：

```text
每个设备单独累计 alarm_count。
```

它对应 SQL 中的：

```sql
SUM(alarm_count) OVER(
    PARTITION BY device_id
    ORDER BY stat_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

---

## SQL / Pandas 对应关系

| 目的 | SQL | Pandas |
|---|---|---|
| 按设备分组 | `PARTITION BY device_id` | `groupby('device_id')` |
| 按日期排序 | `ORDER BY stat_date` | `sort_values(['device_id', 'stat_date'])` |
| 从第一行累计到当前行 | `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | `cumsum()` |
| 累计报警次数 | `SUM(alarm_count) OVER(...)` | `groupby()['alarm_count'].cumsum()` |

---

## 常见错误

### 错误一：没有按日期排序

如果没有：

```sql
ORDER BY stat_date
```

或者 Pandas 中没有：

```python
sort_values(by=['device_id', 'stat_date'])
```

累计顺序就不可靠。

累计统计必须有明确顺序。

---

### 错误二：把移动窗口和累计窗口混淆

累计窗口：

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

含义是：

```text
从第一行到当前行。
```

移动窗口：

```sql
ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
```

含义是：

```text
上一行 + 当前行。
```

两者不是一回事。

---

### 错误三：把 2 PRECEDING 理解成最近 2 条

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

实际是：

```text
前 2 条 + 当前条 = 最多 3 条。
```

如果业务要最近 2 条，应该写：

```sql
ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
```

---

### 错误四：同一天多条记录时排序不唯一

如果一个设备同一天可能有多条记录，仅仅写：

```sql
ORDER BY stat_date
```

可能不够稳定。

真实业务里最好加更细的排序字段，例如：

```sql
ORDER BY stat_date, collect_time
```

或者：

```sql
ORDER BY stat_date, record_id
```

Pandas 也一样：

```python
sort_values(by=['device_id', 'stat_date', 'record_id'])
```

---

## 核心记忆点

```text
累计统计：
从第一行到当前行。
```

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

```text
最近 N 条：
前 N-1 行 + 当前行。
```

```sql
ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW
```

```text
1 PRECEDING + CURRENT ROW = 最近 2 条。
2 PRECEDING + CURRENT ROW = 最近 3 条。
```

```text
ROWS 是按行数算窗口。
RANGE 是按排序值范围算窗口。
当前阶段优先写 ROWS。
```

## Task 6：最近 2 条记录的平均报警次数

### 题目目标

计算每个设备当前记录和上一条记录的平均报警次数。

输出字段：

```text
device_id
stat_date
status
alarm_count
moving_avg_2_alarm_count
```

业务要求：

```text
每个设备第一条记录只有自己一条，也要计算平均值。
```

也就是说：

```text
第一条记录：
只用当前 alarm_count 计算平均值。

第二条及以后：
用上一条 alarm_count 和当前 alarm_count 计算平均值。
```

---

### Pattern 分类

本题属于：

```text
Cumulative Analysis / Rolling Window
```

更准确地说，是：

```text
移动窗口平均值
```

核心逻辑是：

```text
按设备分组
↓
按日期排序
↓
每一行取最近 2 条记录
↓
计算 alarm_count 的平均值
```

---

### SQL 解法

```sql
SELECT
    device_id,
    stat_date,
    status,
    alarm_count,
    AVG(alarm_count) OVER(
        PARTITION BY device_id
        ORDER BY stat_date
        ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
    ) AS moving_avg_2_alarm_count
FROM df
ORDER BY device_id, stat_date;
```

---

### SQL 逻辑说明

```sql
PARTITION BY device_id
```

表示：

```text
每个设备单独计算移动平均。
```

```sql
ORDER BY stat_date
```

表示：

```text
每个设备内部按日期从早到晚排序。
```

```sql
ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
```

表示：

```text
窗口范围 = 上一行 + 当前行
```

所以这不是累计到当前，而是只看最近 2 条记录。

例如：

| stat_date | alarm_count | 窗口范围 | moving_avg_2_alarm_count |
|---|---:|---|---:|
| 2026-01-01 | 2 | 2 | 2 |
| 2026-01-02 | 5 | 2, 5 | 3.5 |
| 2026-01-03 | 6 | 5, 6 | 5.5 |
| 2026-01-04 | 4 | 6, 4 | 5 |

注意：

```text
第一条记录没有上一行，所以窗口里只有当前行。
AVG() 会自动只对当前这一条记录求平均。
```

不要把第一条记录的上一条补成 0。

错误理解：

```text
第一条 = (当前值 + 0) / 2
```

正确理解：

```text
第一条 = 当前值本身
```

---

## Pandas 解法

```python
df_pd = (
    df
    .sort_values(by=['device_id', 'stat_date'])
    .assign(
        moving_avg_2_alarm_count=lambda x: (
            x.groupby('device_id')['alarm_count']
             .rolling(2, min_periods=1)
             .mean()
             .reset_index(level=0, drop=True)
        )
    )
    [
        [
            'device_id',
            'stat_date',
            'status',
            'alarm_count',
            'moving_avg_2_alarm_count'
        ]
    ]
    .reset_index(drop=True)
)

df_pd
```

---

## Pandas 重点：rolling() 的用法

### 1. rolling() 是什么

```python
rolling()
```

可以理解成：

```text
滚动窗口
```

它会沿着当前 DataFrame 的行顺序，一行一行往下移动窗口。

在本题中，先执行：

```python
sort_values(by=['device_id', 'stat_date'])
```

所以每个设备内部的行顺序是按日期从早到晚排列的。

然后：

```python
rolling(2)
```

表示：

```text
每一行最多取最近 2 条记录。
```

也就是：

```text
当前行 + 前 1 行
```

---

### 2. rolling(2) 的含义

```python
rolling(2)
```

这里的 `2` 表示窗口大小。

它不是“前 2 条”。

它表示：

```text
窗口最多包含 2 条记录。
```

如果窗口包含当前行，那么：

```text
rolling(2) = 当前行 + 前 1 行
rolling(3) = 当前行 + 前 2 行
rolling(N) = 当前行 + 前 N-1 行
```

所以：

| 业务含义 | Pandas 写法 |
|---|---|
| 最近 2 条，包括当前行 | `rolling(2)` |
| 最近 3 条，包括当前行 | `rolling(3)` |
| 最近 N 条，包括当前行 | `rolling(N)` |

这和 SQL 的对应关系是：

| 业务含义 | SQL | Pandas |
|---|---|---|
| 最近 2 条 | `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` | `rolling(2)` |
| 最近 3 条 | `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` | `rolling(3)` |
| 最近 N 条 | `ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW` | `rolling(N)` |

---

### 3. min_periods=1 的含义

```python
rolling(2, min_periods=1)
```

其中：

```python
min_periods=1
```

表示：

```text
窗口里至少有 1 条记录，就可以计算结果。
```

这对第一条记录很重要。

如果只写：

```python
rolling(2).mean()
```

默认情况下，窗口必须满 2 条才计算平均值。

那么每个设备第一条记录会得到：

```text
NaN
```

但本题要求：

```text
每个设备第一条记录只有自己一条，也要计算平均值。
```

所以必须写：

```python
rolling(2, min_periods=1).mean()
```

这样第一条记录窗口里虽然只有 1 条，也可以计算平均值。

例如设备 A：

| stat_date | alarm_count | rolling(2, min_periods=1) 的窗口 | 结果 |
|---|---:|---|---:|
| 2026-01-01 | 2 | 2 | 2 |
| 2026-01-02 | 5 | 2, 5 | 3.5 |
| 2026-01-03 | 6 | 5, 6 | 5.5 |

---

### 4. groupby().rolling() 的含义

```python
x.groupby('device_id')['alarm_count'].rolling(2, min_periods=1).mean()
```

这句的意思是：

```text
每个设备单独做 rolling。
```

如果不加：

```python
groupby('device_id')
```

那么 A 设备最后一条记录可能会和 B 设备第一条记录一起参与计算，这在业务上是错误的。

所以移动平均必须先分组：

```text
每个设备内部单独滚动。
```

---

### 5. 为什么要 reset_index(level=0, drop=True)

执行：

```python
x.groupby('device_id')['alarm_count']
 .rolling(2, min_periods=1)
 .mean()
```

之后，Pandas 会生成一个带有多层索引的结果。

大致类似：

```text
device_id   
A          0    2.0
           1    3.5
           2    5.5
B          3    1.0
           4    2.5
```

这个结果的索引有两层：

```text
第 0 层：device_id
第 1 层：原始行索引
```

但是 `.assign()` 需要把结果按原始行索引对齐回 DataFrame。

所以要写：

```python
.reset_index(level=0, drop=True)
```

含义是：

```text
去掉第 0 层 device_id 索引；
只保留原始行索引；
让结果可以正确对齐回原 DataFrame。
```

记忆：

```text
groupby().rolling() 之后，通常要 reset_index(level=0, drop=True)。
```

---

## 为什么不能用 shift().fillna(0)

错误写法：

```python
df_pd = (
    df
    .sort_values(by=['device_id', 'stat_date'])
    .assign(
        previous_alarm_count=lambda x: (
            x.groupby('device_id')['alarm_count']
             .shift(1)
             .fillna(0)
        ),
        moving_avg_2_alarm_count=lambda x: (
            (x['alarm_count'] + x['previous_alarm_count']) / 2
        )
    )
)
```

这个写法的问题是：

```text
把“没有上一条记录”
错误理解成
“上一条记录的报警次数为 0”
```

第一条记录如果 `alarm_count = 2`，会被算成：

```text
(2 + 0) / 2 = 1
```

但正确结果应该是：

```text
2
```

因为第一条记录只有自己一条，平均值就是自己。

所以：

```text
缺少上一条记录，不等于上一条记录为 0。
```

移动平均不要随便 `fillna(0)`。

---

## rolling 和 expanding 的区别

| 方法 | 窗口范围 | 适用场景 |
|---|---|---|
| `expanding()` | 从第一行到当前行，窗口越来越大 | 累计平均、累计统计 |
| `rolling(N)` | 最近 N 条记录，窗口大小固定 | 移动平均、最近 N 条统计 |

例如 alarm_count 为：

```text
2, 5, 6, 4
```

`expanding().mean()`：

```text
第 1 行：2
第 2 行：(2 + 5) / 2 = 3.5
第 3 行：(2 + 5 + 6) / 3 = 4.33
第 4 行：(2 + 5 + 6 + 4) / 4 = 4.25
```

`rolling(2, min_periods=1).mean()`：

```text
第 1 行：2
第 2 行：(2 + 5) / 2 = 3.5
第 3 行：(5 + 6) / 2 = 5.5
第 4 行：(6 + 4) / 2 = 5
```

核心区别：

```text
expanding 是从开头累计到当前。
rolling 是只看最近 N 条。
```

---

## SQL / Pandas 对应关系

| 目的 | SQL | Pandas |
|---|---|---|
| 按设备分组 | `PARTITION BY device_id` | `groupby('device_id')` |
| 按日期排序 | `ORDER BY stat_date` | `sort_values(['device_id', 'stat_date'])` |
| 最近 2 条窗口 | `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` | `rolling(2, min_periods=1)` |
| 计算平均值 | `AVG(alarm_count)` | `.mean()` |
| 第一条也计算 | `AVG()` 自动只算当前行 | `min_periods=1` |

---

## 常见错误

### 错误一：用 fillna(0) 补上一条记录

错误原因：

```text
没有上一条记录，不等于上一条记录为 0。
```

第一条记录应该只用自己计算平均值。

---

### 错误二：忘记 min_periods=1

如果写：

```python
rolling(2).mean()
```

每个设备第一条记录会得到 `NaN`。

本题要求第一条也计算，所以要写：

```python
rolling(2, min_periods=1).mean()
```

---

### 错误三：忘记 groupby

如果直接写：

```python
df['alarm_count'].rolling(2, min_periods=1).mean()
```

不同设备之间会串在一起计算。

应该写：

```python
df.groupby('device_id')['alarm_count'].rolling(2, min_periods=1).mean()
```

---

### 错误四：忘记 reset_index(level=0, drop=True)

`groupby().rolling()` 的结果是多层索引，直接放回 `.assign()` 可能无法正确对齐。

应该写：

```python
.reset_index(level=0, drop=True)
```

---

### 错误五：把 rolling(2) 理解成“前 2 条”

```python
rolling(2)
```

表示：

```text
窗口总大小为 2。
```

不是：

```text
前 2 条 + 当前条。
```

如果要“当前条 + 前 2 条”，应该写：

```python
rolling(3)
```

---

## 核心记忆点

```text
rolling(N) = 最近 N 条记录，包括当前行。
```

```text
rolling(2) = 当前行 + 前 1 行。
rolling(3) = 当前行 + 前 2 行。
```

```text
min_periods=1 = 窗口里至少 1 条就计算。
```

```text
groupby().rolling() 之后通常要 reset_index(level=0, drop=True)。
```

```text
没有上一条记录，不等于上一条记录为 0。
```

```text
移动平均用 rolling。
累计平均用 expanding。
```

## Task 7：上个月同日报警次数对比与增长率

### 题目目标

计算每个设备当天报警次数与上个月同日相比的变化量和增长率。

输出字段：

```text
device_id
stat_date
status
alarm_count
previous_month_alarm_count
alarm_count_diff
growth_rate
growth_rate_pct
```

业务要求：

```text
如果没有上个月同日记录：
previous_month_alarm_count = NULL / NaN
alarm_count_diff = NULL / NaN
growth_rate = NULL / NaN
growth_rate_pct = NULL / NaN

如果上个月同日报警次数为 0：
alarm_count_diff 可以正常计算
growth_rate = NULL / NaN
growth_rate_pct = NULL / NaN
```

---

### Pattern 分类

本题属于：

```text
Time Comparison / 指定时间点比较 / 增长率分析
```

更准确地说，本题不是比较上一条记录，而是比较：

```text
当前日期
vs
上个月同日
```

所以不能直接使用：

```text
LAG()
shift(1)
```

因为它们取的是上一条记录，而不是上个月同日记录。

---

### 核心业务理解

本题要找的是：

```text
同一个 device_id
并且日期是当前日期的上一个自然月同一天
```

例如：

```text
2026-02-01 对比 2026-01-01
2026-02-02 对比 2026-01-02
2026-03-05 对比 2026-02-05
```

所以本题的核心方法是：

```text
复制一张原表
↓
把复制表 stat_date 加 1 个自然月
↓
把 alarm_count 改名为 previous_month_alarm_count
↓
用 device_id + stat_date 合并回原表
↓
计算 diff 和 growth_rate
```

---

### SQL 解法

```sql
WITH previous_month AS (
    SELECT
        device_id,
        stat_date + INTERVAL 1 MONTH AS stat_date,
        alarm_count AS previous_month_alarm_count
    FROM df
),

join_table AS (
    SELECT
        curr.device_id,
        curr.stat_date,
        curr.status,
        curr.alarm_count,
        prev.previous_month_alarm_count
    FROM df AS curr
    LEFT JOIN previous_month AS prev
        ON curr.device_id = prev.device_id
       AND curr.stat_date = prev.stat_date
),

diff_table AS (
    SELECT
        device_id,
        stat_date,
        status,
        alarm_count,
        previous_month_alarm_count,
        alarm_count - previous_month_alarm_count AS alarm_count_diff
    FROM join_table
)

SELECT
    device_id,
    stat_date,
    status,
    alarm_count,
    previous_month_alarm_count,
    alarm_count_diff,
    CASE
        WHEN previous_month_alarm_count IS NULL
          OR previous_month_alarm_count = 0
        THEN NULL
        ELSE ROUND(alarm_count_diff * 1.0 / previous_month_alarm_count, 2)
    END AS growth_rate,
    CASE
        WHEN previous_month_alarm_count IS NULL
          OR previous_month_alarm_count = 0
        THEN NULL
        ELSE ROUND(alarm_count_diff * 100.0 / previous_month_alarm_count, 2)
    END AS growth_rate_pct
FROM diff_table
ORDER BY device_id, stat_date;
```

---

### SQL 逻辑说明

第一步，构造上个月数据表：

```sql
WITH previous_month AS (
    SELECT
        device_id,
        stat_date + INTERVAL 1 MONTH AS stat_date,
        alarm_count AS previous_month_alarm_count
    FROM df
)
```

这一步的含义是：

```text
把上个月的数据移动到本月的位置。
```

例如：

```text
A | 2026-01-01 | alarm_count = 2
```

变成：

```text
A | 2026-02-01 | previous_month_alarm_count = 2
```

这样它就可以和当前表中的：

```text
A | 2026-02-01 | alarm_count = 3
```

对齐。

---

第二步，使用 LEFT JOIN 合并回当前表：

```sql
FROM df AS curr
LEFT JOIN previous_month AS prev
    ON curr.device_id = prev.device_id
   AND curr.stat_date = prev.stat_date
```

这里必须使用：

```text
LEFT JOIN
```

原因是：

```text
要保留当前表中的所有记录。
如果找不到上个月同日数据，previous_month_alarm_count 应该保留为 NULL。
```

不能使用 `INNER JOIN`，否则没有上个月同日数据的当前记录会被删除。

---

第三步，计算变化量：

```sql
alarm_count - previous_month_alarm_count AS alarm_count_diff
```

如果 `previous_month_alarm_count` 是 `NULL`，那么 `alarm_count_diff` 也是 `NULL`。

如果 `previous_month_alarm_count = 0`，差值仍然可以计算。

例如：

```text
当前值 = 8
上个月值 = 0

alarm_count_diff = 8 - 0 = 8
```

---

第四步，计算增长率：

```sql
CASE
    WHEN previous_month_alarm_count IS NULL
      OR previous_month_alarm_count = 0
    THEN NULL
    ELSE ROUND(alarm_count_diff * 1.0 / previous_month_alarm_count, 2)
END AS growth_rate
```

增长率公式是：

```text
growth_rate = alarm_count_diff / previous_month_alarm_count
```

但是如果分母是 `NULL` 或者 `0`，都不能计算增长率。

所以要先排除：

```text
previous_month_alarm_count IS NULL
OR previous_month_alarm_count = 0
```

---

### 为什么 SQL 中要拆多个 CTE

本题中建议拆成三层：

```text
previous_month
join_table
diff_table
```

原因是计算链条比较清楚：

```text
previous_month：
先构造上个月同日数据。

join_table：
把当前数据和上个月数据对齐。

diff_table：
先计算 alarm_count_diff。

最终 SELECT：
再基于 alarm_count_diff 计算 growth_rate。
```

不要在同一层 SELECT 中过度引用刚定义的别名。

例如不推荐：

```sql
SELECT
    alarm_count - previous_month_alarm_count AS alarm_count_diff,
    alarm_count_diff / previous_month_alarm_count AS growth_rate
FROM ...
```

因为不同 SQL 引擎对“同一层 SELECT 中引用刚定义的别名”的支持不完全一致。

更稳妥的写法是：

```text
先在一个 CTE 中算出中间字段；
下一层再继续使用这个字段。
```

---

### Pandas 解法

```python
df_prev = (
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
    [
        [
            'device_id',
            'stat_date',
            'previous_month_alarm_count'
        ]
    ]
)

df_pd = (
    df
    .merge(
        df_prev,
        how='left',
        on=['device_id', 'stat_date']
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
    [
        [
            'device_id',
            'stat_date',
            'status',
            'alarm_count',
            'previous_month_alarm_count',
            'alarm_count_diff',
            'growth_rate',
            'growth_rate_pct'
        ]
    ]
    .sort_values(by=['device_id', 'stat_date'])
    .reset_index(drop=True)
)

df_pd
```

---

### Pandas 逻辑说明

第一步，构造上个月数据表：

```python
df_prev = (
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
```

这一步的含义是：

```text
把原始表中的日期整体向后平移 1 个自然月。
```

例如：

```text
2026-01-01
```

会变成：

```text
2026-02-01
```

这样 1 月的数据就能和 2 月的当前日期对齐。

---

第二步，只保留右表需要的字段：

```python
[
    [
        'device_id',
        'stat_date',
        'previous_month_alarm_count'
    ]
]
```

右表不需要保留 `status`。

如果右表也保留 `status`，merge 后会出现：

```text
status_x
status_y
```

这会让结果字段变乱。

因此右表只保留：

```text
device_id
stat_date
previous_month_alarm_count
```

---

第三步，合并回当前表：

```python
.merge(
    df_prev,
    how='left',
    on=['device_id', 'stat_date']
)
```

这里使用：

```text
how='left'
```

原因是：

```text
保留当前表中的所有记录。
如果没有上个月同日数据，就让 previous_month_alarm_count 为 NaN。
```

匹配键必须是：

```text
device_id + stat_date
```

不能只按 `stat_date` 合并，否则不同设备之间会互相匹配。

---

第四步，计算变化量：

```python
alarm_count_diff=lambda x: (
    x['alarm_count'] - x['previous_month_alarm_count']
)
```

如果 `previous_month_alarm_count` 是 `NaN`，那么 `alarm_count_diff` 也会是 `NaN`。

如果 `previous_month_alarm_count = 0`，差值可以正常计算。

---

第五步，计算增长率：

```python
growth_rate=lambda x: (
    (x['alarm_count_diff'] / x['previous_month_alarm_count'])
    .where(
        x['previous_month_alarm_count'].notna()
        & (x['previous_month_alarm_count'] != 0)
    )
)
```

这里使用 `.where()`，不是 `.loc[]`。

原因是：

```text
本题要求保留所有当前记录；
只是当上个月值为空或为 0 时，不计算增长率。
```

`.loc[]` 会筛选行，不符合条件的行会被删除。

`.where()` 不删除行，只控制字段值。

---

### where 的业务含义

```python
.where(condition)
```

可以理解成：

```text
条件为 True：
保留当前计算结果。

条件为 False：
变成 NaN。
```

本题的条件是：

```python
x['previous_month_alarm_count'].notna()
& (x['previous_month_alarm_count'] != 0)
```

含义是：

```text
上个月同日报警次数不是空
并且
上个月同日报警次数不等于 0
```

只有满足这个条件，增长率才有意义。

---

### diff 和 growth_rate 的区别

`alarm_count_diff` 是绝对变化量：

```text
alarm_count_diff = 当前值 - 上个月值
```

`growth_rate` 是相对变化率：

```text
growth_rate = (当前值 - 上个月值) / 上个月值
```

例如：

```text
从 10 到 15：
diff = 5
growth_rate = 50%

从 100 到 105：
diff = 5
growth_rate = 5%
```

两者的 `diff` 都是 5，但业务意义完全不同。

所以真实分析中，通常要同时看：

```text
绝对变化量
相对变化率
```

---

### 上个月值为 0 时的处理

如果：

```text
previous_month_alarm_count = 0
```

那么：

```text
alarm_count_diff 可以计算
growth_rate 不能计算
```

例如：

```text
当前值 = 8
上个月值 = 0
```

则：

```text
alarm_count_diff = 8 - 0 = 8
growth_rate = NaN
```

不能写成：

```text
增长率无限大
```

也不能写成：

```text
增长率 0%
```

更合理的业务表达是：

```text
上个月为 0，本月新增 8 次报警。
```

---

### SQL / Pandas 对应关系

| 目的 | SQL | Pandas |
|---|---|---|
| 构造上个月数据 | `stat_date + INTERVAL 1 MONTH` | `stat_date + pd.DateOffset(months=1)` |
| 合并当前表和上月表 | `LEFT JOIN` | `merge(..., how='left')` |
| 按设备和日期匹配 | `ON device_id AND stat_date` | `on=['device_id', 'stat_date']` |
| 计算差值 | `alarm_count - previous_month_alarm_count` | `alarm_count - previous_month_alarm_count` |
| 排除 NULL / NaN | `IS NULL` | `.notna()` |
| 排除 0 分母 | `= 0` | `!= 0` |
| 条件计算增长率 | `CASE WHEN ... THEN NULL ELSE ... END` | `.where(condition)` |

---

### 常见错误

#### 错误一：用 LAG / shift 取上个月同日

`LAG()` 和 `shift(1)` 取的是上一条记录。

本题要的是：

```text
上个月同日
```

这是指定时间点比较，应该使用：

```text
日期偏移 + join / merge
```

---

#### 错误二：右表保留多余字段

如果 Pandas 中右表 `df_prev` 保留了 `status`，merge 后会产生：

```text
status_x
status_y
```

所以右表只保留需要参与匹配和计算的字段：

```text
device_id
stat_date
previous_month_alarm_count
```

---

#### 错误三：用 loc 删除无效增长率行

错误写法：

```python
.loc[
    lambda x: (
        x['previous_month_alarm_count'].notna()
        & (x['previous_month_alarm_count'] != 0)
    )
]
```

这会删除没有上个月数据或上个月值为 0 的记录。

本题要求保留所有当前记录，所以应该用：

```python
.where(...)
```

---

#### 错误四：没有处理分母为 0

增长率公式中，分母是：

```text
previous_month_alarm_count
```

如果它等于 0，不能直接除。

SQL 中要写：

```sql
CASE
    WHEN previous_month_alarm_count IS NULL
      OR previous_month_alarm_count = 0
    THEN NULL
    ELSE ...
END
```

Pandas 中要写：

```python
.where(
    x['previous_month_alarm_count'].notna()
    & (x['previous_month_alarm_count'] != 0)
)
```

---

#### 错误五：没有 ORDER BY / sort_values

SQL 如果没有：

```sql
ORDER BY device_id, stat_date
```

结果显示顺序不可靠，容易误以为 `LEFT JOIN` 删除了缺失值行。

Pandas 最后也建议加：

```python
.sort_values(by=['device_id', 'stat_date'])
```

---

### 核心记忆点

```text
上个月同日不是上一条记录。
```

```text
指定时间点比较：
日期偏移 + join / merge。
```

```text
LEFT JOIN / how='left'：
保留当前表所有记录。
```

```text
diff 可以在 previous = 0 时计算。
growth_rate 不能在 previous = 0 时计算。
```

```text
loc 会删除行。
where 会保留行，只控制字段结果。
```

```text
没有比较基准，不等于基准值为 0。
```

# 综合练习 2：设备运行风险综合分析

## 一、练习名称

设备运行风险综合分析

对应文件：

```text
integrated_practice/02_device_log_join_integrated_analysis.ipynb
```

---

## 二、练习目标

本练习基于两张表：

```text
df_device：设备台账表
df_log：设备运行日志表
```

目标是生成一张设备级别的综合分析结果表，用于判断：

```text
1. 哪些设备累计报警较多；
2. 哪些设备出现过 ERROR；
3. 哪些设备存在连续 ERROR；
4. 哪些设备最近状态异常；
5. 哪些日志设备没有登记在设备台账中；
6. 哪些登记设备没有任何日志；
7. 哪些设备整体运行风险较高。
```

本题不是单一 Pattern 练习，而是一次综合分析流程训练。

最终结果要求：

```text
一行 = 一台设备
```

---

## 三、输入表

### 1. 设备台账表：df_device

字段：

```text
device_id
site
runway
device_type
model
install_date
```

字段含义：

| 字段 | 含义 |
|---|---|
| device_id | 设备编号 |
| site | 所属站点 |
| runway | 所属跑道方向 |
| device_type | 设备类型 |
| model | 设备型号 |
| install_date | 投产日期 |

---

### 2. 设备运行日志表：df_log

字段：

```text
device_id
stat_date
status
alarm_count
```

字段含义：

| 字段 | 含义 |
|---|---|
| device_id | 设备编号 |
| stat_date | 日志日期 |
| status | 当日运行状态 |
| alarm_count | 当日报警次数 |

`status` 取值：

```text
NORMAL
WARN
ERROR
```

---

## 四、最终输出字段

最终结果表字段如下：

```text
device_id
site
runway
device_type
model
has_device_info
has_log
first_log_date
latest_stat_date
latest_status
total_alarm_count
error_days
warn_days
max_consecutive_error_days
equipment_risk_score
risk_rank
risk_level
data_quality_status
```

---

## 五、字段含义与计算规则

### 1. has_device_info

表示该设备是否存在于设备台账表 `df_device` 中。

规则：

```text
如果 device_id 能在 df_device 中找到，has_device_info = True
否则 has_device_info = False
```

这个字段用于识别：

```text
日志表中出现了，但设备台账中没有登记的设备。
```

---

### 2. has_log

表示该设备是否存在运行日志。

规则：

```text
如果 device_id 能在 df_log 中找到，has_log = True
否则 has_log = False
```

这个字段用于识别：

```text
设备台账中登记了，但日志表中没有任何记录的设备。
```

---

### 3. first_log_date

设备最早一条日志日期。

规则：

```sql
MIN(stat_date)
```

按 `device_id` 分组计算。

---

### 4. latest_stat_date

设备最近一条日志日期。

规则：

```sql
MAX(stat_date)
```

按 `device_id` 分组计算。

---

### 5. latest_status

设备最近一条日志对应的状态。

不能直接使用：

```sql
MAX(status)
```

因为 `MAX(status)` 只是按字符串大小取最大值，不代表最近日期的状态。

正确做法：

```text
按 device_id 分组；
按 stat_date 降序排序；
使用 ROW_NUMBER() 取每组 rn = 1 的记录。
```

核心 SQL：

```sql
ROW_NUMBER() OVER (
    PARTITION BY device_id
    ORDER BY stat_date DESC
)
```

---

### 6. total_alarm_count

设备累计报警次数。

规则：

```sql
SUM(alarm_count)
```

按 `device_id` 分组计算。

---

### 7. error_days

设备出现 `ERROR` 的天数。

规则：

```sql
SUM(
    CASE
        WHEN status = 'ERROR' THEN 1
        ELSE 0
    END
)
```

---

### 8. warn_days

设备出现 `WARN` 的天数。

规则：

```sql
SUM(
    CASE
        WHEN status = 'WARN' THEN 1
        ELSE 0
    END
)
```

---

### 9. max_consecutive_error_days

设备最长连续 `ERROR` 天数。

本字段需要使用 Gap & Island 思路。

连续 ERROR 的要求：

```text
当前记录 status = 'ERROR'
并且日期必须自然连续
```

也就是说，不能只判断上一条是否也是 `ERROR`，还要判断：

```text
当前 ERROR 日期 = 上一条 ERROR 日期 + 1 天
```

如果中间日期断档，则必须重新开启一个 ERROR 段。

核心判断：

```sql
CASE
    WHEN is_error = TRUE
     AND (
            previous_is_error = FALSE
         OR stat_date > previous_date + INTERVAL 1 DAY
     )
    THEN 1
    ELSE 0
END AS error_start_sign
```

然后通过累计求和生成连续段编号：

```sql
SUM(error_start_sign) OVER (
    PARTITION BY device_id
    ORDER BY stat_date
) AS phase_sign
```

最后按 `device_id + phase_sign` 分组统计每段长度，再取最大值。

---

### 10. equipment_risk_score

设备运行风险分数。

计算公式：

```text
equipment_risk_score
=
total_alarm_count
+ error_days * 5
+ max_consecutive_error_days * 10
```

SQL 中要注意空值处理：

```sql
COALESCE(max_consecutive_error_days, 0)
```

否则如果设备没有 ERROR，`max_consecutive_error_days` 为空，整个风险分数会变成 `NULL`。

---

### 11. risk_rank

设备风险排名。

规则：

```text
按照 equipment_risk_score 从高到低排名。
如果分数相同，使用并列排名。
```

SQL 使用：

```sql
RANK() OVER (
    ORDER BY equipment_risk_score DESC
)
```

---

### 12. risk_level

设备风险等级。

判断顺序从上到下：

| 条件 | risk_level |
|---|---|
| has_log = False | NO_LOG |
| latest_status = 'ERROR' | HIGH |
| max_consecutive_error_days >= 2 | HIGH |
| equipment_risk_score >= 35 | HIGH |
| error_days >= 1 | MEDIUM |
| latest_status = 'WARN' | MEDIUM |
| total_alarm_count >= 10 | MEDIUM |
| 其他情况 | LOW |

SQL 写法：

```sql
CASE
    WHEN has_log = FALSE THEN 'NO_LOG'
    WHEN latest_status = 'ERROR' THEN 'HIGH'
    WHEN max_consecutive_error_days >= 2 THEN 'HIGH'
    WHEN equipment_risk_score >= 35 THEN 'HIGH'
    WHEN error_days >= 1 THEN 'MEDIUM'
    WHEN latest_status = 'WARN' THEN 'MEDIUM'
    WHEN total_alarm_count >= 10 THEN 'MEDIUM'
    ELSE 'LOW'
END AS risk_level
```

注意：

```text
CASE WHEN 会从上往下判断。
一旦命中某个条件，就返回对应结果，后面的条件不再判断。
```

---

### 13. data_quality_status

数据质量状态。

规则：

| 条件 | data_quality_status |
|---|---|
| has_device_info = False | UNKNOWN_DEVICE |
| has_log = False | NO_LOG |
| 其他情况 | OK |

SQL 写法：

```sql
CASE
    WHEN has_device_info = FALSE THEN 'UNKNOWN_DEVICE'
    WHEN has_log = FALSE THEN 'NO_LOG'
    ELSE 'OK'
END AS data_quality_status
```

---

## 六、SQL 分析流程

本练习最终结果不是一次性从原始表中直接查出来，而是通过多个中间表逐步合并。

整体流程如下：

```text
df_device + df_log
↓
all_devices：设备全集
↓
df_device_flags：has_device_info / has_log
↓
df_device_base：设备基础信息 + 标记字段
↓
df_log_summary：日志聚合指标
↓
df_latest_status：最近状态
↓
df_consecutive_error：最长连续 ERROR 天数
↓
final_base：合并所有指标
↓
risk_rank / risk_level / data_quality_status
↓
最终设备风险分析表
```

---

## 七、中间表说明

### 1. all_devices

设备全集。

来源：

```sql
SELECT device_id FROM df_device
UNION
SELECT device_id FROM df_log
```

作用：

```text
保证最终结果既包含设备台账中的设备，
也包含日志表中出现但台账中没有登记的设备。
```

不能只用 `df_device`，否则会漏掉未知设备。

不能只用 `df_log`，否则会漏掉没有日志的登记设备。

---

### 2. df_device_flags

字段：

```text
device_id
has_device_info
has_log
```

作用：

```text
判断设备是否存在台账信息；
判断设备是否存在日志记录。
```

核心方法：

```sql
EXISTS
```

理解：

```text
EXISTS 判断子查询是否查得到结果。
查得到，返回 TRUE。
查不到，返回 FALSE。
```

---

### 3. df_device_base

字段：

```text
device_id
site
runway
device_type
model
has_device_info
has_log
```

作用：

```text
作为最终结果表的骨架。
```

后续所有日志指标、连续 ERROR 指标、风险指标，都要往这张表上合并。

---

### 4. df_log_summary

字段：

```text
device_id
first_log_date
latest_stat_date
total_alarm_count
error_days
warn_days
```

作用：

```text
统计每台设备的基础日志指标。
```

核心方法：

```sql
GROUP BY device_id
MIN(stat_date)
MAX(stat_date)
SUM(alarm_count)
SUM(CASE WHEN ...)
```

---

### 5. df_latest_status

字段：

```text
device_id
latest_status
```

作用：

```text
取每台设备最近一条日志对应的状态。
```

核心方法：

```sql
ROW_NUMBER() OVER (
    PARTITION BY device_id
    ORDER BY stat_date DESC
)
```

---

### 6. df_consecutive_error

字段：

```text
device_id
max_consecutive_error_days
```

作用：

```text
计算每台设备最长连续 ERROR 天数。
```

核心方法：

```text
Gap & Island
LAG()
日期连续性判断
SUM(...) OVER(...)
GROUP BY
MAX()
```

---

### 7. final_base

作用：

```text
把所有中间表按 device_id 合并。
```

合并时必须从 `df_device_base` 出发：

```sql
FROM df_device_base AS ddb
LEFT JOIN df_log_summary AS log
    ON ddb.device_id = log.device_id
LEFT JOIN df_latest_status AS ls
    ON ddb.device_id = ls.device_id
LEFT JOIN df_consecutive_error AS dce
    ON ddb.device_id = dce.device_id
```

原因：

```text
df_device_base 是设备全集骨架。
从它出发，才能保证没有日志的设备、未知设备都不丢失。
```

---

## 八、本题涉及的核心 SQL Pattern

| 分析目标 | 使用 Pattern |
|---|---|
| 构造设备全集 | UNION |
| 判断是否存在台账 / 日志 | EXISTS |
| 聚合报警次数、ERROR 天数、WARN 天数 | GROUP BY + SUM + CASE WHEN |
| 获取最近状态 | ROW_NUMBER() |
| 识别连续 ERROR | Gap & Island |
| 判断日期是否连续 | LAG(stat_date) + INTERVAL 1 DAY |
| 合并多个中间表 | LEFT JOIN |
| 空值补 0 | COALESCE |
| 风险排名 | RANK() |
| 风险等级判断 | CASE WHEN |

---

## 九、本题关键难点

### 1. 先构造分析对象全集

综合分析不能一上来就从某一张原始表直接查。

本题的分析对象是：

```text
df_device 中登记过的设备
+
df_log 中出现过的设备
```

所以必须先构造：

```text
all_devices
```

---

### 2. GROUP BY 不会自动带出最小日期对应的其他字段

例如：

```sql
MIN(stat_date)
```

只会返回最小日期值，不会自动返回该日期对应的 `status` 或 `alarm_count`。

如果要取某个日期对应的整行，需要使用：

```sql
ROW_NUMBER()
```

---

### 3. latest_status 不能用 MAX(status)

`MAX(status)` 只是字符串比较，不代表最近日期状态。

正确方式是：

```text
按日期降序排名，取 rn = 1。
```

---

### 4. 连续 ERROR 必须判断日期是否连续

不能只看上一条是否也是 ERROR。

必须判断：

```text
当前日期是否等于上一条日期 + 1 天。
```

否则日期断档的 ERROR 会被错误地算成连续。

---

### 5. 最终合并必须以设备全集为主表

最终合并时必须从：

```text
df_device_base
```

出发。

不能从 `df_log_summary` 出发，因为它只包含有日志的设备，会漏掉 `has_log = False` 的设备。

不能从 `df_consecutive_error` 出发，因为它只包含出现过 ERROR 的设备，会漏掉从未 ERROR 的设备。

---

### 6. COALESCE 很重要

没有日志、没有 ERROR 的设备，在 LEFT JOIN 后相关指标会是 `NULL`。

需要用：

```sql
COALESCE(字段, 0)
```

把空值转成 0。

否则风险分数计算会出现：

```text
数字 + NULL = NULL
```

---

## 十、本题完成情况

当前已完成：

```text
SQL 轨道
```

暂未完成：

```text
Pandas 轨道
```

Pandas 轨道计划在后续完成第六类题型后，再作为综合复盘补写。

---

## 十一、本题收获

本题第一次完整训练了从原始数据到设备级综合分析表的流程。

相比单项 Pattern 练习，本题的重点不只是语法，而是：

```text
1. 如何确定分析对象；
2. 如何拆分中间结果；
3. 如何给每张中间表明确职责；
4. 如何把多个中间表合并成最终分析结果；
5. 如何处理数据缺失、未知设备、无日志设备；
6. 如何把技术字段转化为业务风险等级。
```

本题标志着训练从“单一 SQL 语法练习”进入到“综合业务分析流程组织”。

# 综合练习 3：用户订单行为综合分析

## 1. 练习目标

本练习模拟一个用户订单分析场景，基于用户信息表和订单明细表，生成用户级付费汇总结果表。

本练习的重点不是复杂业务分析，而是综合复用前面已经学习过的 SQL / Pandas 核心 Pattern。

本练习覆盖以下能力：

| Pattern | 本练习中的体现 |
|---|---|
| 数据清洗 | 订单状态标准化、订单去重 |
| Join / Subquery | 构造用户全集、判断用户信息是否存在、判断是否有有效支付订单 |
| Ranking | 订单去重、支付金额排名 |
| Cumulative Analysis | 累计支付金额 |
| Time Comparison | 上一笔支付日期、距离最近支付天数 |
| Gap & Island | 最长连续支付天数 |
| CASE WHEN / 条件分支 | 生成用户标签 `user_tag` |
| SQL / Pandas 对照 | 同一业务逻辑分别用 SQL 和 Pandas 实现 |

---

## 2. 数据表说明

### 2.1 用户表：`df_users`

| 字段名 | 含义 |
|---|---|
| `user_id` | 用户 ID |
| `user_name` | 用户名称 |
| `city` | 城市 |
| `register_date` | 注册日期 |
| `user_level` | 用户等级 |

### 2.2 订单表：`df_orders`

| 字段名 | 含义 |
|---|---|
| `order_id` | 订单 ID |
| `user_id` | 用户 ID |
| `order_date` | 下单日期 |
| `pay_date` | 支付日期 |
| `order_status` | 订单状态 |
| `order_amount` | 订单金额 |
| `paid_amount` | 实际支付金额 |
| `channel` | 下单渠道 |
| `updated_at` | 订单更新时间 |

---

## 3. 数据问题

原始数据中存在以下问题：

1. `order_status` 大小写不统一。
2. `order_status` 前后可能存在空格。
3. 同一个 `order_id` 可能有多条记录，需要保留最新记录。
4. 有些订单未支付、取消或退款。
5. 订单表中存在用户表没有登记的用户。
6. 用户表中存在没有任何订单的用户。
7. 有些用户没有有效支付订单。
8. 同一用户同一天可能有多笔有效支付订单。

---

## 4. 业务规则

### 4.1 订单状态标准化

订单状态统一处理为：

```sql
UPPER(TRIM(order_status)) AS normalized_status
```

Pandas 对应写法：

```python
df_orders['order_status'].str.strip().str.upper()
```

---

### 4.2 订单去重规则

同一个 `order_id` 如果出现多条记录，只保留 `updated_at` 最新的一条。

SQL 使用：

```sql
ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC
) AS rn
```

Pandas 使用：

```python
.sort_values(by=['order_id', 'updated_at'], ascending=[True, False])
.assign(
    rn=lambda x: x.groupby('order_id').cumcount() + 1
)
.loc[lambda x: x['rn'] == 1]
```

注意：

```text
这里是订单去重，目的是解决同一个 order_id 出现多条记录的问题。
```

---

### 4.3 有效支付订单规则

有效支付订单需要同时满足：

```text
normalized_status = 'PAID'
pay_date 不为空
paid_amount 不为空
```

SQL 条件：

```sql
WHERE normalized_status = 'PAID'
  AND pay_date IS NOT NULL
  AND paid_amount IS NOT NULL
```

Pandas 条件：

```python
.loc[
    lambda x: (
        (x['normalized_status'] == 'PAID')
        & (x['pay_date'].notna())
        & (x['paid_amount'].notna())
    )
]
```

---

## 5. 最终输出表

最终生成用户级汇总表：

```text
df_user_paid_summary
```

字段如下：

| 字段名 | 含义 |
|---|---|
| `user_id` | 用户 ID |
| `user_name` | 用户名称 |
| `city` | 城市 |
| `has_user_info` | 是否存在用户基础信息 |
| `has_paid_order` | 是否存在有效支付订单 |
| `paid_order_count` | 有效支付订单数量 |
| `total_paid_amount` | 累计有效支付金额 |
| `latest_paid_date` | 最近一次有效支付日期 |
| `previous_paid_date` | 最近一次有效支付日期的上一笔支付日期 |
| `days_since_latest_paid` | 距离最近一次有效支付过去多少天 |
| `max_consecutive_paid_days` | 最长连续支付天数 |
| `paid_amount_rank` | 累计支付金额排名 |
| `user_tag` | 用户标签 |

---

## 6. SQL 轨道流程

### 6.1 订单状态标准化

目标：

```text
清洗 order_status，生成 normalized_status。
```

核心 SQL：

```sql
UPPER(TRIM(order_status)) AS normalized_status
```

---

### 6.2 保留最新订单信息

目标：

```text
同一个 order_id 只保留 updated_at 最新的一条记录。
```

核心 SQL：

```sql
ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC
) AS rn
```

使用 `ROW_NUMBER()` 的原因：

```text
每个 order_id 只需要保留一条最新记录。
如果使用 RANK()，遇到并列可能会保留多行。
```

---

### 6.3 保留有效支付订单

目标：

```text
筛选真正完成支付的订单。
```

核心 SQL：

```sql
WHERE normalized_status = 'PAID'
  AND pay_date IS NOT NULL
  AND paid_amount IS NOT NULL
```

生成有效支付订单表：

```text
df_valid_paid
```

---

### 6.4 付费订单明细表

目标：

```text
在有效支付订单明细层面，计算用户内支付顺序、上一笔支付日期、支付间隔和累计支付金额。
```

核心字段：

| 字段名 | 生成方式 |
|---|---|
| `paid_order_seq` | `ROW_NUMBER()` |
| `previous_paid_date` | `LAG(pay_date)` |
| `days_from_previous_paid` | 当前支付日期 - 上一笔支付日期 |
| `running_paid_amount` | 累计支付金额 |

核心 SQL：

```sql
ROW_NUMBER() OVER (
    PARTITION BY user_id
    ORDER BY pay_date, order_id
) AS paid_order_seq
```

```sql
LAG(pay_date) OVER (
    PARTITION BY user_id
    ORDER BY pay_date, order_id
) AS previous_paid_date
```

```sql
SUM(paid_amount) OVER (
    PARTITION BY user_id
    ORDER BY pay_date, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS running_paid_amount
```

---

### 6.5 构造用户全集

目标：

```text
用户全集 = 用户表中的 user_id + 订单表中的 user_id
```

核心 SQL：

```sql
SELECT user_id
FROM df_users

UNION

SELECT user_id
FROM df_orders
```

说明：

```text
UNION 是纵向拼接，并自动去重。
这里用于得到完整用户集合。
```

---

### 6.6 判断是否存在用户信息

目标：

```text
判断每个 user_id 是否存在于 df_users 中。
```

核心 SQL：

```sql
CASE
    WHEN EXISTS (
        SELECT
            1
        FROM df_users AS u
        WHERE u.user_id = ds.user_id
    )
    THEN TRUE
    ELSE FALSE
END AS has_user_info
```

说明：

```text
EXISTS 只判断是否存在匹配记录。
如果只是判断有没有，不需要 JOIN 明细表。
```

---

### 6.7 判断是否存在有效支付订单

目标：

```text
判断每个用户是否存在有效支付订单。
```

核心 SQL：

```sql
CASE
    WHEN EXISTS (
        SELECT
            1
        FROM df_valid_paid AS vp
        WHERE vp.user_id = dub.user_id
    )
    THEN TRUE
    ELSE FALSE
END AS has_paid_order
```

注意：

```text
这里不需要直接 JOIN df_valid_paid。
因为一名用户可能有多笔有效支付订单，直接 JOIN 明细表会把用户级结果撑成多行。
```

---

### 6.8 有效支付订单数量

目标：

```text
按用户统计有效支付订单数量。
```

核心 SQL：

```sql
SELECT
    user_id,
    COUNT(*) AS paid_order_count
FROM df_valid_paid
GROUP BY user_id
```

接回用户基础表：

```sql
LEFT JOIN valid_paid_count AS vpc
    ON dub.user_id = vpc.user_id
```

空值处理：

```sql
COALESCE(vpc.paid_order_count, 0) AS paid_order_count
```

---

### 6.9 累计有效支付金额

目标：

```text
按用户统计累计有效支付金额。
```

核心 SQL：

```sql
SELECT
    user_id,
    SUM(paid_amount) AS total_paid_amount
FROM df_valid_paid
GROUP BY user_id
```

空值处理：

```sql
COALESCE(tp.total_paid_amount, 0) AS total_paid_amount
```

---

### 6.10 最近一次有效支付日期

目标：

```text
按用户取最近一次有效支付日期。
```

核心 SQL：

```sql
SELECT
    user_id,
    MAX(pay_date) AS latest_paid_date
FROM df_valid_paid
GROUP BY user_id
```

注意：

```text
这里使用 GROUP BY + MAX()。
不需要使用窗口函数 OVER()。
```

原因：

```text
目标是生成用户级汇总表，一名用户压缩成一行。
```

---

### 6.11 最近一次有效支付日期的上一笔支付日期

目标：

```text
找到每个用户最近一次支付记录对应的上一笔支付日期。
```

核心逻辑：

```text
先用 LAG() 算出每笔支付订单的上一笔支付日期。
再用 ROW_NUMBER() 找每个用户最近一笔支付订单。
最后取最近一笔订单那一行的 previous_paid_date。
```

核心 SQL：

```sql
LAG(pay_date) OVER (
    PARTITION BY user_id
    ORDER BY pay_date, order_id
) AS previous_paid_date
```

```sql
ROW_NUMBER() OVER (
    PARTITION BY user_id
    ORDER BY pay_date DESC, order_id DESC
) AS rn
```

说明：

```text
这里用 ROW_NUMBER()，不用 RANK()。
因为最终结果需要一名用户只保留一行。
```

---

### 6.12 距离最近一次有效支付的天数

目标：

```text
计算分析日期与最近一次有效支付日期之间相差多少天。
```

分析日期：

```sql
DATE '2026-07-15'
```

核心 SQL：

```sql
date_diff('day', latest_paid_date, DATE '2026-07-15') AS days_since_latest_paid
```

注意：

```text
SQL 中日期常量不要直接写 2026-07-15。
应该写成 DATE '2026-07-15'。
```

错误写法：

```sql
2026-07-15 - latest_paid_date
```

原因：

```text
SQL 可能会把 2026-07-15 理解成数字运算：
2026 - 7 - 15
```

---

### 6.13 用户最长连续支付天数

目标：

```text
计算每个用户最长连续支付天数。
```

核心方法：

```text
Gap & Island 连续区间识别。
```

分析流程：

```text
同一用户同一天支付先去重
↓
按 user_id、pay_date 排序
↓
用 LAG() 取上一笔支付日期
↓
判断当前支付日期是否开启新连续段
↓
用 SUM() OVER() 生成连续段编号
↓
按 user_id + 连续段编号统计每段连续天数
↓
再按 user_id 取最大连续天数
```

判断是否开启新连续段：

```sql
CASE
    WHEN previous_paid_date IS NULL
      OR pay_date > previous_paid_date + INTERVAL 1 DAY
    THEN 1
    ELSE 0
END AS consecutive_start_sign
```

生成连续段编号：

```sql
SUM(consecutive_start_sign) OVER (
    PARTITION BY user_id
    ORDER BY pay_date
) AS phase_sign
```

统计每段连续天数：

```sql
SELECT
    user_id,
    phase_sign,
    COUNT(*) AS consecutive_paid_days
FROM phase_table
GROUP BY user_id, phase_sign
```

取最大连续支付天数：

```sql
SELECT
    user_id,
    MAX(consecutive_paid_days) AS max_consecutive_paid_days
FROM consecutive_count
GROUP BY user_id
```

---

### 6.14 支付金额排名

目标：

```text
按照 total_paid_amount 从高到低给用户排名。
```

核心 SQL：

```sql
RANK() OVER (
    ORDER BY total_paid_amount DESC
) AS paid_amount_rank
```

说明：

```text
RANK() 是窗口函数，必须写 OVER()。
OVER() 里面的 ORDER BY 用来生成排名。
SELECT 语句最后的 ORDER BY 只控制最终结果显示顺序。
```

区别：

```text
RANK() OVER(ORDER BY total_paid_amount DESC)
= 生成排名列

ORDER BY total_paid_amount DESC
= 只控制结果表显示顺序
```

---

### 6.15 生成用户标签

目标：

```text
根据用户信息、支付行为和活跃情况生成用户标签。
```

标签规则：

| 条件 | 标签 |
|---|---|
| `has_user_info = FALSE` | `UNKNOWN_USER` |
| `has_paid_order = FALSE` | `NO_PAID` |
| `total_paid_amount >= 500 AND days_since_latest_paid <= 7` | `HIGH_VALUE_ACTIVE` |
| `total_paid_amount >= 500 AND days_since_latest_paid > 7` | `HIGH_VALUE_SILENT` |
| `paid_order_count >= 3` | `REPEAT_USER` |
| 其他 | `NORMAL_USER` |

核心 SQL：

```sql
CASE
    WHEN has_user_info = FALSE THEN 'UNKNOWN_USER'
    WHEN has_paid_order = FALSE THEN 'NO_PAID'
    WHEN total_paid_amount >= 500 AND days_since_latest_paid <= 7 THEN 'HIGH_VALUE_ACTIVE'
    WHEN total_paid_amount >= 500 AND days_since_latest_paid > 7 THEN 'HIGH_VALUE_SILENT'
    WHEN paid_order_count >= 3 THEN 'REPEAT_USER'
    ELSE 'NORMAL_USER'
END AS user_tag
```

注意：

```text
CASE WHEN 从上往下判断。
一旦命中某个条件，后面的条件不再执行。
```

因此：

```text
UNKNOWN_USER 必须放在前面。
否则订单表中存在、用户表中不存在的用户，可能会被错误标记成高价值用户或复购用户。
```

---

## 7. Pandas 轨道流程

### 7.1 订单状态标准化

SQL：

```sql
UPPER(TRIM(order_status))
```

Pandas：

```python
df_orders_clean = (
    df_orders
    .assign(
        normalized_status=lambda x: (
            x['order_status']
            .str.strip()
            .str.upper()
        )
    )
)
```

---

### 7.2 保留最新订单信息

SQL：

```sql
ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC
)
```

Pandas：

```python
df_latest_orders = (
    df_orders_clean
    .sort_values(
        by=['order_id', 'updated_at'],
        ascending=[True, False]
    )
    .assign(
        updated_at_rank=lambda x: (
            x.groupby('order_id')
            .cumcount()
            + 1
        )
    )
    .loc[lambda x: x['updated_at_rank'] == 1]
    .drop(columns='updated_at_rank')
    .reset_index(drop=True)
)
```

说明：

```text
SQL ROW_NUMBER()
对应 Pandas sort_values() + groupby().cumcount() + 1。
```

---

### 7.3 保留有效支付订单

Pandas 多条件筛选：

```python
df_valid_paid_pd = (
    df_latest_orders
    .loc[
        lambda x: (
            (x['normalized_status'] == 'PAID')
            & (x['pay_date'].notna())
            & (x['paid_amount'].notna())
        )
    ]
    .sort_values(by=['user_id', 'pay_date', 'order_id'])
    .reset_index(drop=True)
)
```

注意：

```text
多个条件之间用 &。
每个条件都要用括号包起来。
```

---

### 7.4 付费订单明细表

Pandas：

```python
df_paid_detail_pd = (
    df_valid_paid_pd
    .sort_values(by=['user_id', 'pay_date', 'order_id'])
    .assign(
        paid_order_seq=lambda x: (
            x.groupby('user_id')
            .cumcount()
            + 1
        ),
        previous_paid_date=lambda x: (
            x.groupby('user_id')['pay_date']
            .shift(1)
        ),
        days_from_previous_paid=lambda x: (
            x['pay_date'] - x['previous_paid_date']
        ).dt.days.astype('Int64'),
        running_paid_amount=lambda x: (
            x.groupby('user_id')['paid_amount']
            .cumsum()
        )
    )
    [
        [
            'order_id',
            'user_id',
            'pay_date',
            'paid_amount',
            'paid_order_seq',
            'previous_paid_date',
            'days_from_previous_paid',
            'running_paid_amount'
        ]
    ]
    .sort_values(by=['user_id', 'pay_date', 'order_id'])
    .reset_index(drop=True)
)
```

对应关系：

| SQL | Pandas |
|---|---|
| `ROW_NUMBER()` | `groupby().cumcount() + 1` |
| `LAG()` | `groupby().shift(1)` |
| `SUM() OVER(...)` | `groupby().cumsum()` |
| `date_diff()` | `(date2 - date1).dt.days` |

---

### 7.5 构造用户全集 + 判断是否存在用户信息

SQL 的 `UNION`：

```sql
SELECT user_id FROM df_users
UNION
SELECT user_id FROM df_orders
```

Pandas 对应：

```python
df_user_id_collect_pd = (
    pd.concat(
        [
            df_orders[['user_id']],
            df_users[['user_id']]
        ],
        ignore_index=True
    )
    .drop_duplicates()
    .sort_values(by='user_id')
    .reset_index(drop=True)
)
```

SQL 的 `EXISTS`：

```sql
EXISTS (
    SELECT 1
    FROM df_users AS u
    WHERE u.user_id = ds.user_id
)
```

Pandas 对应：

```python
x['user_id'].isin(df_users['user_id'])
```

完整写法：

```python
df_user_base_pd = (
    df_user_id_collect_pd
    .merge(
        df_users[['user_id', 'user_name', 'city']],
        how='left',
        on='user_id'
    )
    .assign(
        has_user_info=lambda x: (
            x['user_id'].isin(df_users['user_id'])
        )
    )
    [
        [
            'user_id',
            'user_name',
            'city',
            'has_user_info'
        ]
    ]
    .sort_values(by='user_id')
    .reset_index(drop=True)
)
```

---

### 7.6 判断是否存在有效支付订单

SQL 的 `EXISTS` 对应 Pandas 的 `isin()`：

```python
df_user_base_pd = (
    df_user_base_pd
    .assign(
        has_paid_order=lambda x: (
            x['user_id'].isin(df_valid_paid_pd['user_id'])
        )
    )
)
```

说明：

```text
isin() 表示存在。
~isin() 表示不存在。
```

---

### 7.7 有效支付订单数量

Pandas：

```python
df_paid_order_count_pd = (
    df_valid_paid_pd
    .groupby('user_id', as_index=False)
    .agg(
        paid_order_count=('order_id', 'count')
    )
)

df_user_base_pd = (
    df_user_base_pd
    .merge(
        df_paid_order_count_pd,
        how='left',
        on='user_id'
    )
    .assign(
        paid_order_count=lambda x: (
            x['paid_order_count']
            .fillna(0)
            .astype('Int64')
        )
    )
)
```

说明：

```text
groupby(..., as_index=False) 可以让分组字段保留为普通列。
这样后面 merge(on='user_id') 更清楚。
```

---

### 7.8 累计有效支付金额

Pandas：

```python
df_total_paid_amount_pd = (
    df_valid_paid_pd
    .groupby('user_id', as_index=False)
    .agg(
        total_paid_amount=('paid_amount', 'sum')
    )
)

df_user_base_pd = (
    df_user_base_pd
    .merge(
        df_total_paid_amount_pd,
        how='left',
        on='user_id'
    )
    .assign(
        total_paid_amount=lambda x: (
            x['total_paid_amount']
            .fillna(0)
            .astype('Int64')
        )
    )
)
```

---

### 7.9 最近一次有效支付日期

Pandas：

```python
df_latest_valid_paid_date_pd = (
    df_valid_paid_pd
    .groupby('user_id', as_index=False)
    .agg(
        latest_paid_date=('pay_date', 'max')
    )
)

df_user_base_pd = (
    df_user_base_pd
    .merge(
        df_latest_valid_paid_date_pd,
        how='left',
        on='user_id'
    )
)
```

说明：

```text
取每个用户最大支付日期，用 groupby + max。
不需要排序。
```

---

### 7.10 最近一次有效支付日期的上一笔支付日期

Pandas：

```python
df_user_base_pd = (
    df_valid_paid_pd
    .sort_values(by=['user_id', 'pay_date', 'order_id'])
    .assign(
        previous_paid_date=lambda x: (
            x.groupby('user_id')['pay_date']
            .shift(1)
        )
    )
    .sort_values(
        by=['user_id', 'pay_date', 'order_id'],
        ascending=[True, False, False]
    )
    .assign(
        date_rank=lambda x: (
            x.groupby('user_id')
            .cumcount()
            + 1
        )
    )
    .loc[
        lambda x: x['date_rank'] == 1,
        ['user_id', 'previous_paid_date']
    ]
    .merge(
        df_user_base_pd,
        how='right',
        on='user_id'
    )
    [
        [
            'user_id',
            'user_name',
            'city',
            'has_user_info',
            'has_paid_order',
            'paid_order_count',
            'total_paid_amount',
            'latest_paid_date',
            'previous_paid_date'
        ]
    ]
    .sort_values(by='user_id')
    .reset_index(drop=True)
)
```

注意：

```text
这里必须使用 groupby('user_id')['pay_date'].shift(1)。
不能直接 x['pay_date'].shift(1)。
```

原因：

```text
普通 shift(1) 是整张表整体向下错一行。
groupby().shift(1) 是每个用户组内向下错一行。
```

---

### 7.11 距离最近一次有效支付的天数

SQL：

```sql
date_diff('day', latest_paid_date, DATE '2026-07-15')
```

Pandas：

```python
analysis_date = pd.Timestamp('2026-07-15')

df_user_base_pd = (
    df_user_base_pd
    .assign(
        days_since_latest_paid=lambda x: (
            analysis_date - x['latest_paid_date']
        )
    )
)
```

如果希望得到整数天数：

```python
df_user_base_pd = (
    df_user_base_pd
    .assign(
        days_since_latest_paid=lambda x: (
            analysis_date - x['latest_paid_date']
        ).dt.days.astype('Int64')
    )
)
```

区别：

```text
不加 .dt.days：
结果是 Timedelta 类型，显示为 5 days、14 days。

加 .dt.days：
结果是整数天数，显示为 5、14。
```

如果保留 Timedelta 类型，后续判断要写：

```python
x['days_since_latest_paid'] <= pd.Timedelta(days=7)
```

如果转成整数天数，后续判断可以写：

```python
x['days_since_latest_paid'] <= 7
```

---

### 7.12 用户最长连续支付天数

目标：

```text
计算每个用户最长连续支付天数。
同一用户同一天多笔支付，只算 1 天。
```

Pandas：

```python
df_user_base_pd = (
    df_valid_paid_pd
    [['user_id', 'pay_date']]
    .drop_duplicates()
    .sort_values(by=['user_id', 'pay_date'])
    .assign(
        previous_pay_date=lambda x: (
            x.groupby('user_id')['pay_date']
            .shift(1)
        ),
        start_sign=lambda x: (
            (x['previous_pay_date'].isna())
            |
            (x['pay_date'] > x['previous_pay_date'] + pd.Timedelta(days=1))
        ).astype('Int64'),
        phase_sign=lambda x: (
            x.groupby('user_id')['start_sign']
            .cumsum()
        )
    )
    .groupby(['user_id', 'phase_sign'], as_index=False)
    .agg(
        paid_days_count=('pay_date', 'count')
    )
    .groupby('user_id', as_index=False)
    .agg(
        max_consecutive_paid_days=('paid_days_count', 'max')
    )
    .merge(
        df_user_base_pd,
        how='right',
        on='user_id'
    )
    .assign(
        max_consecutive_paid_days=lambda x: (
            x['max_consecutive_paid_days']
            .fillna(0)
            .astype('Int64')
        )
    )
)
```

核心逻辑：

```text
按 user_id + pay_date 去重
↓
每个用户内取上一笔支付日期
↓
判断是否开启新连续段
↓
累计生成 phase_sign
↓
按 user_id + phase_sign 统计每段连续天数
↓
按 user_id 取最大值
```

注意：

```text
这里的 drop_duplicates() 不是订单去重。
这里是支付日期去重。

订单去重：
按 order_id 去重，解决同一个订单重复记录。

支付日期去重：
按 user_id + pay_date 去重，解决同一天多笔订单不能算多天。
```

---

### 7.13 支付金额排名

SQL：

```sql
RANK() OVER (
    ORDER BY total_paid_amount DESC
)
```

Pandas：

```python
df_user_base_pd = (
    df_user_base_pd
    .assign(
        paid_amount_rank=lambda x: (
            x['total_paid_amount']
            .rank(method='min', ascending=False)
            .astype('Int64')
        )
    )
    .sort_values(by=['paid_amount_rank', 'user_id'])
    .reset_index(drop=True)
)
```

说明：

```text
rank(method='min') 对应 SQL RANK()。
rank(method='dense') 对应 SQL DENSE_RANK()。
cumcount() + 1 对应 SQL ROW_NUMBER()。
```

---

### 7.14 生成用户标签

Pandas 推荐使用 `np.select()`，对应 SQL 的 `CASE WHEN`。

如果 `days_since_latest_paid` 是 Timedelta 类型：

```python
import numpy as np

df_user_paid_summary_pd = (
    df_user_base_pd
    .assign(
        user_tag=lambda x: np.select(
            [
                x['has_user_info'] == False,
                x['has_paid_order'] == False,
                (x['total_paid_amount'] >= 500) & (x['days_since_latest_paid'] <= pd.Timedelta(days=7)),
                (x['total_paid_amount'] >= 500) & (x['days_since_latest_paid'] > pd.Timedelta(days=7)),
                x['paid_order_count'] >= 3
            ],
            [
                'UNKNOWN_USER',
                'NO_PAID',
                'HIGH_VALUE_ACTIVE',
                'HIGH_VALUE_SILENT',
                'REPEAT_USER'
            ],
            default='NORMAL_USER'
        )
    )
    .sort_values(by=['paid_amount_rank', 'user_id'])
    .reset_index(drop=True)
)
```

如果 `days_since_latest_paid` 是整数天数：

```python
import numpy as np

df_user_paid_summary_pd = (
    df_user_base_pd
    .assign(
        user_tag=lambda x: np.select(
            [
                x['has_user_info'] == False,
                x['has_paid_order'] == False,
                (x['total_paid_amount'] >= 500) & (x['days_since_latest_paid'] <= 7),
                (x['total_paid_amount'] >= 500) & (x['days_since_latest_paid'] > 7),
                x['paid_order_count'] >= 3
            ],
            [
                'UNKNOWN_USER',
                'NO_PAID',
                'HIGH_VALUE_ACTIVE',
                'HIGH_VALUE_SILENT',
                'REPEAT_USER'
            ],
            default='NORMAL_USER'
        )
    )
    .sort_values(by=['paid_amount_rank', 'user_id'])
    .reset_index(drop=True)
)
```

说明：

```text
np.select() 会从上往下判断。
先命中的条件优先返回。
```

因此：

```text
UNKNOWN_USER 和 NO_PAID 要放在前面。
```

---

## 8. SQL / Pandas 核心语法对照表

| SQL | Pandas |
|---|---|
| `UPPER(TRIM(col))` | `str.strip().str.upper()` |
| `UNION` | `pd.concat([...]).drop_duplicates()` |
| `UNION ALL` | `pd.concat([...])` |
| `LEFT JOIN` | `merge(..., how='left')` |
| `RIGHT JOIN` | `merge(..., how='right')` |
| `EXISTS` | `isin()` |
| `NOT EXISTS` | `~isin()` |
| `GROUP BY + COUNT` | `groupby().agg(... count ...)` |
| `GROUP BY + SUM` | `groupby().agg(... sum ...)` |
| `GROUP BY + MAX` | `groupby().agg(... max ...)` |
| `ROW_NUMBER()` | `sort_values() + groupby().cumcount() + 1` |
| `RANK()` | `rank(method='min')` |
| `DENSE_RANK()` | `rank(method='dense')` |
| `LAG()` | `groupby().shift(1)` |
| `SUM() OVER(...)` | `groupby().cumsum()` |
| `date_diff('day', a, b)` | `(b - a).dt.days` |
| `COALESCE(x, 0)` | `fillna(0)` |
| `CASE WHEN` | `np.select()` |

---

## 9. 易错点总结

### 9.1 Pandas 单中括号和双中括号的区别

错误写法：

```python
df_users['user_id']
```

这会得到一个 `Series`。

如果后面写：

```python
.sort_values(by='user_id')
```

会报错：

```text
TypeError: Series.sort_values() got an unexpected keyword argument 'by'
```

原因：

```text
Series 是一维数据，没有列名排序的概念，所以 Series.sort_values() 不接受 by 参数。
```

正确写法：

```python
df_users[['user_id']]
```

这会得到一个 `DataFrame`，可以继续写：

```python
.sort_values(by='user_id')
```

记忆点：

```text
df['col']     → Series
df[['col']]   → DataFrame

Series.sort_values()          → 不写 by
DataFrame.sort_values(by=...) → 要写 by
```

---

### 9.2 `rank()` 和 `cumcount()` 的区别

Pandas：

```python
rank(method='min')
```

对应 SQL：

```sql
RANK()
```

特点：

```text
允许并列名次。
后续名次会跳号。
```

Pandas：

```python
groupby().cumcount() + 1
```

对应 SQL：

```sql
ROW_NUMBER()
```

特点：

```text
强制编号。
适合每组只保留一条记录。
```

订单去重应该使用：

```text
ROW_NUMBER() / cumcount() + 1
```

不建议使用：

```text
RANK() / rank(method='min')
```

因为如果 `updated_at` 并列，`RANK()` 可能保留多行。

---

### 9.3 `GROUP BY + MAX()` 和 `MAX() OVER()` 的区别

```text
GROUP BY + MAX()
= 把多行压缩成一行，生成用户级汇总表。

MAX() OVER()
= 不压缩行，只是在每一行旁边增加窗口计算结果。
```

本练习中计算 `latest_paid_date` 应使用：

```sql
SELECT
    user_id,
    MAX(pay_date) AS latest_paid_date
FROM df_valid_paid
GROUP BY user_id
```

Pandas 对应：

```python
df_valid_paid_pd.groupby('user_id', as_index=False).agg(
    latest_paid_date=('pay_date', 'max')
)
```

---

### 9.4 `EXISTS` 不需要额外 JOIN 明细表

如果只是判断用户是否有有效支付订单：

SQL：

```sql
EXISTS (...)
```

Pandas：

```python
isin()
```

即可。

不要为了判断是否存在而直接 JOIN 明细表。

原因：

```text
一名用户可能有多笔有效支付订单。
直接 JOIN 明细表会把用户级结果撑成多行。
```

---

### 9.5 `shift(1)` 必须按用户分组

错误写法：

```python
x['pay_date'].shift(1)
```

问题：

```text
整张表整体向下错一行。
不同用户之间可能串行。
```

正确写法：

```python
x.groupby('user_id')['pay_date'].shift(1)
```

含义：

```text
每个用户内部找上一笔支付日期。
```

SQL 对应：

```sql
LAG(pay_date) OVER (
    PARTITION BY user_id
    ORDER BY pay_date
)
```

---

### 9.6 日期字段不能直接使用 `.dt.days`

错误理解：

```python
x['pay_date'].dt.days
```

问题：

```text
pay_date 是日期，不是时间差。
.dt.days 用于 Timedelta，不用于普通日期字段。
```

正确写法：

```python
(x['pay_date'] - x['previous_pay_date']).dt.days
```

或者直接用日期比较：

```python
x['pay_date'] > x['previous_pay_date'] + pd.Timedelta(days=1)
```

记忆点：

```text
日期字段：
x['pay_date'].dt.day
= 取日期是当月第几天。

时间差字段：
(x['pay_date'] - x['previous_pay_date']).dt.days
= 取两个日期相差多少天。
```

---

### 9.7 SQL 日期常量要写成 DATE 类型

推荐写法：

```sql
DATE '2026-07-15'
```

错误写法：

```sql
2026-07-15
```

原因：

```text
SQL 可能把它理解成数字运算：
2026 - 7 - 15
```

---

### 9.8 Timedelta 和整数天数的区别

Pandas 中：

```python
analysis_date - x['latest_paid_date']
```

结果是 Timedelta：

```text
5 days
14 days
NaT
```

如果加：

```python
.dt.days
```

结果是整数天数：

```text
5
14
<NA>
```

区别：

```text
Timedelta 类型：
显示更直观，但比较时要用 pd.Timedelta(days=7)。

整数天数：
更接近 SQL date_diff('day', ...)，比较时可以直接和 7 比较。
```

---

### 9.9 订单去重和支付日期去重不是一回事

订单去重：

```text
按 order_id 去重。
解决同一个订单重复记录的问题。
```

支付日期去重：

```text
按 user_id + pay_date 去重。
解决同一用户同一天多笔订单不能算多天的问题。
```

计算 `max_consecutive_paid_days` 时，应该先做支付日期去重：

```python
df_valid_paid_pd[['user_id', 'pay_date']].drop_duplicates()
```

原因：

```text
最长连续支付天数统计的是“天数”，不是“订单数”。
```

---

### 9.10 LEFT JOIN 和 RIGHT JOIN 的主表方向

这两种写法语义上可以等价：

```python
df_user_base_pd.merge(metric_table, how='left', on='user_id')
```

和：

```python
metric_table.merge(df_user_base_pd, how='right', on='user_id')
```

区别：

```text
left merge：
主表在前，补充表在后。
阅读顺序更接近“给主表加字段”。

right merge：
补充表在前，主表在后。
代码可以运行，但阅读时需要反向理解。
```

练习阶段建议：

```text
优先把用户级主表 df_user_base_pd 放前面，用 left merge。
```

---

## 10. 本练习最终能回答的问题

最终结果表可以回答：

1. 哪些用户存在于用户表？
2. 哪些用户只存在于订单表、不存在于用户表？
3. 哪些用户没有有效支付订单？
4. 每个用户有效支付了多少笔订单？
5. 每个用户累计支付金额是多少？
6. 每个用户最近一次有效支付日期是什么？
7. 每个用户最近一次有效支付日期的上一笔支付日期是什么？
8. 每个用户距离最近一次支付过去了多少天？
9. 每个用户最长连续支付天数是多少？
10. 每个用户按累计支付金额排名第几？
11. 每个用户属于哪一种标签？

---

## 11. 当前完成情况

已完成：

- SQL 轨道
- Pandas 轨道
- 订单状态标准化
- 订单去重
- 有效支付订单筛选
- 付费订单明细表
- 用户全集构造
- 用户信息存在性判断
- 有效支付订单存在性判断
- 有效支付订单数量统计
- 累计有效支付金额统计
- 最近支付日期计算
- 上一笔支付日期计算
- 距离最近支付天数计算
- 最长连续支付天数计算
- 支付金额排名
- 用户标签生成

后续可以继续补充：

- SQL / Pandas 最终结果一致性校验
- 边界条件测试
- 可视化分析
- 示例输出截图

---

## 12. 练习收获

本练习的核心收获是把前面分散学习过的 SQL / Pandas Pattern 综合起来使用。

尤其是以下能力：

```text
从业务问题拆成中间表
明确每一步的主表
判断什么时候用 JOIN
判断什么时候用 EXISTS / isin()
判断什么时候用 GROUP BY
判断什么时候用窗口函数
区分 ROW_NUMBER / RANK / DENSE_RANK
用 Gap & Island 识别连续区间
用 COALESCE / fillna 处理缺失值
用 CASE WHEN / np.select 做业务标签
```

这类题目接近真实数据分析工作的常见流程：

```text
清洗数据
↓
构造有效业务数据
↓
生成用户级主表
↓
逐步补充指标
↓
计算排名或连续区间
↓
生成业务标签
↓
输出最终分析表
```

---

## 13. Git Commit 建议

如果本练习已经完成 SQL 和 Pandas 双轨：

```bash
git add 06_integrated_practice/02_order_user_analysis.ipynb 06_integrated_practice/README.md
git commit -m "feat: complete order user integrated analysis"
git push
```

如果目录是：

```text
integrated_practice/
```

则使用：

```bash
git add integrated_practice/02_order_user_analysis.ipynb integrated_practice/README.md
git commit -m "feat: complete order user integrated analysis"
git push
```