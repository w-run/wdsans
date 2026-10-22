"""确定性 CFF2 字串编码器。

fontTools 自带的 T2CharStringPen 会按数值做算子优化（能压成 hlineto / vhcurveto 等），
同一路径在不同 master 上可能被编码成不同算子序列，导致 varLib 合并失败。

本模块只输出 rmoveto / rlineto / rrcurveto 三种算子，结构只取决于路径拓扑，
因此在「同源、同拓扑」的不同 master 上必定完全一致 —— 这是 VF 合并的前提。
"""
from fontTools.misc.psCharStrings import T2CharString


class CanonicalPen:
    """把绝对坐标路径写成固定算子序列的 T2 program。"""

    def __init__(self):
        self.program = []
        self._cur = (0, 0)
        self._start = (0, 0)

    # -- pen protocol -------------------------------------------------
    def moveTo(self, pt):
        x, y = pt
        cx, cy = self._cur
        self.program.extend([round(x - cx), round(y - cy), "rmoveto"])
        self._cur = (x, y)
        self._start = (x, y)

    def lineTo(self, pt):
        x, y = pt
        cx, cy = self._cur
        self.program.extend([round(x - cx), round(y - cy), "rlineto"])
        self._cur = (x, y)

    def curveTo(self, *points):
        for p in points:
            x, y = p
            cx, cy = self._cur
            self.program.extend([round(x - cx), round(y - cy)])
            self._cur = (x, y)
        self.program.append("rrcurveto")

    def qCurveTo(self, *points):
        raise NotImplementedError("CFF 只支持三次��线")

    def closePath(self):
        # CFF 轮廓隐式闭合（末点 -> 起点），但解码器的 currentPoint 仍停在**末点**，
        # 所以这里绝不能用起点覆盖 _cur，否则下一个 rmoveto 的基准会错。
        pass

    def endPath(self):
        pass

    def addComponent(self, glyphName, transformation):
        raise NotImplementedError("CFF2 不支持复合字形")

    # -- 输出 ---------------------------------------------------------
    def getCharString(self, private=None, globalSubrs=None):
        cs = T2CharString(program=list(self.program))
        cs.private = private
        cs.globalSubrs = globalSubrs
        return cs


def replay_to_canonical(value):
    """把 RecordingPen 的记录回放进 CanonicalPen，返回 T2CharString。"""
    pen = CanonicalPen()
    for op, args in value:
        getattr(pen, op)(*args)
    return pen
