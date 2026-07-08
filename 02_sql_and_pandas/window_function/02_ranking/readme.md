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


