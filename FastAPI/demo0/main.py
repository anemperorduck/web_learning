"""
理解现代 Python 异步 Web 框架的并发运行机制，
掌握基于声明式类型提示的数据校验方法，
并能够利用自动生成的交互式文档进行高效接口调试。
"""

import asyncio
import time
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr


# 配置日志格式
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FastAPI 异步架构与数据验证教程示例",
    description="展示 FastAPI 异步并发特性、Pydantic 数据校验及最佳实践的示例项目",
    version="1.0.0"
)

# ==========================================
# 1. Pydantic 数据模型定义
# ==========================================

class UserRegisterInput(BaseModel):
    """
    用户注册输入数据模型，包含严格的声明式校验
    """
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=20, 
        description="用户名，长度在 3-20 字符之间",
        examples=["john_doe"]
    )
    email: EmailStr = Field(
        ..., 
        description="合法的电子邮件地址",
        examples=["john@example.com"]
    )
    password: str = Field(
        ..., 
        min_length=8, 
        description="密码，长度不低于 8 位",
        examples=["secret_password123"]
    )

class UserRegisterResponse(BaseModel):
    """
    安全的用户注册响应模型，避免敏感信息（如密码）泄露
    """
    id: int
    username: str
    email: str
    is_active: bool = True


# ==========================================
# 2. 路由与业务逻辑实现
# ==========================================

@app.get("/", tags=["基础接口"])
async def root() -> Dict[str, str]:
    """根路径接口，返回简单的欢迎信息"""
    return {"message": "Hello World"}


@app.get("/sync", tags=["性能对比"])
def sync_endpoint() -> Dict[str, Any]:
    """
    同步阻塞接口：
    模拟 10 次顺序执行的阻塞 I/O 操作（每次 1 秒）。
    该接口在执行时，会按照顺序执行，总共耗时约 10 秒。
    """
    start_time = time.perf_counter()
    logger.info("同步接口开始执行...")
    
    # 模拟同步阻塞操作（例如：传统数据库查询或同步 HTTP 请求）
    for i in range(10):
        time.sleep(1)  # 这是一个阻塞当前线程的同步调用
        
    end_time = time.perf_counter()
    duration = end_time - start_time
    logger.info(f"同步接口执行完毕，耗时: {duration:.2f} 秒")
    return {"mode": "sync", "iterations": 10, "duration_seconds": round(duration, 2)}


@app.get("/async", tags=["性能对比"])
async def async_endpoint(tasks_count: int = 1000) -> Dict[str, Any]:
    """
    异步并发接口：
    使用 asyncio.gather 并发执行指定数量的异步非阻塞 I/O 任务。
    即使任务数量（tasks_count）增加到 1000 甚至 10000，
    由于是非阻塞并发执行，总耗时依然维持在 1 秒左右。
    """
    start_time = time.perf_counter()
    logger.info(f"异步并发接口开始执行，任务数: {tasks_count}...")

    # 定义一个内部协程模拟异步 I/O 任务
    async def async_io_task() -> None:
        await asyncio.sleep(1.0)  # 非阻塞地出让控制权，允许事件循环调度其他协程

    # 将所有协程任务打包
    tasks = [async_io_task() for _ in range(tasks_count)]
    
    # 并发执行所有封装好的协程
    await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    duration = end_time - start_time
    logger.info(f"异步接口执行完毕，耗时: {duration:.2f} 秒")
    return {"mode": "async", "iterations": tasks_count, "duration_seconds": round(duration, 2)}


@app.post(
    "/users/register", 
    response_model=UserRegisterResponse, 
    status_code=status.HTTP_201_CREATED, 
    tags=["用户管理"]
)
async def register_user(user_data: UserRegisterInput) -> Dict[str, Any]:
    """
    用户注册接口：
    展示 Pydantic 的自动类型转换与数据验证。
    """
    logger.info(f"接收到用户注册请求: {user_data.username}")
    
    # 模拟数据库落库操作，由于使用了 response_model，
    # 返回的 dict 会自动被过滤并匹配 UserRegisterResponse 的字段，多余的字段（如 password）会被安全过滤
    mock_db_user = {
        "id": 99,
        "username": user_data.username,
        "email": user_data.email,
        "password": user_data.password,  # response_model 会自动过滤此敏感字段
        "is_active": True
    }
    
    return mock_db_user