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