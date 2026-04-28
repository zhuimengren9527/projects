class Solution:
     # 方法1
    def firstUniqChar_v1(self,s:str)->int:
        count = {}
        for char in s:
            count[char] = count.get(char,0) + 1
        for i,char in enumerate(s):
            if count[char] == 1:
                return i 
        return -1
    # 方法2
    def firstUniqChar_v2(self,s:str)->int:
        # 1.因为s全部为小写字母，准备一个长度为26的列表，记录字母出现的次数，开始均为0
        counts = [0] * 26
        # 2.遍历s得到每一个字母
        for char in s:
            # 计算char的索引
            index = ord(char) -ord('a')
            # 根据char的索引，找到其在counts中的位置，并+=1统计其出现的次数
            counts[index] += 1
        for i,char in enumerate(s):
            if counts[ord(char)-ord('a')] == 1:
                return i
        return -1

# 测试代码
sol = Solution()
test_s = 'leetcode'
print(f"预期输出结果:0")
print(f"方法1 结果:{sol.firstUniqChar_v1(test_s)}")
print(f"方法2 结果:{sol.firstUniqChar_v2(test_s)}")
