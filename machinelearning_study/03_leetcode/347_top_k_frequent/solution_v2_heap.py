class Solution:
    def topKFrequent(self,nums,k):
        import heapq
        from collections import Counter

        # 创建数字与频率字典
        freq_dict = Counter(nums)

        # 创建小顶堆数值频率元组列表
        hp = []

        # 遍历字典取数值与频率
        for num,freq in freq_dict.items():
            if len(hp) < k:
                heapq.heappush(hp, (freq, num))
            elif freq > hp[0][0]: # hp[0][0] 是目前休息室里最弱那个人的频率
                heapq.heapreplace(hp, (freq, num)) # 只有你比他强，才让你替换他

        # 取堆中元组的第二个元素并返回
        return [item[1] for item in hp]

if __name__ == '__main__':

    sol = Solution()

    test_nums = [1,1,1,2,2,3]
    test_k = 2

    result = sol.topKFrequent(test_nums,test_k)

    print(f"预期返回:[2,1]")
    print(f"实际返回值:{result}")

"""
【留痕复盘：347.前K个高频元素统计】

1.核心逻辑：
    - 使用Counter(nums)工具创建数字与频率字典。
    - 创建小顶堆数值与频率的元组列表。
    - 通过for循环拆分字典的键值对。
    - 如果列表元素未达到K个，就继续往hp中添加数值与频率元组
    - heapq.heappush会自动按元组第一个元素freq大小排列元组，将freq最小的元组排在最前面
    - 如果hp中已经有K个元素，heapq.heapreplace会将新元组按照元组的第一个元素freq和hp中的第一个元组的freq进行比较，留下freq更大的元组
    - 循环结束后，返回hp中元组的第二个元素，即数值
"""