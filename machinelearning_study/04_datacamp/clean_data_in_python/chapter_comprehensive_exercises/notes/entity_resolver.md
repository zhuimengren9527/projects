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