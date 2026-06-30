class Solution:
    def topKFrequent(self, words: list[str], k: int) -> list[str]:
        count = {}
        for word in words:
            count[word] = count.get(word,0) + 1
        unique_word = sorted(count.keys(),key=lambda x:(-count[x],x))
        return unique_word[:k]        