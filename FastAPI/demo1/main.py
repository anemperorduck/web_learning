"""
生命周期管理
类型安全验证
标准异常处理
"""
import logging
from contextlib import asynccontextmanager
from pyclbr import Class
from typing import Dict, Any, Optional
from click import Option
from fastapi import FastAPI, Path, Query, HTTPException, status
from pydantic import BaseModel, Field

# 配置日志输出
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FastAPI-APP")

# -----------------------------------------------------------------------------
# 1. 定义生命周期管理器 (Lifespan)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理应用程序的生命周期。
    在此处执行启动时的初始化（如连接数据库、加载 ML 模型等）
    以及关闭时的清理工作。
    """
    logger.info(">>> 正在启动应用：初始化全局资源（例如：加载 LangChain 链或连接数据库）...")
    
    # 模拟全局状态注入
    app.state.db_connection = "Activate Connection Pool"

    yield  # 此时应用开始接收请求

    logger.info("<<< 正在关闭应用：释放全局资源（例如：断开数据库连接、释放显存）...")
    app.state.db_connection = None

# -----------------------------------------------------------------------------
# 2. 初始化 FastAPI 实例
# -----------------------------------------------------------------------------
app = FastAPI(
    title="企业级 AI 辅助 API 服务",
    description="基于 FastAPI 与 Python 异步编程构建的基础框架模板",
    version="1.0.0",
    lifespan=lifespan  # 注入生命周期管理
)

# -----------------------------------------------------------------------------
# 3. 数据校验模型 (Pydantic Model)
# -----------------------------------------------------------------------------
class UserResponse(BaseModel):
    """标准响应数据结构"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(..., description="响应消息描述")
    data: Optional[Dict[str, Any]] = Field(default=None, description="承载数据的主体")

# -----------------------------------------------------------------------------
# 4. 路由定义 (Endpoints)
# -----------------------------------------------------------------------------
@app.get(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="根路径测试接口"
)
async def read_root():
    """
    根路径异步接口，返回基础连通性测试数据
    """
    logger.info("处理根路径请求")
    return UserResponse(
        code=200,
        message="Hello World, FastAPI 运行正常！",
        data={"framework": "FastAPI", "mode": "Asynchronous"}
    )

@app.get(
    "/hello/{name}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="路径参数与查询参数接口"
)
async def read_item(
    name: str = Path(..., description="用户名称", min_length=1, max_length=50),
    age: Optional[int] = Query(None, description="可选的用户年龄", ge=0, le=150)
):
    """
    带参数的异步接口：
    - name: 路径参数 (Path Parameter)，强制校验长度
    - age: 查询参数 (Query Parameter)，可选，校验范围在 0-150 岁
    """
    logger.info(f"处理 hello 请求, 参数: name={name}, age={age}")

    # 简单的业务异常模拟
    if name.lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统安全限制：禁止以管理员身份进行此操作"
        )
    
    response_data = {"name": name}
    if age is not None:
        response_data["age"] = age
    
    return UserResponse(
        code=200,
        message="数据获取成功",
        data=response_data
    )
