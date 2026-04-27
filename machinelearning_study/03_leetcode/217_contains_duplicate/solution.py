class Solution:
    # 方法1：哈希表法 (时间 O(n), 空间 O(n))
    def containsDuplicate_v1(self, nums: list[int]) -> bool:
        count = {}
        for n in nums:
            if n in count: return True
            count[n] = 1
        return False

    # 方法2：集合长度法 (代码最简洁)
    def containsDuplicate_v2(self, nums: list[int]) -> bool:
        return len(set(nums)) < len(nums)

# 测试代码
if __name__ == '__main__':
    sol = Solution()
    test_nums = [1, 1, 3, 4, 5]
    
    # 这样你可以同时测试两个方法，确保它们结果一致
    print(f"方法1 结果: {sol.containsDuplicate_v1(test_nums)}")
    print(f"方法2 结果: {sol.containsDuplicate_v2(test_nums)}")