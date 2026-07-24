import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, List, Optional
from uuid import UUID

from fastapi import FastAPI, Path, Query, Body, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

# ------------------------------------------------------------------------------
# 1. 日志与全局配置
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AIGateway")

# ------------------------------------------------------------------------------
# 2. Lifespan 生命周期管理 (模拟 Agent 全局资源初始化)
# ------------------------------------------------------------------------------
# 全局资源句柄字典
app_resources: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI 应用生命周期上下文管理器。
    在服务启动时加载 LLM 连接池与 LangGraph Checkpointer，在服务停止时优雅清理。
    """
    logger.info("🚀 [Lifespan] 正在初始化 AI Gateway 全局资源 (LLM Clients, Checkpointer)...")

    # 模拟异步初始化数据库连接池或 LLM Client
    await asyncio.sleep(0.5)
    app_resources["llm_client"] = "FakeLLMClientInitialized"
    app_resources["graph_checkpointer"] = "FakeRedisCheckpointerInitialized"
    logger.info("✅ [Lifespan] 全局资源初始化完成。")

    yield  # 服务运行中...

    logger.info("🛑 [Lifespan] 正在释放全局资源...")
    app_resources.clear()
    logger.info("✅ [Lifespan] 资源释放完毕，服务已安全退出。")

# ------------------------------------------------------------------------------
# 3. Pydantic 进阶请求模型定义 (配合 Field 类型注解)
# ------------------------------------------------------------------------------
class MessagePayload(BaseModel):
    """单条消息载体"""
    role: str = Field(
        ...,
        pattern="^(user|system|assistant)$", 
        description="消息发送者角色，必须为 user, system 或 assistant"
    )

    cotent: str = Field(
        ...,
        min_length=1, 
        max_length=4096,
        description="消息文本内容，不得为空且不超过 4096 字符"
    )

class AgentChatRequest(BaseModel):
    """Agent 对话请求体模型"""
    prompt: str = Field(
        ...,
        min_length=1, 
        max_length=2000, 
        description="用户当前输入的 Prompt 指令",
        examples=["请帮我总结这篇文章的核心观点。"]
    )

    history: List[MessagePayload] = Field(
        default_factory=list,
        max_length=20,
        description="历史对话上下文，最多保留最近 20 条"
    )

    attachment_urls: Optional[List[HttpUrl]] = Field(
        default=None,
        description="可选的附件 URL 列表（用于多模态 Agent 参数注入）"
    )

class AgentChatResponse(BaseModel):
    """Agent 对话响应模型"""
    session_id: UUID
    agent_id: str
    output_text: str
    tokens_used: int
    execution_time_ms: float

# ------------------------------------------------------------------------------
# 4. FastAPI 应用实例初始化
# ------------------------------------------------------------------------------
app = FastAPI(
    title="Enterprise AI Agent Gateway",
    version="1.0.0",
    description="工业级 FastAPI + LangChain/LangGraph 参数校验路由 Gateway",
    lifespan=lifespan
)


# ------------------------------------------------------------------------------
# 5. 核心路由实现 (结合 Path, Query, Field)
# ------------------------------------------------------------------------------
@app.post(
    "/api/v1/agents/{agent_id}/sessions/{session_id}/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="向指定 Agent 发送对话请求",
    tags=["Agent Operations"]
)
async def chat_with_agent(
    # --- 路径参数 (Path) ---
    agent_id:str = Path(
        ..., 
        min_length=3, 
        max_length=32, 
        pattern="^[a-zA-Z0-9_-]+$", 
        description="Agent 唯一标识符（仅支持字母、数字、下划线和连字符）"
    ),
    session_id: UUID = Path(
        ..., 
        description="符合 RFC 4122 标准的 Session UUID，映射为 LangGraph thread_id"
    ),

    # --- 查询参数 (Query) ---
    verbose: bool = Query(
        default=False, 
        description="是否开启 Agent 执行的调试日志输出"
    ),
    temperature: float = Query(
        default=0.7, 
        ge=0.0, 
        le=2.0, 
        description="控制 LLM 输出随机性 (0.0 - 2.0)"
    ),
    max_tokens: int = Query(
        default=1024, 
        ge=64, 
        le=4096, 
        description="单次生成最大 Token 数"
    ),

    # --- 请求体参数 (Body / Field) ---
    request_body: AgentChatRequest = Body(
        ..., 
        description="对话请求负载，已被 Pydantic Field 严格校验"
    )
) -> AgentChatRequest:
    """
    **Agent 对话主入口点**

    通过严格的 Path/Query/Body 参数校验，过滤无效请求后将 Payload 递交至下游 LangGraph 图逻辑。
    """
    start_time = asyncio.get_event_loop().time()

    # 1. 检查全局资源是否正常启动
    if "llm_client" not in app_resources:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="AI Gateway 服务未准备就绪，LLM 客户端未初始化"
        )
    
    logger.info(f"收到 Agent 请求 | Agent ID: {agent_id} | Session ID: {session_id}")
    logger.info(f"控制参数 | Temp: {temperature} | Max Tokens: {max_tokens} | Verbose: {verbose}")

    # 2. 模拟构造 LangGraph State 初始状态
    # 在真实场景中，这里对应 langgraph_app.ainvoke(input_state, config=config)
    graph_input_state = {
        "thread_id": str(session_id),
        "agent_id": agent_id,
        "current_prompt": request_body.prompt,
        "chat_history": [msg.model_dump() for msg in request_body.history],
        "temperature": temperature,
        "attachments": [str(url) for url in request_body.attachment_urls] if request_body.attachment_urls else []
    }

    # 模拟异步调用 LangGraph 节点处理
    try:
        # 使用 asyncio.sleep 模拟非阻塞的 LLM 调用
        await asyncio.sleep(0.2) 
        mock_llm_reply = f"【Agent {agent_id} 响应】: 我已收到您的指令 '{request_body.prompt}'，并基于历史 {len(request_body.history)} 条消息完成了推演。"
    except Exception as e:
        logger.error(f"Agent 推演失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent 处理异常: {str(e)}"
        )
    
    duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

    # 3. 构造返回结构
    return AgentChatResponse(
        session_id=session_id,
        agent_id=agent_id,
        output_text=mock_llm_reply,
        tokens_used=128,  # 模拟占用 Token 数
        execution_time_ms=round(duration_ms, 2)
    )