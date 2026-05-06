## 第一层：语法层（DataCamp基础）
    
* **如何使用==thefuzz==计算两个字符串的相似度**
    * **单个字符比较**
    ```python
    from thefuzz import fuzz
    score = fuzz.WRation('字符串1','字符串2')
    ```
    * **批量比对**
    ```python
    import pandas as pd
    from thefuzz import process

    # 1. 假设这是干净的、标准的“州名词库” (用 Pandas Series 装着)
    correct_states = pd.Series([
        "California", 
        "New York", 
        "Texas", 
        "Florida", 
        "Washington"
    ])

    # 2. 这是调查问卷里用户乱填的一个错别字
    typo_word = "New Yrok"  # 故意把 r 和 o 写反

    print(f"🔍 正在为脏数据 '{typo_word}' 寻找最匹配的亲兄弟...\n")

    # 3. 召唤 process.extract，在 correct_states 里找最像的 2 个候选人
    # 参数：(目标词, 词库, limit=返回几个候选人)
    matches = process.extract(typo_word, correct_states, limit=2)
    print(f"打印'matches'的输出结果(一个包含元组的列表):") 
    print(matches)
    print("--- 🏆 匹配结果排行榜 ---")
    for match in matches:
        print(match)
    ```
        打印'matches'的输出结果(一个包含元组的列表):
            [('New York', 88, 1), ('Texas', 26, 2)]
            --- 🏆 匹配结果排行榜 ---
            ('New York', 88, 1)
            ('Texas', 26, 2)
