# ======================================================
# 题目：347. 前 K 个高频元素 (Top K Frequent Elements)
# 难度：Medium
# 核心考点：哈希表(Dict)、排序(Sort) / 堆(Heap)
# 学习日期：2026-04-14
# ======================================================

class Solution:
    def topKFrequent(self, nums: list[int], k: int) -> list[int]:
        """
        这是力扣的标准函数格式。
        我们将逻辑封装在这里，方便重复测试不同的输入。
        """
        # 1. 手动计数逻辑 
        count = {}
        for n in nums:
            count[n] = count.get(n, 0) + 1
        
        # 2. 排序逻辑 
        unique_nums = sorted(count.keys(), key=lambda x: count[x], reverse=True)
        
        # 3. 返回结果 
        return unique_nums[:k]

# ==========================================
# 下面是测试区域 (Test Bench)
# 这里的代码只有当直接运行这个文件时才会执行
# ==========================================
if __name__ == "__main__":
    # 实例化解决方案
    sol = Solution()
    
    # 测试案例 1
    test_nums = [1, 1, 1, 2, 2, 3]
    test_k = 2
    result = sol.topKFrequent(test_nums, test_k)
    
    print(f"输入: {test_nums}, k={test_k}")
    print(f"预期结果: [1, 2]")
    print(f"实际结果: {result}")
    
    # 如果你想再测一组，直接加几行就行，不用改上面的逻辑
    print("-" * 20)
    print(f"案例 2 结果: {sol.topKFrequent([1], 1)}")

    """
【留痕复盘：347. 前 K 个高频元素】

1. 核心逻辑：
   - 使用 .get() 实现了 O(N) 的频率统计。
   - 使用 lambda 表达式对字典的键进行‘按值排序’。

2. 关键感悟：
   - lambda x: count[x] 实际上是将‘待排序对象’(数字) 映射到了‘排序权重’(次数)上。
   - 这种方法在 Python 中非常简洁，但在处理海量数据（如 N 很大，k 很小）时，
     全排序 O(NlogN) 的效率不如小顶堆 O(NlogK)。

3. 机器学习联系：
   - 这是一个典型的“特征提取”逻辑。在处理自然语言（NLP）时，我们会用这种方法
     过滤掉出现频率极低的词噪声，或者选出出现频率最高的关键词。
"""