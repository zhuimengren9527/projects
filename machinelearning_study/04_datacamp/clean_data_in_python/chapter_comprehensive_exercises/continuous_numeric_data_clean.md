# 🎈 连续数值型数据清洗（含单位 / 混合文本）

---

## ⚠️ 1. 为什么金额字段慎用 `value_counts()`

### 📌 问题本质

* 金额属于**连续型数据**
* 高基数（High Cardinality）

例如：

* 100 万条订单
* 可能 90 万个不同金额

```python
df['amount'].value_counts()
```

👉 结果：

* 输出极其庞大
* 无法人工识别异常值
* 性能浪费

---

### ✅ 正确思路：只关注“异常值”

#### 🔍 反向探测法（推荐）

```python
temp_parsed = pd.to_numeric(df['total_spend'], errors='coerce')

dirty_mask = temp_parsed.isna()

df_dirty = df.loc[dirty_mask, 'total_spend']
```

👉 含义：

* 无法解析为数字 → 转为 NaN
* 只筛出异常数据（文本 / 混合值）

---

## ⚠️ 2. `errors='coerce'` 的风险

### 📌 问题

以下数据会被误杀：

* `$1599.50`
* `8848元`
* `100,000.00`

👉 这些是**有效业务数据**，但包含非数字字符

---

## 🔪 3. 正确做法：结构化提取（Regex）

### 🎯 目标

将原始字段拆解为：

* 货币符号（currency）
* 数值部分（amount）

---

### 🧪 Step 1：正则提取

```python
extracted = df['monthly_fee'].astype(str).str.extract(
    r'([^\d\.\-]+)?([\d\.\-]+)'
)

extracted.columns = ['currency', 'raw_amount']
```

#### 📌 说明

* `([^\d\.\-]+)?`

  * 匹配货币符号（可选）
* `([\d\.\-]+)`

  * 匹配数字（含小数 / 负号）

---

### 🧼 Step 2：清洗货币字段

```python
extracted['currency'] = (
    extracted['currency']
    .fillna('$')
    .str.strip()
)
```

👉 注意：

* 原始数据可能包含空格
* 正则不会自动清理空白

---

### 🔢 Step 3：安全数值转换

```python
extracted['raw_amount'] = pd.to_numeric(
    extracted['raw_amount'],
    errors='coerce'
)
```

---

### 💱 Step 4：汇率统一

```python
rate_map = {
    '$': 1.0,
    '¥': 0.14
}

extracted['exchange_rate'] = (
    extracted['currency']
    .map(rate_map)
    .fillna(1.0)
)

df['amount_usd'] = (
    extracted['raw_amount'] *
    extracted['exchange_rate']
)
```

---

## ⚖️ 4. 业务规则校验

### 🚫 负值处理（示例）

```python
mask_negative = df['amount_usd'] < 0

df.loc[mask_negative, 'amount_usd'] = np.nan
```

👉 示例逻辑：

* 订阅费 < 0 → 异常数据

---

## 🧠 5. 类型优化（内存压缩）

```python
df['amount_usd'] = df['amount_usd'].astype('Float32')
```

👉 优势：

* 节省内存
* 适合大数据场景

---

## 🔧 6. 实战增强建议（重要）

### ✅ 处理千分位

```python
df['monthly_fee'] = (
    df['monthly_fee']
    .astype(str)
    .str.replace(',', '')
)
```

---

### ✅ 更稳健的正则（支持符号在前或后）

```python
r'([^\d\.\-]+)?\s*([\d,\.]+)\s*([^\d\.\-]+)?'
```

👉 可覆盖：

* `$100`
* `100元`
* `USD 100`

---

### ✅ 避免多小数点异常

```python
mask_invalid = extracted['raw_amount'].str.count(r'\.') > 1
```

---

## 🧩 总结

连续数值清洗的核心不是“转数字”，而是：

### 1️⃣ 异常识别优先

* 不看整体分布
* 只抓解析失败的数据

### 2️⃣ 保留业务信息

* 不盲目 `coerce`
* 先拆解再转换

### 3️⃣ 结构化处理

* currency + amount 分离
* 再统一标准

### 4️⃣ 最终统一

* 单位对齐（如 USD）
* 类型压缩（Float32）

---

## 📌 一句话原则

> **先识别异常 → 再结构化 → 最后数值化**

---
