# 注意力与Transformer

Self-Attention 让序列中任意位置互相「看」，适合并行训练。
Transformer 叠多头注意力与前馈网络，是现代大模型骨干。

关键思想：用相似度加权聚合信息。理解这一点有助于读懂 LLM 论文入门材料。
