# 第一阶段：pd.merge 逻辑深度总结
* **在这一阶段，我们完成了从“能连上就好”到“逻辑严密、防御性编程”的转变。核心要点如下：**

    * **显式化原则：**永远不要让 Pandas 猜你的意图。显式指定 on 和 how。

    * **约束验证（validate）：**这是逻辑防线。通过声明 many_to_one 等关系，利用程序崩溃来拦截数据污染。

    * **主体性思维：**以“左表”为主，优先使用 how='left'，保证业务主体的完整性。

    * **冗余管理：**当列名不一致使用 left_on/right_on 时，合并后立即清理冗余列。

    * **审计意识：**利用 indicator=True 快速定位那些没对上的“孤儿数据”。

**示例代码：工业级合并模板**


```Python
import pandas as pd

# 1. 准备数据：左表（订单），右表（产品维度表）
df_orders = pd.DataFrame({
    'order_id': [1, 2, 3, 4],
    'product_code': [101, 102, 101, 999] # 999 是系统中不存在的临时测试品
})

df_products = pd.DataFrame({
    'p_id': [101, 102, 103],
    'price': [50.0, 150.0, 3000.0]
})

# 2. 严谨的合并流程
# 我们使用 left_on 和 right_on，因为列名不统一
# 同时加入 validate 确保右表（维度表）没有重复 ID 导致订单膨胀
merged_df = (
    pd.merge(
        df_orders, 
        df_products, 
        left_on='product_code', 
        right_on='p_id', 
        how='left', 
        validate='many_to_one', 
        indicator=True
    )
    .drop(columns=['p_id']) # 移除冗余列
)

# 3. 数据审计与后续处理
# 找出哪些订单没匹配上产品
missing_products = merged_df[merged_df['_merge'] == 'left_only']
print("未匹配到产品的订单：\n", missing_products)

# 填充 NaN 以便进行严谨的统计计算
merged_df['price'] = merged_df['price'].fillna(0)

print("\n最终合并结果：")
print(merged_df)
```