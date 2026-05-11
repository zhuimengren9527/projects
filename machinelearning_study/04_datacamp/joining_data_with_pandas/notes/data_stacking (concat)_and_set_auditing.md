## 1. `pd.concat`：不仅仅是简单的堆叠

从严谨的工程角度看，`concat` 是最容易导致 **Schema（模式）污染** 的地方。

### 核心逻辑：对齐（Alignment）

`pd.concat` 的核心逻辑是：**根据列名对齐。**

#### 逻辑漏洞：隐性列漂移

假设有两张表：

- **1月数据**：列名是 `['date', 'sales', 'user_id']`
    
- **2月数据**：列名是 `['Date', 'Sales', 'User_ID']` (开发者换了命名习惯)
    

如果直接 `pd.concat([df1, df2])`，Pandas 不会报错，它会生成一个拥有 **6 列** 的怪胎表，且每一行都有一半是 `NaN`。

**大师级准则：** 在 `concat` 之前，永远执行一次列名对齐检查。

Python

```
# 快速检查列名是否完全一致
if not df1.columns.equals(df2.columns):
    print("警告：列名不匹配！合并后会产生冗余列。")
    # 此时应该先处理列名，再合并
```

---

## 2. 索引的“二次伤害”

这是 `concat` 中最经典的问题：**索引重复**。

Python

```
import pandas as pd

df1 = pd.DataFrame({'val': [1, 2]}, index=[0, 1])
df2 = pd.DataFrame({'val': [3, 4]}, index=[0, 1])

res = pd.concat([df1, df2])
print(res.index) 
# 结果会是 [0, 1, 0, 1]
```

**为什么这是地雷？** 当尝试 `res.loc[0]` 时，预期得到一行，结果返回了两行。这会让后续所有的基于索引的计算全部失效。

**解决方案：**

- **方案 A**：`ignore_index=True`。如果不在乎原始索引，直接洗牌重排。
    
- **方案 B**：使用 `keys` 参数创建多级索引（MultiIndex）。这是**可追溯性**的专业写法。
    
    Python
    
    ```
    # 这样你可以通过 res.loc['Jan'] 轻松找回一月份的数据
    res = pd.concat([df_jan, df_feb], keys=['Jan', 'Feb'])
    ```
    

---

## 3. 数据审计：找出“对不上”的数据

 `how='left'` 会产生 `NaN`。要主动利用这种“不对称”来做数据审计。

### 反连接（Anti-join）的逻辑实现

场景：有 `全量学生表` 和 `已缴费学生表`，想找出 **“还没缴费的学生”**。

这在 Pandas 中没有直接的 `anti_join` 函数，需要用逻辑组合：

Python

```
# 方案：利用 indicator 参数定位
audit = pd.merge(all_students, paid_students, on='student_id', how='left', indicator=True)

# 过滤出只在左表（all_students）中存在的数据
unpaid = audit[audit['_merge'] == 'left_only']
```

---

## 4. 深度思考：Concat 的 Axis 维度

`pd.concat` 其实也可以横向拼接（`axis=1`），这听起来和 `join` 很像。

**它们的本质区别是什么？**

- **`join/merge`**：是根据内容（值）去寻找对应关系。
    
- **`pd.concat(axis=1)`**：是机械地根据位置（或索引）去硬碰硬。
    

> **批判性思维：** 除非百分之百确定两张表的行顺序完全一致且没有任何缺失，否则**永远不要**使用 `pd.concat(axis=1)` 来合并业务数据。