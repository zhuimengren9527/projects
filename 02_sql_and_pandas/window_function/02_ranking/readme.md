# 第二章：Ranking（排名模式）

## 总结：

- **在每个分组内部进行排序，然后给每一行一个名次。**

## 这里面有三个核心函数：

- `ROW_NUMBER()`

- `RANK()`

- `DENSE_RANK()`



## 为什么需要 Ranking？

* **假设有员工工资表：**

|dept	|name	|salary|
|-------|-------|------|
|A	|张三	|10000|
|A	|李四	|8000|
|A	|王五	|7000|
|B	|赵六	|9000|
|B	|孙七	|6000|

**问：**

每个部门工资最高的人是谁？

普通的：

`ORDER BY salary DESC`

**得到的是：**

|dept	|name	|salary|
|-------|-------|------|
|A	|张三	|10000|
|B	|赵六	|9000|
|A	|李四	|8000|
|A	|王五	|7000|
|B	|孙七	|6000|



虽然排好了，但是：

* **哪一行才是每个部门第一？**

数据库不知道。

**于是：**

`ROW_NUMBER()`出现了。

例如：
```sql
SELECT
    *,
    ROW_NUMBER() OVER(
        PARTITION BY dept
        ORDER BY salary DESC
    ) AS rn
FROM employee
```
得到：

|dept	|name	|salary	|rn|
|-------|-------|-------|--|
|A	|张三	|10000	|1|
|A	|李四	|8000	|2|
|A	|王五	|7000	|3|
|B	|赵六	|9000	|1|
|B	|孙七	|6000	|2|


现在：

A部门

1
2
3

B部门

1
2


## 第一类经典题

* **每个部门工资最高的人。**

```SQL

WITH t AS (

SELECT
    *,
    ROW_NUMBER() OVER(
        PARTITION BY dept
        ORDER BY salary DESC
    ) AS rn
FROM employee

)

SELECT *
FROM t
WHERE rn = 1
```

## 第二类经典题

* **设备日志：**

|device	|time|
|-------|----|
|A	|08:00|
|A	|08:01|
|A	|08:05|
|B	|08:00|
|B	|08:10|

* **要求：**

每个设备最新一条。
```SQL
ROW_NUMBER()
OVER(
    PARTITION BY device
    ORDER BY time DESC
)
WHERE rn = 1
```

工资第一。

最新记录。

销量第一。

最近登录。

完全一样。

## 第三类经典题

* **Top N**

例如：

每个部门工资前三。

就是：

`WHERE rn <= 3`

结束。

## 今日成就 （2026-07-10）

## 02_top_n_per_group

本题练习 `Ranking Pattern` 中的 `Top N Per Group` 问题。

核心思路：

1. 按分组字段进行 `PARTITION` / `groupby`
2. 按排序字段降序排列 `ORDER BY DESC`/ `sort_values(by=,ascending=False)`
3. 使用 `ROW_NUMBER()` / `cumcount() + 1` 生成组内排名
4. 筛选 `rn <= N`,`WHERE` / `.loc[]`


**注意点：**

链式写法中，如果要用 `loc` 筛选刚刚 `assign` 出来的新列，应使用：

`.loc[lambda x: x['rn'] <= 2]`

而不是：

`.loc[df['rn'] <= 2]`

## 今日成就（2026-07-11）

### 03_rank_dense_rank_comparison

**重点：**
* **处理重复排名时：**
    - `ROW_NUMBER()` 强行为相同名次排先后。
    - `RANK()` 为重复数据排相同名次，并在后继排名中跳号
    - `DENSE_RANK()` 为重复数据排相同名次，后继名次不跳号。
* **分组排序时：**
    - `ROW_NUMBER`：可以加次级排序，因为它本来就要强行分出先后。

    - `RANK / DENSE_RANK`：如果要保留 `目标排序列` 相同就是并列，就只能按 ``目标列`` 排名，不能把 `次级排序列` 加进去破坏并列关系。

* **算轨道方法对应：**
    |目标|SQL方法|PANDAS方法|
    |----|------|----------|
    |生成强制编号	|`ROW_NUMBER()`|	`groupby('device_id').cumcount() + 1`|
    |生成普通排名，保留并列但跳号	|`RANK()`	|`rank(method='min', ascending=False)`|
    |生成密集排名，保留并列但不跳号|	`DENSE_RANK()`|	`rank(method='dense', ascending=False)`|