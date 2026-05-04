import heapq
from collections import Counter

class Word:
    def __init__(self, freq, word):
        # 封装：把外来数据变成“我的”属性
        self.freq = freq
        self.word = word

    def __lt__(self, other):
        """
        核心协议：定义谁是“差生”（返回 True 的人会被送往堆顶踢走）
        """
        if self.freq != other.freq:
            # 频率低的更差
            return self.freq < other.freq
        # 频率一样，字母序靠后的更差（利用 ASCII 码欺骗教官）
        return self.word > other.word

class Solution:
    def topKFrequent(self, words: list[str], k: int) -> list[str]:
        # 1. 统计频率：机器学习预处理常用的 Counter
        freq_dict = Counter(words)
        
        # 2. 维护一个大小为 k 的小顶堆
        hp = []
        
        for word, freq in freq_dict.items():
            # 实例化：把数据塞进带有“规则”的士兵身体里
            current_word = Word(freq, word)
            
            if len(hp) < k:
                heapq.heappush(hp, current_word)
            else:
                # 这里的比较会自动调用我们定义的 __lt__ 协议
                # 如果当前单词比堆顶的“差生”要强（即堆顶比当前单词“小”）
                if hp[0] < current_word: 
                    # 踢走差生，换入优等生
                    heapq.heapreplace(hp, current_word)
        
        # 3. 结果收割与物理翻转
        # 堆顶是剩下的人里最差的，所以弹出的顺序是 [差 -> 优]
        res = []
        while hp:
            res.append(heapq.heappop(hp).word)
        
        # 物理翻转：把 [差 -> 优] 变成 [优 -> 差]
        return res[::-1]