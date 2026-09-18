# K12 人工智能通识课教学助手

赛题向网页端 AI 教学助手：年级自适应对话、RAG 知识库、配图、在线 Python、练习与多智能体协同。

## 给评委：3 步运行

| 步骤 | 操作 |
|------|------|
| 1 | 双击 **`setup.bat`**（首次安装依赖，需联网） |
| 2 | 编辑 **`.env`**，填写 `DEEPSEEK_API_KEY` |
| 3 | 双击 **`run.bat`**，浏览器打开提示的地址（默认 `http://127.0.0.1:7860`） |

更完整说明见：[docs/给评委的3步说明.md](docs/给评委的3步说明.md)

---

## 功能

- **对话**：DeepSeek + 学段 Prompt + ChromaDB RAG
- **配图**：通义万相（需 `DASHSCOPE_API_KEY`）
- **朗读**：Edge TTS
- **编程**：受限 Python 沙箱
- **练习**：AI 出题 / 批改 + 本地 JSONL 记录
- **多智能体**：主讲老师 / 提问同学 / 笔记助手

## 开发者启动（可选）

```powershell
cd 项目目录
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
# 编辑 .env，至少填写 DEEPSEEK_API_KEY
.\.venv\Scripts\python.exe -m app.main
```

若 `Activate.ps1` 报「禁止运行脚本」：不必激活虚拟环境，直接用 `.venv\Scripts\python.exe` 即可。

CLI 联调：

```powershell
.\.venv\Scripts\python.exe api.py
```

## 环境变量

见 [.env.example](.env.example)。

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | 必填 |
| `DASHSCOPE_API_KEY` | 配图可选；不配则对话等功能仍可用 |
| `DEEPSEEK_MODEL` | 默认 `deepseek-flash` |

## 目录

```
app/                 # 应用代码
knowledge_base/      # 分学段 Markdown 知识库
data/chroma/         # 向量库（自动生成）
data/progress/       # 练习记录
```

## 演示脚本（约 5 分钟）

1. 选 **小学高年级**，问「什么是机器学习？」→ 查看 RAG 调试区  
2. 点 **生成配图** / **朗读回答**  
3. 改选 **初中**，问同一问题，对比难度与风格  
4. **编程** Tab 运行 Hello World 模板  
5. **练习** Tab 出题并批改  
6. **多智能体** Tab 输入「神经网络」观看三角色输出  

## 知识库

按学段放入 `knowledge_base/grade_*/*.md`，在界面 **系统** Tab 点「重建知识库索引」。

## 技术栈

Gradio · DeepSeek API · ChromaDB · LangChain Text Splitters · DashScope 万相 · Edge TTS

## （重要！可以预先准备图片，在介绍一般概念的时候用图片辅助呈现）
生成虚拟图像
## 接入图像模型，扩展知识库