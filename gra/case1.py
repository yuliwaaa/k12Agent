"""
智能体问答网页 - Gradio 实现
支持流式输出、多轮对话、上下文管理
兼容 Gradio 4.x/5.x/6.x 版本
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Optional, AsyncGenerator, Union

import gradio as gr
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置管理 ====================
class Config:
    """应用配置"""
    API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000/v1/chat/completions")
    API_KEY = os.getenv("AGENT_API_KEY", "sk-default-key")
    MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "gpt-3.5-turbo")
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful AI assistant.")
    TIMEOUT = int(os.getenv("TIMEOUT", 60))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 2))

    # Gradio 配置
    SERVER_NAME = os.getenv("SERVER_NAME", "127.0.0.1")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 7860))

config = Config()

# ==================== Agent 客户端 ====================
class AgentClient:
    """智能体 API 客户端"""

    def __init__(self):
        self.api_url = config.API_URL
        self.api_key = config.API_KEY
        self.model = config.MODEL_NAME
        self.system_prompt = config.SYSTEM_PROMPT
        self.timeout = config.TIMEOUT
        self.max_retries = config.MAX_RETRIES

    def _build_messages(self, history: List[Dict[str, str]], new_message: str) -> List[Dict[str, str]]:
        """构建完整的消息列表（包含 system prompt 和历史）"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": new_message})
        return messages

    async def send_message(
        self,
        history: List[Dict[str, str]],
        new_message: str
    ) -> AsyncGenerator[str, None]:
        """
        发送消息并流式接收响应

        Args:
            history: 历史对话列表 [{"role": "user/assistant", "content": "..."}]
            new_message: 用户新消息

        Yields:
            流式响应的文本片段
        """
        messages = self._build_messages(history, new_message)

        # 请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 重试机制
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST",
                        self.api_url,
                        json=payload,
                        headers=headers
                    ) as response:
                        response.raise_for_status()

                        logger.info(f"开始接收流式响应 - 问题: {new_message[:50]}...")

                        async for line in response.aiter_lines():
                            if not line:
                                continue

                            # 解析 SSE 格式
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 "data: " 前缀

                                if data == "[DONE]":
                                    logger.info("流式响应完成")
                                    break

                                try:
                                    chunk = json.loads(data)
                                    # 提取 delta.content（OpenAI 兼容格式）
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            content = delta["content"]
                                            if content:  # 非空内容
                                                yield content
                                except json.JSONDecodeError as e:
                                    logger.warning(f"JSON 解析失败: {e}, 原始数据: {data}")
                                    continue

                # 成功接收，跳出重试循环
                break

            except httpx.TimeoutException as e:
                logger.error(f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    yield f"\n\n⚠️ **错误**: 请求超时，请稍后重试。"
                else:
                    await asyncio.sleep(2 ** attempt)  # 指数退避

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP 错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    yield f"\n\n⚠️ **错误**: 服务器返回错误 {e.response.status_code}，请检查 API 配置。"
                else:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"未知错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}", exc_info=True)
                if attempt == self.max_retries:
                    yield f"\n\n⚠️ **错误**: {str(e)}"
                else:
                    await asyncio.sleep(1)

# ==================== Gradio 界面逻辑 ====================
class ChatApp:
    """聊天应用主类"""

    def __init__(self):
        self.client = AgentClient()
        self._setup_ui()

    def _setup_ui(self):
        """构建 Gradio 界面"""
        with gr.Blocks(title="智能体问答助手") as self.interface:

            # 标题区域
            gr.Markdown("""
            # 🤖 智能体问答助手
            #### 基于 Gradio 构建的多轮对话系统
            """)

            # 状态栏
            with gr.Row():
                gr.Markdown(
                    f"""
                    <div style="display: flex; align-items: center; font-size: 14px; color: #666; padding: 8px;">
                        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; 
                             background-color: #00ff00; box-shadow: 0 0 8px #00ff00; margin-right: 8px;"></span>
                        <span>系统在线 · 模型: {config.MODEL_NAME}</span>
                    </div>
                    """
                )

            # 聊天组件 - 不指定 type，使用默认行为
            self.chatbot = gr.Chatbot(
                label="对话历史",
                height=480
            )

            # 输入区域
            with gr.Row():
                self.msg = gr.Textbox(
                    label="输入您的问题",
                    placeholder="请输入您的问题，按 Enter 发送...",
                    lines=3,
                    scale=8,
                    show_label=True
                )
                with gr.Column(scale=1, min_width=120):
                    self.submit_btn = gr.Button("🚀 发送", variant="primary", size="lg")

            # 操作按钮
            with gr.Row():
                self.clear_btn = gr.Button("🗑️ 清空对话", variant="secondary", size="sm")
                gr.Markdown("""
                <div style="font-size: 12px; color: #999; text-align: right; margin: 8px 0;">
                    💡 支持 Markdown 格式 · 流式输出 · 自动上下文
                </div>
                """)

            # ==================== 事件绑定 ====================

            # 发送消息
            self.submit_btn.click(
                self._respond,
                [self.msg, self.chatbot],
                [self.chatbot]
            ).then(
                lambda: "",  # 清空输入框
                None,
                [self.msg]
            )

            # 回车发送
            self.msg.submit(
                self._respond,
                [self.msg, self.chatbot],
                [self.chatbot]
            ).then(
                lambda: "",
                None,
                [self.msg]
            )

            # 清空对话
            self.clear_btn.click(
                self._clear_history,
                None,
                [self.chatbot]
            )

    async def _respond(
        self,
        message: str,
        history: List[Union[List[str], Dict[str, str]]]
    ):
        """
        响应函数 - 处理用户消息并生成回复

        Args:
            message: 用户消息
            history: 当前对话历史 (Gradio Chatbot 格式)

        Yields:
            更新后的对话历史
        """
        # 如果消息为空，直接返回当前历史
        if not message or not message.strip():
            yield history
            return

        # 检测 Chatbot 使用的格式
        # 如果 history 中的元素是字典，使用 messages 格式
        # 否则使用传统的 [user, assistant] 格式
        use_messages_format = False
        if history and isinstance(history[0], dict):
            use_messages_format = True

        if use_messages_format:
            # ====== Messages 格式 (字典) ======
            # 添加用户消息
            history.append({"role": "user", "content": message})
            yield history

            # 添加占位的助手消息
            history.append({"role": "assistant", "content": ""})
            full_response = ""

            try:
                # 获取历史
                hist_dict = [msg for msg in history if msg["role"] != "system"]

                async for chunk in self.client.send_message(hist_dict, message):
                    full_response += chunk
                    history[-1]["content"] = full_response
                    yield history

                logger.info(f"响应完成，长度: {len(full_response)} 字符")

            except Exception as e:
                error_msg = f"❌ 发生错误: {str(e)}"
                history[-1]["content"] = error_msg
                yield history
                logger.error(f"响应失败: {e}", exc_info=True)

        else:
            # ====== 传统格式 (列表) ======
            # 添加用户消息
            history.append([message, None])
            yield history

            full_response = ""

            try:
                # 转换历史格式
                hist_dict = []
                for user_msg, assistant_msg in history[:-1]:
                    if user_msg:
                        hist_dict.append({"role": "user", "content": user_msg})
                    if assistant_msg:
                        hist_dict.append({"role": "assistant", "content": assistant_msg})

                async for chunk in self.client.send_message(hist_dict, message):
                    full_response += chunk
                    history[-1][1] = full_response
                    yield history

                logger.info(f"响应完成，长度: {len(full_response)} 字符")

            except Exception as e:
                error_msg = f"❌ 发生错误: {str(e)}"
                history[-1][1] = error_msg
                yield history
                logger.error(f"响应失败: {e}", exc_info=True)

    def _clear_history(self) -> list:
        """清空对话历史"""
        return []

    def launch(self):
        """启动应用"""
        self.interface.launch(
            server_name=config.SERVER_NAME,
            server_port=config.SERVER_PORT,
            share=False,
            debug=False
        )

# ==================== 入口 ====================
if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════╗
    ║     🤖 智能体问答助手 v1.0               ║
    ║     Powered by Gradio + Codex            ║
    ║                                          ║
    ║     访问地址: http://127.0.0.1:7860      ║
    ╚═══════════════════════════════════════════╝
    """)

    app = ChatApp()
    app.launch()