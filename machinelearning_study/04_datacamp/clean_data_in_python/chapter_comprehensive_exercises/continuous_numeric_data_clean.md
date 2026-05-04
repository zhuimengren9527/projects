# 🎈带有业务杂质的连续数值型数据的清洗（带单位）
* **1. 为什么对金额数据，慎用 value_counts()**
    - 在处理日期或状态（如 VIP、SVIP）时，value_counts() 是神技，因为它们的种类是有限的（离散数据）。但是，金额是连续数据。假设有 100 万条订单，可能就有 90 万个不同的金额数值（比如 15.99, 16.00, 16.01...）。如果对它用value_counts()，屏幕上会立刻刷出几十万行结果，肉眼根本无法从中找出那些混进去的“文本毒瘤”。
    -  **💡 专属侦察兵：反向探测法**
    对于连续数字列，大厂的做法不是看全貌，而是只抓异类。我们会利用 to_numeric 的报错机制，先不急着覆盖原数据，而是做一次“模拟排雷”：

        ```python
        # 1. 模拟强制转换，不合规的变成 NaN
        temp_parsed = pd.to_numeric(df_exam['total_spend'], errors='coerce')

        # 2. 揪出那些变成了 NaN 的行（也就是原本混有文本的行）
        dirty_mask = temp_parsed.isna()

        # 3. 只打印这些“嫌疑犯”的本来面目
        print("🚨 发现以下非纯数字的脏数据：")
        print(df_exam.loc[dirty_mask, 'total_spend'])
        ```
* **2. 混入字符就被踢成 NaN，岂不是误杀？**

    - 如果发现“嫌疑犯”长这样：`Pending_Audit`（纯文本），那直接 NaN 杀掉完全没毛病。但如果嫌疑犯长这样：$1599.50、8848元、100,000.00（带逗号的千分位）—— 这可是真金白银的有效业务数据！如果用errors='coerce' 一锤子砸下去，它们全都会变成 NaN，这就叫严重的业务事故。

    * **🔪 破局之法：从“大锤”换成“手术刀” (Regex 提取)**
    当侦察兵发现存在可以抢救的带字符数字时，就不能用 coerce 这种莽夫操作了。需要用正则表达式（Regex），把数字和小数点从文本里“抠”出来：

        ```python
        # 使用正则表达式提取：只保留数字、小数点和负号
        # [^\d\.-] 的意思是：匹配所有【不是】数字(\d)、小数点(\.)、负号(-)的字符
        # regex=True 表示开启正则，把这些非数字字符替换为空字符串 ''
        df_exam['spend_clean'] = df_exam['total_spend'].astype(str).str.replace(r'[^\d\.-]', '', regex=True)

        # 抠干净之后，里面就只剩纯粹的数字字符串了，此时再安全地转换
        df_exam['spend_clean'] = pd.to_numeric(df_exam['spend_clean'], errors='coerce')
        ```
