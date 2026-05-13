import heapq
class Point:
    def __init_(self,x,y):
        self.x = x
        self.y = y
        self.dist_sq = x**2 + y**2
    def __lt__(self,other):
        return self.dist_sq > other.dist_sq
    
class Solution:
    def KCloest(self,points:list[list[int]],k:int)->list[list[int]]:
        hp = []
        for x,y in points:
            p = Point(x,y)
            if len(hp) < k:
                heapq.heappush(hp,p)
            else:
                if hp[0] < p:
                    heapq.heapreplace(hp,p)
        res = []
        while hp:
            curr = heapq.heappop(hp)
            res.append([curr.x,curr.y])
        return res


