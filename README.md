# reasonchain 🧠

**让AI的思考过程变得可见。**

不只是另一个prompt模板——`reasonchain` 把LLM的黑盒回答变成结构化的推理链。

## 为什么用 reasonchain？

LLM给你答案，但不告诉你**为什么**这么想。reasonchain 补上这一环：

```
❌ 普通方式: "AI会取代部分程序员工作"
✅ reasonchain: 
   ├─ 假设A: 取代重复性编码 (置信度85% | 支持: GitHub Copilot数据)
   ├─ 假设B: 不会取代系统设计 (置信度70% | 反对: 需要领域知识)
   ├─ 工程角度: 当前AI在创造性任务上仍有盲区
   ├─ 经济角度: 需求增长 > 被替代的速度
   └─ 结论: 部分替代，整体增强 (置信度75%)
```

## 安装

```bash
pip install reasonchain
```

## 5秒上手

```python
from reasonchain import think

# 分析任何问题
chain = think("微服务 vs 单体架构，选哪个？")
print(chain.to_markdown())

# 结合LLM回答深化分析
import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "微服务 vs 单体架构"}]
)
chain = think("微服务 vs 单体架构", response.choices[0].message.content)
print(chain.to_markdown())
# 输出包含: 问题分解 + 假设对比表 + 多角度分析 + 结论
```

## 功能

- ✅ **推理链可视化** — 把LLM回答解析为结构化推理过程
- ✅ **假设对比** — 并列展示多个假设，标注证据和置信度
- ✅ **多角度分析** — 自动检测工程/经济/伦理等维度
- ✅ **冲突标注** — 标记未解决的推理矛盾
- ✅ **LLM增强** — 注入第一性原理推理框架到API调用

MIT License
