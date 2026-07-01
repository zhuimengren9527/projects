# 算法笔记：K 个最接近原点的点 (K Closest Points to Origin)

## 1. 核心逻辑对比看板

| **维度**       | **方案 A：直接排序 (Sort)** | **方案 B：大顶堆 (Max Heap)** | **方案 C：快速选择 (Quick Select)** |
| -------------- | --------------------------- | ----------------------------- | ----------------------------------- |
| **直觉模型**   | 全班排排坐，取前 K 个       | 维持一个 K 人的“优等生”俱乐部 | 不断划地盘，直到分水岭切在 K 上     |
| **时间复杂度** | $O(N \log N)$               | $O(N \log K)$                 | 平均 $O(N)$，最差 $O(N^2)$          |
| **空间复杂度** | $O(N)$ (取决于排序实现)     | $O(K)$                        | $O(1)$ (原地交换)                   |
| **适用场景**   | 数据量小，追求代码简洁      | 数据流处理，内存有限          | 追求极致性能，处理大规模静态数据    |

---

## 2. 深度拆解：双指针快速选择 (Quick Select)

### 你的物理模型 (The "Two-Pointer Swap" Model)

> **笔记摘要**：
> 
> 1. **i 指针 (红色/侦察)** 与 **store_idx 指针 (蓝色/闸门)** 初始均指向 `left`。
>     
> 2. **标杆 (Pivot)** 暂避锋芒，换到最右边 `right`。
>     
> 3. **循环过程**：我对partition的分析逻辑是这样的：i是一个指针（红色），store_idx = left是一个指针（蓝色），当标杆去了最右边，循环开始，最初他们都指向第一个人，如果都比标杆小（这是我的判断标准，找最矮的）他们同时往右走一步，去下一个人，直到遇到比标杆大的，那蓝色指针不动，死死标记它，红色指针继续向右，如果比标杆小，马上和蓝色指针标记的人换位置，然后蓝色指针再次向右，他们继续往右寻找，找完了之后，最右边的标杆和蓝色指针标记的人换位置，此时标杆左边都是比它小的，右边都是比它大的或者和它相等的
>         
> 4. **归位**：扫描结束，标杆从 `right` 回到蓝针位置。此时标杆左边全小，右边大于等于。
>     

### 完整代码实现



```python
import random

class Solution:
    def kClosest(self, points: list[list[int]], k: int) -> list[list[int]]:
        dist = lambda p: p[0]**2 + p[1]**2

        def partition(left, right, pivot_idx):
            pivot_dist = dist(points[pivot_idx])
            # 1. 标杆去最右边罚站
            points[pivot_idx], points[right] = points[right], points[pivot_idx]
            
            store_idx = left
            # 2. i 指针开始巡逻
            for i in range(left, right):
                if dist(points[i]) < pivot_dist:
                    # 发现好数，填入 store_idx 标记的坑位
                    points[i], points[store_idx] = points[store_idx], points[i]
                    store_idx += 1
            
            # 3. 标杆归位，形成分水岭
            points[right], points[store_idx] = points[store_idx], points[right]
            return store_idx

        def select(left, right, k):
            if left >= right: return
            
            p_idx = random.randint(left, right)
            actual_idx = partition(left, right, p_idx)
            
            # 划地盘决策
            if k == actual_idx + 1:
                return
            elif k < actual_idx + 1:
                select(left, actual_idx - 1, k) # 划多了，去左边精选
            else:
                select(actual_idx + 1, right, k) # 划少了，去右边扩招

        select(0, len(points) - 1, k)
        return points[:k]
```

---

## 3. 工业级推荐：大顶堆 (Max Heap)

### 思考逻辑：名额优胜劣汰

- 我们维持一个大小为 $K$ 的堆。
    
- **入堆规则**：如果堆还没满，直接进。
    
- **踢人规则**：如果堆满了，拿当前点和堆顶（目前最差的优等生）比。如果当前点更近，就把堆顶踢走，让当前点进来。
    
- **结果**：遍历完后，堆里剩下的就是全场最接近的 $K$ 个。
    

### 代码实现 (Pythonic)

Python

```python
import heapq

class Solution:
    def kClosest(self, points: list[list[int]], k: int) -> list[list[int]]:
        # Python 默认是小顶堆，所以存入负距离变成“大顶堆”
        heap = []
        for (x, y) in points:
            d = -(x**2 + y**2)
            if len(heap) < k:
                heapq.heappush(heap, (d, x, y))
            elif d > heap[0][0]: # 比堆里最远的点还要近
                heapq.heappushpop(heap, (d, x, y))
        
        return [[x, y] for (d, x, y) in heap]
```

---

## 4. 暴力美学：一行排序 (Sort)

### 思考逻辑：化繁为简

如果你在非算法面试场景，或者数据量极小，直接利用 Python 内置的 $Timsort$ 是最稳健的选择。

Python

```python
class Solution:
    def kClosest(self, points: list[list[int]], k: int) -> list[list[int]]:
        # 根据欧几里得距离平方进行升序排列，取前 K 个
        return sorted(points, key=lambda p: p[0]**2 + p[1]**2)[:k]
```