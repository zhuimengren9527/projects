import random

class Solution:
    def KClosest(self,points:list[list[int]],k:int)->list[list[int]]:
        # 身高计算标准
        get_dist = lambda p:p[0]**2 + p[1]**2
        def partition(left,right,pivot_idx):
            # 算出标杆的身高
            pivot_dist = get_dist(points[pivot_idx])
            # 将标杆和最右边的人调换位置
            points[pivot_idx],points[right] = points[right],points[pivot_idx]

            # 创建标记指针
            store_idx = left
            # 双指针开始循环（store_idx和i）
            for i in range(left,right):
                # 如果索引为i的人比标杆矮,此时两个指针指的是同一个人
                if get_dist(points[i]) < pivot_dist:
                    # 自己和自己交换（保持不动）
                    points[i],points[store_idx] = points[store_idx],points[i]

                    # 标记指针也随i同时往右移一格，如果遇到一个比标杆高的，if为False，那么store_idx就不动了，i继续往右走，
                    # 直到遇到一个比标杆小的人，再来和被标记的这个高个子换位置，与此同时，标记指针（store_idx）再次+1，
                    # 往右走一格
                   
                    store_idx += 1
            # 循环结束后，将标杆和标记指针标记的人换位置
            points[right],points[store_idx] = points[store_idx],points[right]
            # 返回标记指针，也就是标杆所在的位置，其左边全比标杆小，右边大于等于标杆
            return store_idx
        def quick_select(left,right,k):
            if left >= right:
                return
            
            # 随机选一个标杆
            pivot_idx = random.randint(left,right)

            # 执行partition(分区)，获取标杆最终排在第几位
            actual_idx = partition(left,right,pivot_idx)
            # 如果k恰好是标杆的位置，结束
            if k == actual_idx + 1:
                return 
            # 如果k比标杆所在的位置小，那么就从左边开始到标杆左边的数再过一次partition
            elif k < actual_idx + 1:
                quick_select(left,actual_idx-1,k)

            # 否则就从标杆的右边开始到最右的索引再过一次partition
            else:
                quick_select(actual_idx+1,right,k)
            # 调用函数quick_select
        quick_select(0,len(points)-1,k)
            # 返回前k个元素
        return points[:k]





