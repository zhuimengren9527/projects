## 🛠️ SQL 基础实战：最简代码手册

### 1. 别名 (Aliasing)：给列换个名字

**场景：** 数据库里的列名叫 `name`，但你想要在结果里显示为 `first_name`。

SQL

```
-- 语法：SELECT 原始列名 AS 新名字 FROM 表名;
SELECT name AS first_name 
FROM employees;
```

- **注意：** 此时屏幕上看到的表格表头变成了 `first_name`，但数据库里的表没变，还是 `name`。
    

### 2. 去重 (DISTINCT)：只看有哪些种类

**场景：** 员工表里有 100 个人，分别来自 3 个部门。你想知道是哪 3 个部门。

- **单字段去重：**
    

SQL

```
-- 语法：SELECT DISTINCT 列名 FROM 表名;
SELECT DISTINCT dept_id 
FROM employees; 
```

- **多字段去重（重点理解）：**
    

SQL

```
-- 语法：SELECT DISTINCT 列 1, 列 2 FROM 表名;
SELECT DISTINCT dept_id, year_hired 
FROM employees;
```

> **白话解释：** 这不是去重 `dept_id` 再去重 `year_hired`。这是把它们两个**绑在一起**看。只有当两个人的“部门”和“年份”**完全一样**时，才会被合成一行。

### 3. 视图 (Views)：把代码存起来

**场景：** 你写了一段很长的查询，不想每次都重写，想给它起个名字方便以后直接调用。

SQL

```
-- 第一步：创建（存代码）
CREATE VIEW my_practice_view AS
SELECT name AS first_name, year_hired
FROM employees;

-- 第二步：调用（就像查表一样查代码）
SELECT * FROM my_practice_view;
```

### 4. 限制行数：只看前几行

**场景：** 表太大了，只想看一眼长什么样。

- **PostgreSQL (DataCamp 常用):**
    

SQL

```
SELECT * FROM employees LIMIT 2;
```

- **SQL Server:**
    

SQL

```
SELECT TOP 2 * FROM employees;
```