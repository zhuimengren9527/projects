# 🧠 算法笔记：前 K 个高频单词（堆与协议实战）

```python
import heapq
from collections import Counter

class Word:
    def __init__(self, freq, word): # 修正：这是对象的“出生”构造函数
        self.freq = freq
        self.word = word
```
## 构造函数的功能：

* 它的真正动作是将外部传入的数据，通过 self. 永久地绑定在对象身上。绑定在 self 身上，是为了让该对象的所有方法在任何时间、任何地点都能访问到这些初始数据，而不需要外部反复传递。将零散的数据（参数）转化为一个具有持久状态的实体（对象）。

* 建立私有空间：没有构造函数，对象就只是一个空壳。有了它，每个对象才有了属于自己的“内存快照”。

* 映射关系：它是为了把数据装进一个“包含属性的容器”。
```python
    def __lt__(self, other):
        # 核心：定义“谁是差生”（返回 True 的人会被推向堆顶踢走）
        if self.freq != other.freq:
            # 频率低的，是差生
            return self.freq < other.freq
        else:
            # 频率一样时，字母序靠后的（ASCII编码大），反而返回 True，被判定为“小”
            return self.word > other.word
```
## `__lt__`函数的功能与意义：

* 在 Python 中，lt 代表 Less Than（小于）
* 在__lt__函数中为对象设定一系列规则，返回True就是小于，返回False就是不小于：
    * 返回 True：正式向 Python 宣告：“我（self）确实比对方（other）小。”
    * 返回 False：宣告：“我不比对方小（即我大于或等于对方）。”

```python
class Solution:
    def topKFrequent(self, words, k):
        # 1. 统计频率
        freq_dict = Counter(words)

        # 2. 建立小顶堆
        hp = []
        for word, freq in freq_dict.items():
            # 此时往 hp 中添加的是 Word 对象，包含频率和单词两个属性的容器
            # hp = [Word对象A, Word对象B, Word对象C, ...]
            current_word = Word(freq, word)

            if len(hp) < k:
                heapq.heappush(hp, current_word)
            else:
                # 此时 hp[0] 调用函数 hp[0].__lt__(current_word) 进行比武
                if hp[0] < current_word:
                    heapq.heapreplace(hp, current_word)
        
        # 3. 收割结果
        res = []
        while hp:
            # '消耗性'循环：只要 hp 不为空，循环继续
            # heappop 将 hp 中的对象拿出来，.word 取对象中的单词名牌，存入 res
            res.append(heapq.heappop(hp).word)
            
        # 4. 物理翻转
        # 由于 hp 中最小的（最差的）在堆顶，因此 heappop 出来后是 [差 -> 优]
        # 如果要取最大的在前，就得用 [::-1] 反向取值
        return res[::-1]
```
## 知识点复盘：
🟢 对象的“容器化” (Encapsulation)
* 理解：不要零散地处理频率和单词。通过 Word 类，把它们封装成一个整体。

* 意义：数据和它的“比武规则”绑定在一起，代码更具有工程严谨性。

🟡 while hp 的“消耗性”本质
* 重点：这不是在遍历，这是在摧毁式提取。

* 理由：堆的列表本身不是全排序的，只有通过 heappop 这种物理弹出的动作，才能确保每次拿出来的都是剩下的人里“最差”的那一个。

🔴 __lt__ 的“逻辑映射”
* 真相：计算机不分好坏，只认 True/False。

* 策略：通过 word > other.word 得到 True，从而成功欺骗堆教官，把字母序靠后的“优等生逆向标记为差生”踢走。