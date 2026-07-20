# Pandas 缺失值识别与标准化

## 1. 练习说明

本练习属于 Pandas 专项训练中的数据清洗模块，主要训练真实业务数据中的缺失值识别、文本标准化和字段级清洗规则设计。

当前数据为模拟的设备巡检记录。由于数据可能来自人工录入或不同业务系统，同一个业务含义可能存在多种不同的原始表达。

例如，业务上都表示“缺失”的值，在原始数据中可能分别表现为：

- `None`
- 空字符串 `""`
- 纯空格 `" "`
- `"N/A"`
- `"NULL"`
- `"-"`
- `"unknown"`

其中，只有一部分会被 Pandas 自动识别为缺失值。

本练习的重点不是直接调用 `dropna()` 或 `fillna()`，而是先检查数据的原始表达，再根据各字段的业务含义制定不同的清洗规则。

---

## 2. 文件结构

```text
01_missing_value_cleaning/
├── 01_missing_value_cleaning.ipynb
└── README.md
```

文件说明：

- `01_missing_value_cleaning.ipynb`：保存数据构造、检查、清洗和验证过程。
- `README.md`：记录练习目标、分析思路、清洗规则和复盘总结。

---

## 3. 训练目标

本练习计划完成以下任务：

1. 检查原始数据的规模、字段类型和缺失情况。
2. 检查各字段中真实存在的原始表达。
3. 识别真实缺失值和伪装缺失值。
4. 清除文本字段前后的无意义空格。
5. 统一部分字段的大小写。
6. 将不同缺失标记统一转换为 Pandas 缺失值。
7. 根据字段业务含义分别采用删除、填充或保留策略。
8. 生成字段级缺失情况报告。
9. 转换数值字段和日期时间字段的数据类型。
10. 使用断言验证最终清洗结果。

---

## 4. 数据字段

| 字段 | 业务含义 | 当前类型 | 预期类型 |
|---|---|---|---|
| `record_id` | 巡检记录编号 | 整数 | 整数 |
| `device_id` | 设备编号 | 文本 | 字符串 |
| `site` | 站点编号 | 文本 | 字符串 |
| `status` | 设备状态 | 文本 | 字符串 |
| `signal_strength` | 信号强度 | 文本 | 数值 |
| `technician` | 巡检人员 | 文本 | 字符串 |
| `inspect_time` | 巡检时间 | 文本 | 日期时间 |

---

## 5. 原始数据检查思路

数据清洗之前，先通过不同的检查语句回答不同的问题。

每一个检查语句都必须具有明确目的，不能为了“多写代码”而堆积无意义的查询。

当前使用的检查逻辑为：

```text
检查数据规模
    ↓
检查字段类型和非空数量
    ↓
统计 Pandas 已识别的缺失值
    ↓
检查各字段的原始表达及出现次数
    ↓
根据检查结果制定字段级清洗规则
```

---

### 5.1 检查数据规模

```python
df_raw.shape
```

功能：

检查原始数据的行数和列数，为清洗前后的数据量对比建立基准。

通过该语句可以回答：

- 原始数据共有多少行；
- 原始数据共有多少列；
- 清洗后是否发生了行数变化。

---

### 5.2 检查数据结构

```python
df_raw.info()
```

功能：

检查各字段的数据类型、非空数量和整体数据结构，初步判断字段类型是否符合业务含义。

通过该语句可以回答：

- 每个字段当前是什么数据类型；
- 每个字段有多少个非空值；
- 哪些字段的当前类型与业务预期不一致。

例如：

- `signal_strength` 业务上应为数值类型，但当前为文本类型；
- `inspect_time` 业务上应为日期时间类型，但当前为文本类型。

这通常意味着字段中存在异常字符串，或者尚未进行类型转换。

---

### 5.3 检查 Pandas 已识别的缺失值

```python
df_raw.isna().sum()
```

功能：

统计 Pandas 当前能够直接识别的缺失值数量。

常见的真实缺失值包括：

- `None`
- `np.nan`
- `pd.NA`
- `NaT`

但是，下面这些值仍然是普通字符串，不会被 `isna()` 自动识别：

- `""`
- `" "`
- `"N/A"`
- `"NULL"`
- `"-"`
- `"unknown"`

因此，`isna().sum()` 得到的只是 Pandas 当前已经识别出的缺失数量，不一定等于真实业务缺失数量。

---

### 5.4 检查字段原始表达

```python
check_cols = [
    "device_id",
    "site",
    "status",
    "signal_strength",
    "technician"
]

for col in check_cols:
    print(f"\n===== {col} =====")
    print(df_raw[col].map(repr).value_counts())
```

功能：

检查每个重点字段中存在哪些原始表达，以及每种表达分别出现了多少次。

这段代码由三个部分组成：

```text
map()
→ 将函数应用到 Series 的每一个元素

repr()
→ 返回对象更明确的字符串表示

value_counts()
→ 统计每一种表达出现的次数
```

---

## 6. `map(repr)` 的作用

### 6.1 `map()` 的作用

`Series.map()` 会将指定函数应用到 Series 的每一个元素。

例如：

```python
s = pd.Series([1, 2, 3])

s.map(lambda x: x * 10)
```

结果为：

```text
10
20
30
```

因此：

```python
df_raw[col].map(repr)
```

表示对该字段中的每一个值调用一次 `repr()`。

---

### 6.2 `repr()` 的作用

`repr()` 是 Python 内置函数，用于返回一个对象更加明确、更加接近其内部形式的字符串表示。

普通输出可能无法清楚显示空格：

```python
print(" normal ")
```

输出时很难准确判断字符串两侧是否存在空格。

使用 `repr()`：

```python
repr(" normal ")
```

结果为：

```text
' normal '
```

引号明确显示了字符串边界，因此可以看出前后存在空格。

---

### 6.3 区分空字符串和纯空格

```python
repr("")
```

结果：

```text
''
```

表示字符串长度为零。

```python
repr(" ")
```

结果：

```text
' '
```

表示字符串中包含一个空格。

```python
repr("   ")
```

结果：

```text
'   '
```

表示字符串中包含三个空格。

这些值在普通表格输出中都可能看起来像空白，但实际上并不相同。

---

### 6.4 显示前后空格

```python
repr("normal")
```

结果：

```text
'normal'
```

```python
repr(" normal ")
```

结果：

```text
' normal '
```

因此可以发现字段中隐藏的前后空格问题。

---

### 6.5 区分字符串数字和真正数值

```python
repr("18.5")
```

结果：

```text
'18.5'
```

```python
repr(18.5)
```

结果：

```text
18.5
```

带引号的是字符串，不带引号的是数值。

这可以帮助判断 `signal_strength` 中的数值究竟是真正的数值，还是以文本形式保存的数字。

---

### 6.6 区分真实缺失值和缺失字符串

```python
repr(None)
```

结果：

```text
None
```

```python
repr("None")
```

结果：

```text
'None'
```

两者含义不同：

- `None` 是 Python 的真实空值；
- `'None'` 是普通字符串。

同理：

```python
repr(pd.NA)
```

结果：

```text
<NA>
```

而：

```python
repr("<NA>")
```

结果：

```text
'<NA>'
```

---

### 6.7 显示不可见字符

`repr()` 还可以显示换行符、制表符等不可见字符。

```python
repr("abc\ndef")
```

结果：

```text
'abc\ndef'
```

其中：

```text
\n
```

表示换行符。

```python
repr("abc\tdef")
```

结果：

```text
'abc\tdef'
```

其中：

```text
\t
```

表示制表符。

---

### 6.8 `map(repr)` 的使用边界

`map(repr)` 只用于检查数据，不用于正式清洗。

不能这样修改字段：

```python
df_clean["status"] = df_clean["status"].map(repr)
```

因为这会把原来的值全部转换为字符串表示。

例如：

```text
None
```

会变成：

```text
"None"
```

数值：

```text
18.5
```

也会变成字符串形式：

```text
"18.5"
```

因此，正确用法是临时检查：

```python
df_raw["status"].map(repr).value_counts()
```

正式清洗应使用：

```python
.str.strip()
.str.upper()
.replace()
.fillna()
.dropna()
```

---

## 7. 当前检查结论

### 7.1 `record_id`

当前情况：

- 当前为整数类型；
- 未发现明显缺失；
- 未发现格式异常；
- 可以作为每条巡检记录的唯一编号。

初步清洗判断：

- 保持原字段不变；
- 后续验证其是否存在重复值。

---

### 7.2 `device_id`

当前发现的问题：

- 存在真实缺失值；
- 部分值前后带有空格；
- 字母大小写可能不统一。

业务判断：

`device_id` 是定位巡检记录所属设备的关键字段。

如果设备编号缺失，就无法判断该条记录属于哪台设备，因此该记录通常无法继续用于设备级分析。

初步清洗规则：

- 转换为 Pandas `string` 类型；
- 去除前后空格；
- 统一转换为大写；
- 删除 `device_id` 缺失的记录。

---

### 7.3 `site`

当前发现的问题：

- 部分值前后带有空格；
- 同一站点存在大小写不同的表达；
- 例如可能同时存在 `R34`、`r34` 和 `" R34 "`。

业务判断：

大小写和前后空格不应导致同一个站点被识别为不同类别。

初步清洗规则：

- 转换为 Pandas `string` 类型；
- 去除前后空格；
- 统一转换为大写；
- 清洗后检查是否存在缺失值或异常站点编号。

---

### 7.4 `status`

当前发现的问题：

- 存在前后空格；
- 存在大小写不统一；
- 存在纯空格；
- 存在 `N/A`；
- 存在 `NULL`；
- 存在 `-`；
- 存在真实缺失值。

业务判断：

需要先统一文本格式，再识别不同形式的缺失值。

缺失状态不一定意味着整条巡检记录无效，因此不应直接删除记录。

初步清洗规则：

- 转换为 Pandas `string` 类型；
- 去除前后空格；
- 统一转换为大写；
- 将伪缺失值统一转换为 `pd.NA`；
- 将缺失状态填充为 `UNKNOWN`。

预期清洗后的有效状态包括：

```text
NORMAL
ERROR
UNKNOWN
```

---

### 7.5 `signal_strength`

当前发现的问题：

- 业务上应为数值；
- 当前以文本形式保存；
- 存在纯空格；
- 存在 `unknown`；
- 存在 `NULL`；
- 存在 `-`；
- 存在真实缺失值。

业务判断：

该字段当前混入了多种异常字符串，因此不能直接安全地转换为数值类型。

信号强度缺失可能本身就是设备异常或数据传输异常的表现，因此不能随意删除或填充。

初步清洗规则：

- 转换为 Pandas `string` 类型；
- 去除前后空格；
- 将伪缺失值统一转换为 `pd.NA`；
- 缺失值暂时保留；
- 后续使用 `pd.to_numeric()` 转换为数值类型。

---

### 7.6 `technician`

当前发现的问题：

- 存在前后空格；
- 存在空字符串；
- 存在 `N/A`；
- 存在 `NULL`；
- 存在 `-`；
- 人名大小写可能不统一。

业务判断：

巡检人员缺失不代表整条巡检记录无效，因此不应删除该记录。

初步清洗规则：

- 转换为 Pandas `string` 类型；
- 去除前后空格；
- 将伪缺失值统一转换为 `pd.NA`；
- 将缺失值填充为 `UNASSIGNED`。

人名大小写是否统一，需要根据实际业务编码规范决定，暂不直接全部转换为大写。

---

### 7.7 `inspect_time`

当前发现的问题：

- 当前以文本形式保存；
- 业务上应为日期时间类型。

业务判断：

时间字段需要转换为真正的日期时间类型，才能进行排序、时间差计算、按日期聚合等操作。

初步清洗规则：

- 使用 `pd.to_datetime()` 转换为日期时间类型；
- 对无法解析的异常时间进行检查；
- 转换后检查是否出现 `NaT`。

---

## 8. 初步清洗规则汇总

| 字段 | 格式标准化 | 缺失值处理 | 类型处理 |
|---|---|---|---|
| `record_id` | 保持不变 | 当前无须处理 | 保持整数 |
| `device_id` | 去除前后空格，统一大写 | 删除缺失设备编号的记录 | 转为 `string` |
| `site` | 去除前后空格，统一大写 | 清洗后重新检查 | 转为 `string` |
| `status` | 去除前后空格，统一大写 | 伪缺失转为 `pd.NA`，再填充为 `UNKNOWN` | 转为 `string` |
| `signal_strength` | 去除前后空格 | 伪缺失转为 `pd.NA`，缺失暂时保留 | 转为数值 |
| `technician` | 去除前后空格 | 伪缺失转为 `pd.NA`，再填充为 `UNASSIGNED` | 转为 `string` |
| `inspect_time` | 暂无大小写处理 | 转换失败值需要单独检查 | 转为日期时间 |

计划统一转换为缺失值的文本包括：

```text
""
"N/A"
"NULL"
"-"
"UNKNOWN"
```

其中，纯空格会先通过：

```python
.str.strip()
```

转换为空字符串，再通过：

```python
.replace("", pd.NA)
```

转换为真正的缺失值。

---

## 9. 缺失值处理原则

相同的缺失形式，在不同字段中不一定采用相同的处理方法。

例如：

| 字段 | 缺失值处理方式 | 原因 |
|---|---|---|
| `device_id` | 删除记录 | 无法判断记录所属设备 |
| `status` | 填充为 `UNKNOWN` | 状态未知，但记录仍可能有效 |
| `signal_strength` | 保留缺失 | 缺失本身可能具有分析价值 |
| `technician` | 填充为 `UNASSIGNED` | 巡检人员未知不代表记录无效 |

因此，缺失值处理不能简单地对整个 DataFrame 使用：

```python
df.dropna()
```

也不能对所有字段使用统一填充值。

正确逻辑是：

```text
识别缺失
    ↓
理解字段业务含义
    ↓
决定删除、填充或保留
```

---

## 10. 清洗流程设计

本练习计划采用以下处理顺序：

```text
检查原始数据
    ↓
保留原始 DataFrame
    ↓
创建清洗副本
    ↓
统一字符串类型
    ↓
清除前后空格
    ↓
统一部分字段大小写
    ↓
将伪缺失值转换为 pd.NA
    ↓
重新统计缺失情况
    ↓
生成字段级缺失报告
    ↓
根据字段业务含义处理缺失值
    ↓
转换数值和日期时间类型
    ↓
验证清洗结果
```

不能在检查原始表达之前直接修改数据。

否则可能出现以下问题：

- 没有发现所有缺失值表达；
- 不清楚某一步修改了多少数据；
- 无法解释为什么采用某种处理方式；
- 清洗后无法与原始数据进行对比；
- 不同字段被错误地采用相同处理策略。

---

## 11. 检查语句与目的对应关系

| 检查语句 | 检查目的 |
|---|---|
| `df_raw.shape` | 检查原始数据的行数和列数 |
| `df_raw.info()` | 检查字段类型、非空数量和整体结构 |
| `df_raw.isna().sum()` | 统计 Pandas 已经识别的真实缺失值 |
| `map(repr).value_counts()` | 检查原始表达及各表达出现次数 |
| `df_raw.dtypes` | 单独查看每个字段的数据类型 |
| `df_raw.head()` | 查看数据整体内容和字段排列 |

当前练习不需要无目的地增加大量查询语句。

每一个查询都应回答一个明确问题，并帮助后续制定清洗规则。

---

## 12. 当前进度

- [x] 创建练习目录
- [x] 创建 Notebook
- [x] 创建 README
- [x] 构造模拟巡检数据
- [x] 检查数据规模
- [x] 检查字段类型和非空数量
- [x] 统计 Pandas 已识别的缺失值
- [x] 检查重点字段的原始表达
- [x] 理解 `map(repr)` 的作用
- [x] 初步制定字段级清洗规则
- [ ] 创建原始数据的清洗副本
- [ ] 标准化文本字段
- [ ] 统一伪缺失值
- [ ] 生成缺失情况报告
- [ ] 按业务规则处理缺失值
- [ ] 转换数值类型
- [ ] 转换日期时间类型
- [ ] 使用断言验证清洗结果
- [ ] 完成最终复盘总结

---

## 13. 当前阶段总结

本练习当前完成了数据清洗前的检查和清洗规则设计，尚未正式执行完整清洗。

当前建立的核心流程是：

```text
检查语句
    ↓
明确检查目的
    ↓
观察字段问题
    ↓
结合业务含义制定规则
    ↓
执行清洗
    ↓
验证结果
```

目前得到的主要认识包括：

1. `isna()` 只能识别 Pandas 已知的真实缺失值，不能识别普通字符串形式的伪缺失值。
2. `map(repr)` 可以暴露空字符串、纯空格、前后空格和字符串类型数字等隐藏表达。
3. `map(repr)` 只用于检查，不应作为正式清洗方法。
4. 不同字段的缺失值具有不同业务含义，不能统一删除或统一填充。
5. 字段类型异常通常意味着字段中混入了异常字符串，或者尚未进行类型转换。
6. 数据清洗必须保留原始数据，并在副本上执行处理。
7. 每一条检查语句都应具有明确目的，并服务于后续清洗规则判断。

下一步将在 Notebook 中创建 `df_clean` 副本，并正式开始文本字段标准化。

## 14. 实际清洗过程

本次清洗始终保留原始数据 `df_raw`，所有操作均在清洗副本 `df_cleaning` 上完成。

```python
df_cleaning = df_raw.copy()
```

这样可以避免清洗过程直接修改原始数据，并方便后续对比和追溯。

---

### 14.1 定义伪缺失值

不同字段中存在多种表示缺失的字符串，需要统一转换为 Pandas 缺失值。

```python
missing_markers = {
    "": pd.NA,
    "N/A": pd.NA,
    "NULL": pd.NA,
    "-": pd.NA,
    "UNKNOWN": pd.NA
}
```

文本字段通常按照以下顺序标准化：

```text
转换为 Pandas string 类型
    ↓
删除首尾空格
    ↓
统一大小写
    ↓
将伪缺失值转换为 pd.NA
```

---

### 14.2 清洗 `device_id`

处理规则：

- 转换为 Pandas `string` 类型；
- 删除首尾空格；
- 统一转换为大写；
- 将伪缺失值转换为 `pd.NA`；
- 保存设备编号缺失的记录；
- 删除 `device_id` 缺失的整行。

```python
df_cleaning["device_id"] = (
    df_cleaning["device_id"]
    .astype("string")
    .str.strip()
    .str.upper()
    .replace(missing_markers)
)
```

删除之前，先将问题记录保存为独立 DataFrame：

```python
removed_missing_device = df_cleaning.loc[
    df_cleaning["device_id"].isna()
].copy()
```

再删除设备编号缺失的整行：

```python
df_cleaning = (
    df_cleaning
    .dropna(subset=["device_id"])
    .reset_index(drop=True)
)
```

本次共删除 1 条记录，对应原始数据中的 `record_id = 7`。

删除整行的原因是：

> `device_id` 是设备级分析的关键标识。设备编号缺失后，无法判断该条记录属于哪台设备。

被删除记录已经单独保存，可以通过 `record_id` 与原始数据对应。

---

### 14.3 清洗并验证 `site`

处理规则：

- 转换为 Pandas `string` 类型；
- 删除首尾空格；
- 统一转换为大写；
- 将伪缺失值转换为 `pd.NA`。

```python
df_cleaning["site"] = (
    df_cleaning["site"]
    .astype("string")
    .str.strip()
    .str.upper()
    .replace(missing_markers)
)
```

清洗后分别检查三类问题。

#### 缺失值检查

```python
df_cleaning["site"].isna().sum()
```

结果为 `0`，说明清洗后的站点编号不存在缺失值。

#### 格式检查

站点编号的预期格式为：

```text
R + 两位数字
```

例如：

```text
R34
R35
R38
```

检查代码：

```python
site_format_valid_mask = (
    df_cleaning["site"]
    .str.fullmatch(r"R\d{2}")
)

invalid_site_format_mask = (
    df_cleaning["site"].notna()
    & ~site_format_valid_mask
)
```

清洗后未发现格式异常的站点编号。

#### 业务合法范围检查

```python
valid_sites = {
    "R34",
    "R35",
    "R36",
    "R37",
    "R38"
}
```

只检查格式正确但不属于合法站点清单的记录：

```python
invalid_site_value_mask = (
    df_cleaning["site"].notna()
    & site_format_valid_mask
    & ~df_cleaning["site"].isin(valid_sites)
)
```

清洗后未发现不在合法清单中的站点编号。

格式检查与合法范围检查的职责不同：

| 检查 | 示例 | 含义 |
|---|---|---|
| 格式异常 | `R3A` | 编号写法不符合规则 |
| 业务范围异常 | `R99` | 格式正确，但不是合法站点 |
| 正常 | `R34` | 格式和业务范围均正确 |

---

### 14.4 清洗并验证 `status`

处理规则：

- 转换为 Pandas `string` 类型；
- 删除首尾空格；
- 统一转换为大写；
- 将伪缺失值转换为 `pd.NA`。

```python
df_cleaning["status"] = (
    df_cleaning["status"]
    .astype("string")
    .str.strip()
    .str.upper()
    .replace(missing_markers)
)
```

标准化后使用以下代码查看状态类别及数量：

```python
df_cleaning["status"].value_counts(dropna=False)
```

标准化结果：

```text
<NA>      5
NORMAL    3
ERROR     3
```

说明：

- 原始数据中的空格、`N/A`、`NULL`、`-` 和 `unknown` 已转换为缺失值；
- 非缺失状态只剩下 `NORMAL` 和 `ERROR`；
- 标准化后共识别出 5 个状态缺失值。

此时暂不立即填充缺失值，而是先保留 `pd.NA`，用于生成全表缺失报告。

---

### 14.5 清洗并验证 `signal_strength`

处理规则：

- 转换为 Pandas `string` 类型；
- 删除首尾空格；
- 统一伪缺失值；
- 转换为浮点数；
- 缺失值暂时保留。

```python
df_cleaning["signal_strength"] = (
    df_cleaning["signal_strength"]
    .astype("string")
    .str.strip()
    .str.upper()
    .replace(missing_markers)
    .astype("float")
)
```

转换后的数据类型：

```text
float64
```

使用 `describe()` 检查数值分布：

```python
df_cleaning["signal_strength"].describe()
```

结果如下：

| 统计指标 | 结果 |
|---|---:|
| 非缺失数量 | 6 |
| 平均值 | 19.20 |
| 标准差 | 1.20 |
| 最小值 | 17.80 |
| 第一四分位数 | 18.55 |
| 中位数 | 18.90 |
| 第三四分位数 | 19.70 |
| 最大值 | 21.20 |

清洗后共有：

- 6 个有效数值；
- 5 个缺失值；
- 有效值范围为 `17.8` 至 `21.2`。

由于当前没有可靠的业务上下限，因此不自行设置异常范围。

`signal_strength` 的缺失值可能本身具有业务分析价值，因此保留缺失，不删除，也不填充。

---

### 14.6 清洗并验证 `technician`

处理规则：

- 转换为 Pandas `string` 类型；
- 删除首尾空格；
- 统一转换为大写；
- 将伪缺失值转换为 `pd.NA`。

```python
df_cleaning["technician"] = (
    df_cleaning["technician"]
    .astype("string")
    .str.strip()
    .str.upper()
    .replace(missing_markers)
)
```

标准化后查看类别及数量：

```python
df_cleaning["technician"].value_counts(dropna=False)
```

结果：

```text
<NA>    4
LI      2
WANG    2
ZHAO    2
CHEN    1
```

说明：

- 姓名前后空格已经清除；
- 姓名大小写已经统一；
- 空字符串、`N/A`、`NULL` 和 `-` 已转换为缺失值；
- 标准化后共识别出 4 个缺失值。

此时先保留 `pd.NA`，等待全表缺失报告生成后再进行业务填充。

---

### 14.7 转换并验证 `inspect_time`

`inspect_time` 原始内容未发现明显格式异常，主要问题是字段类型为文本。

使用 `pd.to_datetime()` 转换：

```python
df_cleaning["inspect_time"] = pd.to_datetime(
    df_cleaning["inspect_time"],
    format="%Y-%m-%d %H:%M",
    errors="coerce"
)
```

参数说明：

- `format="%Y-%m-%d %H:%M"`：明确指定原始时间格式；
- `errors="coerce"`：无法解析的值统一转换为 `NaT`。

转换后检查类型：

```python
df_cleaning["inspect_time"].dtype
```

结果为日期时间类型：

```text
datetime64
```

检查转换失败或原始缺失数量：

```python
df_cleaning["inspect_time"].isna().sum()
```

结果为 `0`，说明所有时间均成功转换。

---

## 15. 生成缺失情况报告

所有字段完成格式标准化和伪缺失值统一后，再生成全表缺失报告。

先统计每个字段的缺失数量：

```python
missing_count = df_cleaning.isna().sum()
```

再统计每个字段的缺失比例：

```python
missing_rate = df_cleaning.isna().mean()
```

将两个结果组合为 DataFrame：

```python
missing_report = pd.DataFrame({
    "missing_count": missing_count,
    "missing_rate": missing_rate
})
```

将字段名从索引转换为普通列：

```python
missing_report = (
    missing_report
    .reset_index(names="column")
)
```

缺失比例保留四位小数，并按照缺失数量降序排列：

```python
missing_report["missing_rate"] = (
    missing_report["missing_rate"]
    .round(4)
)

missing_report = (
    missing_report
    .sort_values(
        by=["missing_count", "column"],
        ascending=[False, True]
    )
    .reset_index(drop=True)
)
```

最终缺失报告：

| column | missing_count | missing_rate |
|---|---:|---:|
| `signal_strength` | 5 | 0.4545 |
| `status` | 5 | 0.4545 |
| `technician` | 4 | 0.3636 |
| `device_id` | 0 | 0.0000 |
| `inspect_time` | 0 | 0.0000 |
| `record_id` | 0 | 0.0000 |
| `site` | 0 | 0.0000 |

该报告描述的是：

> 删除 `device_id` 缺失记录之后、业务填充之前，当前清洗表中各字段的真实缺失情况。

---

## 16. 根据业务含义处理缺失值

缺失报告生成后，再对不同字段采用不同的处理策略。

### 16.1 填充 `status`

状态缺失不代表整条记录无效，因此统一标记为 `UNKNOWN`：

```python
df_cleaning["status"] = (
    df_cleaning["status"]
    .fillna("UNKNOWN")
)
```

### 16.2 填充 `technician`

巡检人员缺失不代表巡检记录无效，因此统一标记为 `UNASSIGNED`：

```python
df_cleaning["technician"] = (
    df_cleaning["technician"]
    .fillna("UNASSIGNED")
)
```

### 16.3 保留 `signal_strength` 缺失值

`signal_strength` 缺失可能具有设备异常或数据传输异常的分析价值，因此：

```text
不删除
不填充
继续保留 NaN
```

最终缺失值处理策略如下：

| 字段 | 处理方式 | 业务原因 |
|---|---|---|
| `device_id` | 删除整行 | 无法判断记录所属设备 |
| `status` | 填充 `UNKNOWN` | 状态未知，但记录仍然有效 |
| `signal_strength` | 保留缺失 | 缺失本身可能具有分析价值 |
| `technician` | 填充 `UNASSIGNED` | 人员未知不代表记录无效 |
| `site` | 无须处理 | 清洗后不存在缺失 |
| `inspect_time` | 无须处理 | 时间全部成功转换 |

---

## 17. 最终验证

清洗完成后，使用断言将清洗规则转换为自动化验证条件。

```python
# 1. 验证数据行数
assert len(df_cleaning) == 11, \
    "清洗后数据行数不等于 11"

# 2. 验证 record_id
assert df_cleaning["record_id"].notna().all(), \
    "record_id 仍存在缺失值"

assert df_cleaning["record_id"].is_unique, \
    "record_id 存在重复值"

# 3. 验证 device_id
assert df_cleaning["device_id"].notna().all(), \
    "device_id 仍存在缺失值"

assert (
    df_cleaning["device_id"]
    .str.fullmatch(r"R\d{2}-\d{2}")
    .all()
), "device_id 存在格式异常"

# 4. 验证 site
valid_sites = {"R34", "R35", "R36", "R37", "R38"}

assert df_cleaning["site"].notna().all(), \
    "site 仍存在缺失值"

assert (
    df_cleaning["site"]
    .str.fullmatch(r"R\d{2}")
    .all()
), "site 存在格式异常"

assert (
    df_cleaning["site"]
    .isin(valid_sites)
    .all()
), "site 存在不在合法清单中的编号"

# 5. 验证 status
valid_statuses = {"NORMAL", "ERROR", "UNKNOWN"}

assert df_cleaning["status"].notna().all(), \
    "status 仍存在缺失值"

assert (
    df_cleaning["status"]
    .isin(valid_statuses)
    .all()
), "status 存在未预期的状态值"

# 6. 验证 signal_strength
assert pd.api.types.is_float_dtype(
    df_cleaning["signal_strength"]
), "signal_strength 不是浮点数类型"

assert (
    df_cleaning["signal_strength"].isna().sum() == 5
), "signal_strength 缺失数量不等于 5"

# 7. 验证 technician
assert df_cleaning["technician"].notna().all(), \
    "technician 仍存在缺失值"

# 8. 验证 inspect_time
assert pd.api.types.is_datetime64_any_dtype(
    df_cleaning["inspect_time"]
), "inspect_time 不是日期时间类型"

assert df_cleaning["inspect_time"].notna().all(), \
    "inspect_time 存在转换失败或缺失值"

print("所有清洗规则验证通过。")
```

---

### 17.1 验证删除记录的可追溯性

```python
assert len(removed_missing_device) == 1, \
    "因 device_id 缺失而删除的记录数量异常"

assert removed_missing_device["device_id"].isna().all(), \
    "被删除记录中存在非缺失的 device_id"

assert (
    len(df_cleaning) + len(removed_missing_device)
    == len(df_raw)
), "清洗结果无法完整对应原始数据"
```

进一步验证所有记录编号均可追溯：

```python
cleaned_record_ids = set(df_cleaning["record_id"])
removed_record_ids = set(removed_missing_device["record_id"])
raw_record_ids = set(df_raw["record_id"])

assert (
    cleaned_record_ids | removed_record_ids
    == raw_record_ids
), "清洗过程中存在记录丢失或新增"

print("删除记录与原始数据的对应关系验证通过。")
```

该验证证明：

```text
保留的记录
+
被删除的记录
=
全部原始记录
```

---

## 18. 最终清洗结果

原始数据共有 12 条记录。

由于其中 1 条记录缺少 `device_id`，最终清洗结果保留 11 条有效记录。

清洗完成后：

- `record_id` 无缺失、无重复；
- `device_id` 无缺失，格式统一为 `Rxx-xx`；
- `site` 无缺失，格式统一为 `Rxx`；
- `status` 无缺失，只包含 `NORMAL`、`ERROR` 和 `UNKNOWN`；
- `signal_strength` 已转换为 `float64`，保留 5 个缺失值；
- `technician` 无缺失，原缺失值填充为 `UNASSIGNED`；
- `inspect_time` 已转换为日期时间类型，无转换失败；
- 被删除记录已单独保存，可以通过 `record_id` 追溯到原始数据。

---

## 19. 关键方法总结

| 方法 | 本次练习中的作用 |
|---|---|
| `.copy()` | 创建独立清洗副本或保存待删除记录 |
| `.astype("string")` | 转换为 Pandas 可空字符串类型 |
| `.str.strip()` | 删除字符串首尾空白字符 |
| `.str.upper()` | 统一文本大小写 |
| `.replace()` | 将伪缺失值统一转换为 `pd.NA` |
| `.isna()` | 判断缺失值 |
| `.notna()` | 判断非缺失值 |
| `.dropna(subset=...)` | 根据指定字段删除缺失记录 |
| `.fillna()` | 根据业务规则填充缺失值 |
| `.value_counts(dropna=False)` | 查看类别字段的类别及数量 |
| `.describe()` | 查看数值字段的统计分布 |
| `.str.fullmatch()` | 检查字符串是否完全符合规定格式 |
| `.isin()` | 检查值是否属于合法业务范围 |
| `pd.to_datetime()` | 转换日期时间字段 |
| `assert` | 自动验证清洗结果是否符合规则 |

---

## 20. 本次练习复盘

本次练习建立了完整的缺失值清洗流程：

```text
检查原始表达
    ↓
建立字段级清洗规则
    ↓
保留原始数据
    ↓
创建清洗副本
    ↓
标准化文本格式
    ↓
统一伪缺失值
    ↓
检查类别、类型和数值分布
    ↓
生成全表缺失报告
    ↓
根据业务含义处理缺失值
    ↓
使用断言验证最终结果
```

本次练习得到的主要认识：

1. 数据清洗中的每个查询都应具有明确目的。
2. `isna()` 只能识别真正的缺失值，不能自动识别普通字符串形式的伪缺失值。
3. 不同字段即使都存在缺失，也不能采用相同的处理方式。
4. 删除记录属于破坏性操作，应提前保存被删除记录并保留追溯依据。
5. 类别字段适合使用 `value_counts()` 检查，连续数值字段更适合使用 `describe()`。
6. 格式正确不代表业务值一定合法，需要区分格式规则和合法范围。
7. 缺失报告应在伪缺失值标准化之后、业务填充之前生成。
8. 最终验证不应只依赖肉眼查看，而应使用断言将规则自动化。
9. `record_id` 用于追溯原始记录，DataFrame 索引只表示当前行位置。
10. 链式写法不是越短越好，当前阶段优先保证每一步逻辑清楚。

---

## 21. 完成进度

- [x] 创建练习目录
- [x] 构造模拟巡检数据
- [x] 检查原始数据结构
- [x] 检查字段原始表达
- [x] 制定字段级清洗规则
- [x] 创建清洗副本
- [x] 清洗 `device_id`
- [x] 保存并删除关键字段缺失记录
- [x] 清洗并验证 `site`
- [x] 清洗并验证 `status`
- [x] 清洗并验证 `signal_strength`
- [x] 清洗并验证 `technician`
- [x] 转换并验证 `inspect_time`
- [x] 生成字段级缺失报告
- [x] 根据业务含义处理缺失值
- [x] 使用断言验证最终结果
- [x] 验证删除记录的可追溯性
- [x] 完成本次练习复盘