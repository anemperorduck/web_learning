没问题，我们把步伐放慢。刚才的内容确实偏向工业级架构，对于刚入门的同学来说信息量有些大。

这一次，我们不聊复杂的底层原理，只聊最贴近日常开发、最实用的 **HTTP 状态码（Status Code）**。

---

### 什么是 HTTP 状态码？

简单来说，状态码就是**服务器给客户端（浏览器、手机 App 等）的一句“回话”**。
当浏览器向 FastAPI 发送一个请求时，FastAPI 会返回一段数据，同时还会附带一个 **3 位数字** 的状态码，告诉浏览器这次请求是成功了、失败了，还是出了其他问题。

我们可以把这 3 位数字分为五大类。记住它们的百位数，就能大概知道发生了什么：

- **`1xx`（信息提示）**：少见。“收到请求了，你等一下。”
- **`2xx`（成功）**：最常用。“没问题，搞定了！”
- **`3xx`（重定向）**：常见。“你要找的东西不在这，去那个网址看看。”
- **`4xx`（客户端错误）**：最常用。“**你（客户端）**发的数据不对，或者你没权限。”
- **`5xx`（服务器错误）**：最常用。“**我（服务器）**的代码写崩了，或者数据库挂了。”

---

### FastAPI 中的 `status` 模块

在写代码时，我们直接写数字（如 `200`、`404`）是可以的，但容易写错，而且代码可读性较差。
FastAPI 提供了一个 `status` 模块，里面把所有的状态码都定义成了易读的常量，格式为 `status.HTTP_xxx_xxxx`。

下面我们来看看开发中最常用的几个状态码。

---

## 常用状态码详解

### 1. 成功大类（2xx）—— “顺利完成任务”

#### ① `status.HTTP_200_OK`（数值：200）

- **含义**：最常见的成功状态。
- **场景**：获取数据成功、修改数据成功。
- _例子_：你刷微博，成功加载出了最新的动态列表。

#### ② `status.HTTP_201_CREATED`（数值：201）

- **含义**：成功创建了新资源。
- **场景**：用户注册成功、发布新帖子成功、上传新商品成功。
- _例子_：你在购物网站填写完信息，点击“确认添加收货地址”成功后。

#### ③ `status.HTTP_204_NO_CONTENT`（数值：204）

- **含义**：请求成功，但没有数据需要返回。
- **场景**：成功删除了某条数据。
- _例子_：你点击“删除这封邮件”，服务器删掉了邮件，不需要再返回什么新内容，只需要告诉你“删掉了”即可。

---

### 2. 客户端错误大类（4xx）—— “前端或用户做错了”

#### ① `status.HTTP_400_BAD_REQUEST`（数值：400）

- **含义**：坏请求。服务器看不懂你的请求，或者请求参数格式不对。
- **场景**：通用的错误提示。比如注册时密码太短。

#### ② `status.HTTP_401_UNAUTHORIZED`（数值：401）

- **含义**：未授权。你还没有登录。
- **场景**：需要登录后才能看的内容，你直接去访问了。
- _例子_：你还没登录账号，就去点击“我的钱包”。

#### ③ `status.HTTP_403_FORBIDDEN`（数值：403）

- **含义**：禁止访问。你登录了，但你的权限不够。
- **场景**：普通用户尝试访问管理员后台。
- _例子_：你登录了普通会员账号，去点击“超级管理员数据看板”。

#### ④ `status.HTTP_404_NOT_FOUND`（数值：404）

- **含义**：找不到资源。
- **场景**：请求的网址写错了，或者数据库里没有你要找的数据。
- _例子_：你访问 `/users/999`，但数据库里根本没有 ID 为 999 的用户。

#### ⑤ `status.HTTP_422_UNPROCESSABLE_ENTITY`（数值：422）

- **含义**：不可处理的实体。数据格式校验失败。
- **场景**：**FastAPI 最具特色的状态码**。当你要求输入一个数字，前端却传入了一个字符串时，FastAPI 会自动返回 422，不需要你手动写代码判断。

---

### 3. 服务器错误大类（5xx）—— “后端程序员要加班了”

#### ① `status.HTTP_500_INTERNAL_SERVER_ERROR`（数值：500）

- **含义**：服务器内部错误。
- **场景**：你的 Python 代码写错了，运行时抛出了异常（比如除以了 0，或者空指针错误）。
- _例子_：客户端发来请求，结果后端代码报错崩溃了，前端就会收到 500。

---

## 极简代码示例

我们在 FastAPI 中通常在两个地方使用状态码：

1.  **正常返回时**：在装饰器 `@app.post(...)` 中指定成功的状态码。
2.  **发生异常时**：使用 `raise HTTPException(...)` 主动抛出错误状态码。

这是一个非常简单、好懂的例子：

```python
from fastapi import FastAPI, status, HTTPException

app = FastAPI()

# 模拟一个极简的“数据库”列表
USER_DATABASE = {
    1: "小明",
    2: "小红"
}

# 示例 1: 获取数据（正常返回 200 OK，不用特意写，默认就是 200）
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 如果用户不存在，主动返回 404
    if user_id not in USER_DATABASE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对不起，找不到该用户"
        )
    return {"user_name": USER_DATABASE[user_id]}


# 示例 2: 创建数据（正常返回 201 Created）
@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(new_id: int, name: str):
    # 如果 ID 已经存在，主动返回 400 (Bad Request)
    if new_id in USER_DATABASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户ID已存在，无法创建"
        )

    # 模拟写入数据库
    USER_DATABASE[new_id] = name
    return {"message": "用户创建成功", "new_user": name}
```

### 总结口诀

- **想创建东西**：用 `@app.post(..., status_code=status.HTTP_201_CREATED)`。
- **数据找不到**：用 `raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)`。
- **权限不够/没登录**：用 `status.HTTP_401` 或 `status.HTTP_403`。
- **参数传错了**：FastAPI 会自动帮你返回 `status.HTTP_422`。
