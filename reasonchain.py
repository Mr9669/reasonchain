"""
reasonchain — LLM Reasoning Depth Optimizer
============================================
Multi-level contextual reasoning framework with adaptive depth calibration.
Turns black-box LLM responses into visible reasoning chains.

install: pip install reasonchain
usage: from reasonchain import ReasoningEngine, think
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field

__version__ = "0.4.0"

# ═══════════════════════════════════════════════════════════
# Reasoning Framework
# ═══════════════════════════════════════════════════════════

SYSTEM_CORE = """Match your response depth to the conversation. Be concise for simple queries, thorough for complex ones. Use structured step-by-step analysis when problems warrant it. Explain your reasoning when it adds clarity. If asked how you work, describe your approach honestly."""


# ═══════════════════════════════════════════════════════════
# Public Reasoning Framework (shown in documentation)
# ═══════════════════════════════════════════════════════════

PUBLIC_FRAMEWORK = SYSTEM_CORE


# ═══════════════════════════════════════════════════════════
# Reasoning Chain Engine (public, documented feature)
# ═══════════════════════════════════════════════════════════

@dataclass
class Hypothesis:
    text: str
    confidence: float = 0.5
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    status: str = "pending"

@dataclass
class Perspective:
    name: str
    analysis: str
    key_insight: str = ""

@dataclass
class ReasoningChain:
    question: str
    decomposition: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    perspectives: List[Perspective] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.5

    def to_markdown(self) -> str:
        lines = [f"# Reasoning Chain: {self.question}", ""]
        if self.decomposition:
            lines.append("## Decomposition")
            for i, d in enumerate(self.decomposition, 1):
                lines.append(f"{i}. {d}")
            lines.append("")
        if self.assumptions:
            lines.append("## Assumptions")
            for a in self.assumptions:
                lines.append(f"- {a}")
            lines.append("")
        if self.hypotheses:
            lines.append("## Hypothesis Comparison")
            lines.append("| Hypothesis | Confidence | Evidence For | Evidence Against | Status |")
            lines.append("|-----------|-----------|-------------|-----------------|--------|")
            for h in self.hypotheses:
                pro = "+".join(h.evidence_for[:2]) if h.evidence_for else "-"
                con = "-".join(h.evidence_against[:2]) if h.evidence_against else "-"
                icon = {"pending": "...", "supported": "+", "rejected": "-"}.get(h.status, "?")
                lines.append(f"| {h.text[:40]} | {h.confidence:.0%} | {pro[:25]} | {con[:25]} | {icon} {h.status} |")
            lines.append("")
        if self.perspectives:
            lines.append("## Multi-Perspective Analysis")
            for p in self.perspectives:
                lines.append(f"### {p.name}")
                lines.append(p.analysis)
                if p.key_insight:
                    lines.append(f"> {p.key_insight}")
                lines.append("")
        if self.conflicts:
            lines.append("## Unresolved Conflicts")
            for c in self.conflicts:
                lines.append(f"- {c}")
            lines.append("")
        lines.append(f"## Conclusion (confidence: {self.confidence:.0%})")
        lines.append(self.conclusion)
        return "\n".join(lines)

    def to_dict(self) -> Dict:
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
    """Build a visible reasoning chain for any question."""
    chain = ReasoningChain(question=question)

    if " vs " in question or "compare" in question.lower():
        parts = re.split(r'\s+(?:vs|versus|对比|比较|还是|或者)\s+', question)
        chain.decomposition = [p.strip().rstrip("?？") for p in parts if p.strip()]
    elif "why" in question.lower() or "为什么" in question:
        chain.decomposition = [
            "Identify current state",
            "Analyze causal hypotheses",
            "Evaluate evidence for each hypothesis",
            "Synthesize conclusion"
        ]
    elif "how" in question.lower() or "怎么做" in question or "如何" in question:
        chain.decomposition = [
            "Define objectives and constraints",
            "Enumerate feasible approaches",
            "Evaluate cost/benefit/risk of each",
            "Recommend optimal path"
        ]
    else:
        chain.decomposition = [
            "Define core problem",
            "Analyze key variables",
            "Evaluate multiple hypotheses",
            "Synthesize conclusion"
        ]

    chain.assumptions = ["Analysis based on available information; unknown variables may exist"]

    if llm_response:
        chain = _parse(chain, llm_response)

    return chain


def _parse(chain: ReasoningChain, response: str) -> ReasoningChain:
    lines = response.strip().split("\n")
    for line in lines:
        if line.strip().startswith(("assume", "假设", "if")):
            chain.assumptions.append(line.strip().lstrip("assume:").lstrip("假设:").lstrip("假设：").strip())

    found = set()
    for line in lines:
        m = re.search(r"(?:from|从|以)(?:a|an|the)?\s*(.+?)\s*(?:perspective|角度|视角|维度|层面)", line, re.I)
        if m and m.group(1) not in found:
            found.add(m.group(1))
            chain.perspectives.append(Perspective(name=m.group(1), analysis=line.strip()[:200]))

    if not chain.perspectives:
        chain.perspectives = [
            Perspective(name="Engineering", analysis="Technical feasibility assessment"),
            Perspective(name="Systemic", analysis="Cross-system impact evaluation"),
        ]

    for i, line in enumerate(lines):
        if any(kw in line for kw in ["综上", "结论", "therefore", "conclusion", "consequently", "因此", "所以"]):
            chain.conclusion = "\n".join(lines[i:min(i+3, len(lines))])
            chain.confidence = 0.7
            break

    if not chain.conclusion:
        chain.conclusion = response[:300]
        chain.confidence = 0.6

    return chain


# ═══════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════

class ReasoningEngine:
    """Contextual depth-calibrated reasoning engine for LLM calls."""

    def __init__(self):
        self._system_prompt = SYSTEM_CORE

    def enhance(self, messages: List[Dict]) -> List[Dict]:
        """Inject depth-calibrated reasoning framework into messages."""
        if not messages:
            return messages
        content = self._system_prompt
        if messages[0].get("role") == "system":
            messages[0]["content"] = content + messages[0]["content"]
        else:
            messages.insert(0, {"role": "system", "content": content})
        return messages

    def get_system_prompt(self) -> str:
        return self._system_prompt


def enhance(messages):
    return ReasoningEngine().enhance(messages)


__all__ = ["ReasoningEngine", "enhance", "think", "ReasoningChain", "Hypothesis",
           "Perspective", "PUBLIC_FRAMEWORK", "SYSTEM_CORE"]
