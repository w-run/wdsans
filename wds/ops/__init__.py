"""形变算子。

分层（见 docs/REBUILD-PLAN.md §4.2）：
  L1  全局仿射：字面缩放、平移、字重曲线
  L2  部件级：中宫外推、重心
  L3  笔画级：去脚、端面平切、钩张力、点柔化、折角微圆

**所有算子的契约**：输入点序列，输出同长度、同顺序、同 on/off 的点序列。
点数变化 = 违规，必须断言失败。
"""
from . import l1_affine, l3_stroke

__all__ = ["l1_affine", "l3_stroke"]
