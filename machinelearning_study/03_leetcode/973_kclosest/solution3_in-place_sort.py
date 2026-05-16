class Solution:
    def KClosest(self,points:list[list[int]],k:int)->list[list[int]]:
        points.sort(key=lambda p:p[0]**2+p[1]**2)
        return [[x,y] for x,y in points[:k]]
# 定义测试函数
def run_test():
    test_cases = [
        {
            "name": "常规案例",
            "points": [[1, 3], [-2, 2]],
            "k": 1,
            "expect": [[-2, 2]]
        },
        {
            "name": "K=总数 (全收割)",
            "points": [[3, 3], [5, -1], [-2, 4]],
            "k": 3,
            "expect_len": 3
        }
    ]
    for case in test_cases:
        sol = Solution()
        result = sol.KClosest(case['points'],case['k'])
        if "expect" in case:
            assert len(result) == len(case["expect"]), f"❌ {case['name']} 数量不对"
        print(f"✅ 测试点 '{case['name']}' 通过！输出: {result}")
if __name__ == '__main__':
    run_test()