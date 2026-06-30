class Solution:
    def minSubArrayLen(self,target: int, nums: list[int]) -> int:
        left_idx = 0
        current_sum = 0
        min_len = float('inf')

        for right in range(len(nums)):
            current_sum += nums[right]

            while current_sum >= target:
                min_len = min(min_len,right-left_idx+1)

                current_sum -= nums[left_idx]
                left_idx += 1
       
        return min_len if min_len != float('inf') else 0