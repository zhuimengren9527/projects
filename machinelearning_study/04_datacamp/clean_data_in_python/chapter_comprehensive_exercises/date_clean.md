# 📅 日期数据清洗：启发式解析 vs 确定性解析

---

## 🔍 流派一：启发式解析（Heuristic Parsing）

### 📌 核心逻辑

* 不指定 `format`
* 依赖 Pandas 内置规则自动推断格式

```python id="2m8gqk"
pd.to_datetime(df['date'])
pd.to_datetime(df['date'], format='mixed')
```

---

### 👍 优点

* 兼容性强：

  * `2023-01-01`
  * `2023/1/1`
  * `Jan 1st 2023`
  * `2023年1月1日`
* 适合快速处理混乱数据

---

### ⚠️ 风险

#### 1. 不可控（核心问题）

* 存在歧义：

  * `11/12/2023`

    * 可能是：11月12日（美式）
    * 可能是：12月11日（欧式）

* 默认行为：

  * 倾向按美式解析（month-first）

---

#### 2. 性能较低

* 每条数据需进行规则推断
* 比指定 format 慢（数量级差异）

---

### 📍 使用场景

* EDA（探索阶段）
* 一次性数据处理
* 临时分析任务

---

## 🛡️ 流派二：确定性解析（Deterministic Parsing）

### 📌 核心逻辑

* 显式指定格式
* 严格匹配

```python id="b9b6fy"
pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
```

---

### 👍 优点

#### 1. 可控性强

* 解析结果完全确定
* 不存在隐式猜测

---

#### 2. 性能高

* 直接调用底层 `strptime`
* 适合大规模数据

---

### ⚠️ 缺点

* 需要提前了解数据格式
* 需要编写多层规则

---

### 📍 使用场景

* 生产环境
* 自动化数据管道
* 定时任务（ETL / Batch）

---

## 🏗️ 标准工程方案：瀑布流解析（多阶段）

---

### 🕵️ 第一阶段：数据探查（Profiling）

```python id="c6s4hf"
df['signup_date'].value_counts()
```

或：

* 抽样分析
* 统计格式分布

---

### 🎯 目标

识别主要格式占比：

| 格式       | 占比 |
| ---------- | ---- |
| `%Y-%m-%d` | 85%  |
| `%Y/%m/%d` | 10%  |
| `%d-%m-%Y` | 4.9% |
| 其他       | 0.1% |

---

## 🏗️ 第二阶段：规则构建（瀑布流）

### 📌 核心原则

* 按**数据占比从高到低**解析
* 每一步只处理“剩余未解析数据”

---

### 🧪 示例代码

```python id="m3j9ls"
# Step 1: 主格式
df['parsed_date'] = pd.to_datetime(
    df['signup_date'],
    format='%Y-%m-%d',
    errors='coerce'
)

# Step 2: 处理斜杠格式
mask = df['parsed_date'].isna()

df.loc[mask, 'parsed_date'] = pd.to_datetime(
    df.loc[mask, 'signup_date'],
    format='%Y/%m/%d',
    errors='coerce'
)

# Step 3: 处理日-月-年格式
mask = df['parsed_date'].isna()

df.loc[mask, 'parsed_date'] = pd.to_datetime(
    df.loc[mask, 'signup_date'],
    format='%d/%m/%Y',
    errors='coerce'
)

# Step 4: 点分隔格式
mask = df['parsed_date'].isna()

df.loc[mask, 'parsed_date'] = pd.to_datetime(
    df.loc[mask, 'signup_date'],
    format='%Y.%m.%d',
    errors='coerce'
)

# Step 5: 含时间格式
mask = df['parsed_date'].isna()

df.loc[mask, 'parsed_date'] = pd.to_datetime(
    df.loc[mask, 'signup_date'],
    format='%Y-%m-%d %H:%M:%S',
    errors='coerce'
)
```

---

## ⚖️ 第三阶段：业务规则校验

### 🚫 异常年份处理

```python id="u2dr6k"
mask = df['parsed_date'].dt.year < 1999

df.loc[mask, 'parsed_date'] = np.nan
```

---

### 🕛 时间归一化

```python id="vv2x1q"
df['parsed_date'] = df['parsed_date'].dt.normalize()
```

---

## 🧠 关键工程原则

### 1️⃣ 数据驱动开发

* 所有规则来自数据分布
* 不凭经验硬写逻辑

---

### 2️⃣ 优先级排序

* 高频格式优先处理
* 降低整体计算成本

---

### 3️⃣ 控制复杂度

* 不为极端长尾数据过度优化
* 接受少量 NaT

---

## 🔧 实战优化补充（重要）

### ✅ 指定 dayfirst（避免歧义）

```python id="q6yq3o"
pd.to_datetime(df['date'], dayfirst=True)
```

---

### ✅ cache 加速

```python id="oz7tqg"
pd.to_datetime(df['date'], cache=True)
```

👉 对重复值多的数据效果明显

---

### ✅ 避免重复计算

```python id="q3j9mz"
mask = df['parsed_date'].isna()
```

👉 每一步必须刷新 mask

---

### ✅ 提前标准化字符串（推荐）

```python id="l2d5yk"
df['signup_date'] = (
    df['signup_date']
    .astype(str)
    .str.strip()
)
```

---

## 📌 一句话总结

> **探索阶段用“猜”，生产环境用“控”**

---
