# 实体解析 (ER)：从底层语法到防御架构

## 抽屉一：兵器库 (DataCamp 基础语法)
> 认知定位：这里只记录“怎么算”，不考虑系统死活。

*   **核心工具**：`thefuzz` 库 (基于莱文斯坦编辑距离)
*   **基础语法 1：两两单挑**
    *   `fuzz.ratio("Apple", "Appel")` -> 返回两个词的相似度分数。
*   **基础语法 2：大海捞针 (工业界常用)**
    *   `process.extractOne("脏词", 标准词库列表)` -> 只返回匹配度最高的那一个和分数，带有 100 分提前熔断机制 (Early Exit)，速度极快。
    *   ⚠️ **避坑指南**：坚决不用 `extract(limit=N)`，它会触发全局排序，导致数据量大时系统卡死。

---

## 抽屉二：安检站 (工业级流水线架构)
> 认知定位：在真实业务中，不能拿着脏词直接算，必须经过三道漏斗。

*   **漏斗 1：记事本拦截 (Cache 缓存)**
    *   **逻辑**：建一个空字典 `cache = {}`。脏词来了先查字典，算过的直接返回 $O(1)$，没算过的才放行。
    *   **目的**：极大地拯救重复计算造成的 CPU 浪费。
*   **漏斗 2：高频词预热 (先验概率排序)**
    *   **逻辑**：把标准词库里最热门的词（如腾讯、阿里）排在列表最前面。
    *   **目的**：让 `extractOne` 以最快速度撞上 100 分触发熔断。
*   **漏斗 3：冷酷审判 (阈值截断 Threshold)**
    *   **逻辑**：算出来的最高分如果 `< 85` 分，直接判定为 `Unknown`。
    *   **目的**：宁可错杀，绝不放过。防止假阳性污染下游干净的数据模型。

---

## 抽屉三：防弹衣 (防御性编程与算力保护)
> 认知定位：永远假设输入的数据是有毒的，内存是有限的。

*   **防线 1：空值物理阻断**
    *   用 `pd.isna()` 提前拦截空值。如果不拦，底层的 C++ 匹配引擎遇到 NaN 会直接抛出 `TypeError`，导致千万级清洗任务中途全线崩溃。
*   **防线 2：内存撑爆防御 (LRU Cache)**
    *   **痛点**：普通字典缓存是“只进不出”的黑洞，遇到海量爬虫乱码会 OOM (内存溢出)。
    *   **解法**：使用 `@lru_cache(maxsize=100000)`。强制设定容量上限，满了自动踢出“最久未被查询”的垃圾脏词。
*   **防线 3：变量隔离 (OOP 面向对象)**
    *   将预排序的标准库和缓存字典，封装进 `class EntityResolver` 内部。避免在洗“公司名”和“城市名”时发生全局变量污染。

* **示例代码：**
```python
from thefuzz import process
import pandas as pd

# 【唯一需要记住的优化】：在外面挂一个空字典当小本子
simple_cache = {}

def clean_data_basic(dirty_word, standard_list):
    # 动作 1：遇到空值直接拒绝，防止报错
    if pd.isna(dirty_word):
        return "Unknown"
        
    # 动作 2：查小本子。算过的直接拿走，绝不算第二次
    if dirty_word in simple_cache:
        return simple_cache[dirty_word]
        
    # 动作 3：干活。只挑最高分，且必须及格 (>= 85)
    best_match, score = process.extractOne(dirty_word, standard_list)
    result = best_match if score >= 85 else "Unknown"
    
    # 动作 4：把算完的结果记入小本子
    simple_cache[dirty_word] = result
    
    return result
```
## ❓❓❓ 这就涉及到一个问题，随着数据的增多，引擎缓存会不会被撑爆?
### 会，而且一定会死得很惨。
这就是为什么必须要用 LRU Cache (最近最少使用淘汰机制) 来替代普通字典。
* **🎈如果直接把`@lru_cache`直接加在刚才写地函数上，会踩中一个及其隐蔽的“数据结构地雷”：**

    * 因为 LRU Cache 的底层本质上也是一个高级字典。字典的“键（Key）”是要缓存的函数的参数组合（即 dirty_word 和 standard_words）。在计算机物理学中，只有不可变的数据（如字符串、数字、元组）才能作为字典的键（被哈希）。而传入的 standard_words 是一个 list（列表），列表是可变的（Mutable），缓存引擎怕半路修改了列表导致缓存错乱，所以直接拒绝服务。
* **💻 工业级的终极修正方案:**

    * 为了让函数能挂上这把工业级的 LRU 锁，只需对传入的数据结构做一次极其微小的“冰冻”处理：把列表（List）变成元组（Tuple）。把活的列表（List）“冰冻”成死的元组（Tuple），同时完美解决了 Key 的哈希崩溃和 Value 的幽灵篡改！
```python
import pandas as pd
import numpy as np
from thefuzz import process
from functools import lru_cache

# ==========================================
# 静态资产区 (造轮子的地方)
# ==========================================
MASTER_BRANDS = ['Nike', 'Adidas', 'Puma', 'Under Armour', 'Lululemon']
# 在函数外部，提前完成冰冻！
FROZEN_BRANDS = tuple(MASTER_BRANDS)

# ==========================================
# 引擎制造区
# ==========================================
@lru_cache(maxsize=1000)
# 【看这里！极其重要】：给 standard_words 赋了默认值 FROZEN_BRANDS
def clean_brand_ultimate(dirty_word: str, standard_words: tuple = FROZEN_BRANDS) -> str:
    # 军规 1：拦截所有的空洞 (包含 Numpy 的 np.nan 和 Python 原生的 None)
    if pd.isna(dirty_word):
        return 'Unknown'
    
    # 军规 5：莱文斯坦距离提取与 85 分熔断
    best_match, score = process.extractOne(dirty_word, standard_words)
    return best_match if score >= 85 else 'Unknown'

# ==========================================
# 业务流水线区 (必须与函数平级，不能缩进进去！)
# ==========================================
df_challenge = pd.DataFrame({
    'user_input': ['Nike', 'Addidas', np.nan, 'Addidas', 'Lulu lemon', 'McDonalds', 'PUMA', None, 'Adibas']
})

print("🚀 开始极速清洗...")

# 【军规 4 达成】：因为我们在上面把白名单焊死成了默认参数
# 所以在这里，我们连 lambda 都不用写，连参数都不用传！
# 直接把函数的名字（指针）扔给 apply，让底层的 C 引擎以最高速狂飙！
df_challenge['cleaned_brand'] = df_challenge['user_input'].apply(clean_brand_ultimate)

print("\n✅ 终极战报：")
print(df_challenge)

# 看看 LRU 门卫到底拦截了多少次重复计算
print("\n🔍 门卫（缓存）工作报告：")
print(clean_brand_ultimate.cache_info())
```
* **✅输出结果：**

### 品牌数据清洗对账单 (Brand Cleaning Report)

| 索引 | 原始输入 (user_input) | 清洗结果 (cleaned_brand) | 状态判定                |
| :--- | :-------------------- | :----------------------- | :---------------------- |
| 0    | Nike                  | **Nike**                 | 一致                    |
| 1    | Addidas               | **Adidas**               | 拼写纠正                |
| 2    | NaN                   | *Unknown*                | 空值填充                |
| 3    | Addidas               | **Adidas**               | 重复项识别              |
| 4    | Lulu lemon            | **Lululemon**            | 格式标准化 (去空格)     |
| 5    | McDonalds             | *Unknown*                | 业务范围外过滤          |
| 6    | PUMA                  | **Puma**                 | 大小写统一 (Title Case) |
| 7    | None                  | *Unknown*                | 空值填充                |
| 8    | Adibas                | *Unknown*                | 无法识别 (模糊度过高)   |

---

### 🔍 缓存系统性能审计 (LRU Cache Report)

| 指标                | 数值      | 逻辑解读                                |
| :------------------ | :-------- | :-------------------------------------- |
| **Hits (命中)**     | `1`       | 仅 11.1% 的数据避免了重复计算，效率极低 |
| **Misses (未命中)** | `8`       | 绝大多数请求触发了底层清洗逻辑          |
| **Max Size**        | `100,000` | 内存分配过度，建议根据唯一值数量缩减    |
| **Curr Size**       | `8`       | 当前内存占用极小                        |

> **大师级提醒：** > 观察索引 1 和 3，输入完全相同。理论上，若在清洗前执行了 `.strip()`，索引 3 必然会命中缓存。当前的 `Misses=8` 说明清洗函数可能在接收参数时包含了不稳定的元数据（如 Row Index），这打破了函数的**幂等性**。建议检查代码逻辑，确保缓存 Key 的纯净。
---

## 补充：
* **🔍 第一个问题：extractOne 的输出到底长什么样？**
当执行 `process.extractOne("Addidas", ("Nike", "Adidas", "Puma"))` 时，底层引擎算完之后，会向外吐出一个元组 (Tuple)。

- 它的完整长相是这样的：
    `('Adidas', 86)`

- 第一个元素 'Adidas'，是你提供的标准词库里，长得最像的那个词（字符串）。

- 第二个元素 86，是它们俩的莱文斯坦相似度得分（整数 0-100）。

    * **代码里的魔法（解包 Unpacking）：**
        - 当写下 best_match, score = process.extractOne(...) 时，Python 执行了一个极其优雅的动作叫“解包”。
        - 它自动把元组里的第一个值 'Adidas' 塞进了变量 best_match 里；
        - 把第二个值 86 塞进了变量 score 里。

  * **所以，在这行代码之后：**

    - best_match 的值就是 'Adidas'

    - score 的值就是 86

    - 这就是为什么你下一行可以直接拿 score >= 85 来做数学审判。
* **🛡️ 第二个问题：用了 @lru_cache，就彻底不用写字典了吗？**
  
    - 绝对不用写了。一行都不用写。

    - 不仅不需要在外面声明 `simple_cache = {}`，甚至连函数里面那句 `if dirty_word in simple_cache:` 的拦截逻辑，以及 `simple_cache[dirty_word] = result` 的写入逻辑，统统可以删掉！

    - 这就是 Python 装饰器`（@）`这种“语法糖”的暴力美学。

    * **它的物理流转是这样的：**
  
        - `@lru_cache` 就像是一个站在清洗函数大门外的“带枪门卫”。这个门卫的怀里，死死抱着一个用 C 语言写成的高级字典（带有 10 万条容量限制的 `LRU 字典）`。

        - 当 Pandas 派人拿着脏词 "Addidas" 走向你的函数时，门卫会先把它拦住。

        - 门卫查自己怀里的字典。如果有，门卫直接把答案甩给 Pandas，你的清洗函数根本连运行的机会都没有（被物理阻断了，省下了 100% 的 CPU 算力）。

        - 如果门卫字典里没有，门卫才会放行，让你的 extractOne 去干苦力计算。

        - 算完之后，结果在离开大门时，门卫会自动把它抄写在自己的字典里，然后再放结果出去。
        - 
---

    * **对比代码的进化：**

        ❌ 过去（手动打理一切）：

```Python
cache = {} # 手动建字典

def clean(word, master):
    if word in cache:          # 手动查字典
        return cache[word]
        
    res, score = process.extractOne(word, master) # 干活
    final = res if score >= 85 else 'Unknown'
    
    cache[word] = final        # 手动写字典
    return final
```
✅ 现在（工业级降维）：

```Python
@lru_cache(maxsize=1000)       # 门卫接管一切
def clean(word, master):
    res, score = process.extractOne(word, master) # 只管干活！
    return res if score >= 85 else 'Unknown'
```
底层最复杂的内存调度、状态拦截、LRU 淘汰，全被封装在了那个小小的 @ 符号里。只需要专注于最纯粹的数学计算（算出分数，判定及格线）。