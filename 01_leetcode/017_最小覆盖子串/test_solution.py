import pytest
# 从你的业务代码文件中导入写好的函数
from solution import minWindow


# =====================================================================
# 🔬 核心规范 1：使用 @pytest.mark.parametrize 实现数据与逻辑分离
# 这种写法被称为“数据驱动测试”。你只需要维护测试用例表格，不需要重复写 if-else
# =====================================================================
@pytest.mark.parametrize(
    "s, t, expected",
    [
        # 用例 1：标准常规用例（昨晚肉搏的主战场）
        ("ADOBECODEBANC", "ABC", "BANC"),
        # 用例 2：你提出的终极进化双 A 用例（验证去重与备胎逻辑）
        ("AAOBECODEBANC", "ABC", "BANC"),
        # 用例 3：边界条件 - 目标字符串比原字符串还要长（刚性熔断）
        ("A", "AA", ""),
        # 用例 4：边界条件 - 刚好完全相等
        ("ABC", "ABC", "ABC"),
        # 用例 5：边界条件 - 噪声极大，嫌疑人极少
        ("XYZABCXYZ", "ABC", "ABC"),
        # 用例 6：极端边界 - 根本找不到（大盘彻底破产）
        ("ABCDEFG", "XYZ", ""),
        # 用例 7：嫌疑人有重复要求的用例
        ("AABCC", "AABC", "AABC"),
    ],
)
def test_min_window_accuracy(s: str, t: str, expected: str):
    """测试 minWindow 函数在各种常规和边界用例下的输出准确性。

    规范：测试函数的名称必须以 `test_` 开头。
    """
    # 🌟 工业级标准：使用 assert 算子进行无损对账，而不是用 print()
    assert minWindow(s, t) == expected


# =====================================================================
# 🔬 核心规范 2：极端异常边界测试（鲁棒性防御）
# =====================================================================
def test_min_window_empty_input():
    """测试输入为空字符串时的防御机制。"""
    assert minWindow("", "ABC") == ""
    assert minWindow("ABC", "") == ""