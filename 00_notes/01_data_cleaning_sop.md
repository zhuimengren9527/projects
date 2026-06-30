# 数据清洗标准流程 (SOP) —— 缺失值处理篇
> 核心原则：拯救数据优先于处理缺失，严谨逻辑闭环。

## 第一阶段：全局扫描 (Profiling)
* **动作**：使用自动化工具或反向筛选，摸清底细。
* **目的**：确定该列缺失率，决定是“修复”还是“整列舍弃”。

## 第二阶段：规则反筛 (Filtering)
* **动作**：定义“干净数据”模式，把不符合规则的整行数据抓进 `quarantine` (隔离区)。
* **审问策略**：
    * **低基数**（种类少）：直接用 `quarantine['col'].value_counts()` 暴露脏数据全貌。
    * **高基数**（种类极多）：放弃肉眼排查。改用 `.sample(20)` 随机抽样，或 `.str.len().value_counts()` 观察长度异常分布。

## 第三阶段：底噪清除 (Noise Removal)
> 核心心法：绝不手工穷举脏数据。优先物理碾压格式，然后根据脏数据的规模，选择合适的自动化批量击杀方案。

### 1. 物理碾压（必做前置动作）
在做任何替换前，必须先清除看不见的格式错误（如多余空格），防止脏数据靠空格伪装逃脱。
```python
# 剥离首尾空格，" ? " 会现原形为 "?"
df['target_column'] = df['target_column'].str.strip()
```
### 2.精准击杀（三种实战兵器）
根据在第二阶段（隔离区）侦察到的脏数据规模，选择对应的武器：
* 兵器 A：黑名单提取法（针对脏数据种类 < 100 种）
逻辑：让代码自动从隔离区提取黑名单，然后精准替换，拒绝手工敲打。
```python
# 1. 自动提取唯一的不重复脏数据，生成列表
dirty_list = quarantine['target_column'].unique().tolist()
# 2. 闭眼批量击杀为空值
df['target_column'] = df['target_column'].replace(dirty_list, np.nan)
```
* 兵器 B：白名单反杀法（针对脏数据种类成千上万，如乱填的文本）
* 逻辑：脏数据多到无法穷举时，不再找坏人，而是只保护好人。不符合白名单的，无差别抹平。
```python
# 1. 定义白名单掩码（以纯5位数字为例）
is_good = df['target_column'].str.match(r'^\d{5}$', na=False)
# 2. 将非白名单 (~is_good) 的所有行，强行抹平为 NaN
df.loc[~is_good, 'target_column'] = np.nan
```

* 兵器 C：降维强转法（仅限纯数值型的列，如工资、年龄）
* 逻辑：利用 Pandas 的底牌 errors='coerce'，强行逼迫数据转化为数字格式。
```python
# 任何无法被解析为数字的妖魔鬼怪（字母、乱码、特殊符号），都会瞬间原地变成 NaN
df['numeric_column'] = pd.to_numeric(df['numeric_column'], errors='coerce')
```
## 第四阶段：终极处决 (Execution)
* **分类变量**：填充 `'Unknown'` 或众数。
* **数值变量**：填充中位数（稳健性高）或剔除。

## 第五阶段：闭环验收 (Validation)
* **动作**：强制断言空值为 0。
* **代码**：`assert df['col'].isnull().sum() == 0`