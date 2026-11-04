"""WDesign Sans 构建内核 (wds)。

设计前提（见 docs/REBUILD-PLAN.md）：
  只改 gvar 的 delta 向量，绝不重建轮廓 —— 保证跨字重拓扑一致、VF 成立。
"""
__version__ = "0.1.0"
