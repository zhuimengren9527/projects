import heapq
from collections import Counter

class Word:
    """
    自定义包装类：用来定义我们自己的“比武规则”。
    小顶堆（heapq）永远会踢走“最小（最差）”的对象。
    """
    def __init__(self, freq, word):
        self.freq = freq
        self.word = word

    def __lt__(self, other):
        # 规则 1：如果频率不同，频率小的就是“差生”（返回 True）
        if self.freq != other.freq:
            return self.freq < other.freq
        
        # 规则 2：如果频率相同，字母序靠后的（比如 'banana'）反而是“差生”。
        # 我们告诉计算机：'banana' > 'apple' 结果为 True，
        # 也就是让计算机认为 'banana' 才是那个“小”的。
        return self.word > other.word

class Solution:
    def topKFrequent(self, words: list[str], k: int) -> list[str]:
        # 1. 统计频率：建立单词到频率的映射
        freq_dict = Counter(words)
        
        # 2. 建立小顶堆：堆里只放 K 个最强的“优等生”
        hp = []
        
        for word, freq in freq_dict.items():
            # 实例化我们的自定义 Word 对象
            current_word = Word(freq, word)
            
            if len(hp) < k:
                # 堆还没满，直接进场排队
                heapq.heappush(hp, current_word)
            else:
                # 堆满了，让新来的和堆顶最差的那个（hp[0]）比武。
                # 注意：这里会自动调用 Word 类的 __lt__ 方法进行比较。
                if current_word.word > hp[0].word if current_word.freq == hp[0].freq else current_word.freq > hp[0].freq:
                    # 如果新来的更强，就踢走堆顶的差生，换新生入场
                    # heappushpop 或 heapreplace 都会让堆重新排队
                    heapq.heapreplace(hp, current_word)
        
        # 3. 收割结果：此时堆里剩下的 K 个就是最强的。
        # 但正如你所说，堆顶（左边）是这 K 个里最差的，最好的在右边。
        res = []
        while hp:
            # 每次弹出堆顶（目前最差的一个），依次放入结果列表
            res.append(heapq.heappop(hp).word)
            
        # 4. 物理翻转：
        # 因为 heappop 是从小到大弹出的（差生先出来），
        # 结果是 [差, 中, 优]，我们要的是 [优, 中, 差]，所以必须翻转。
        return res[::-1]

# --- 测试部分 ---
if __name__ == "__main__":
    sol = Solution()
    test_words = ["the", "day", "is", "sunny", "the", "the", "the", "sunny", "is", "is"]
    k = 4
    
    # 执行
    result = sol.topKFrequent(test_words, k)
    
    print(f"输入数据: {test_words}")
    print(f"预期结果: ['the', 'is', 'sunny', 'day']")
    print(f"实际结果: {result}")


