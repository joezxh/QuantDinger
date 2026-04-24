# LLM 流式和非流式输出使用指南

## 概述

`llm.py` 已增强以同时支持**流式输出**（streaming）和**非流式输出**（complete response）两种模式。

## 核心改动

### 1. 新增参数

- `stream: bool = False` - 控制是否使用流式模式（默认 False，保持向后兼容）

### 2. 新增方法

- `_process_streaming_response()` - 处理流式响应的内部方法
- `call_llm_streaming()` - 便捷方法，直接启用流式模式

## 使用方式

### 方式一：非流式模式（默认，向后兼容）

```python
from app.services.llm import LLMService

llm_service = LLMService()

# 原有代码无需修改，默认使用非流式模式
result = llm_service.call_llm_api(
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ],
    model="openai/gpt-4o",
    use_json_mode=True
)

print(result)  # 直接获取完整响应
```

### 方式二：使用 stream 参数启用流式

```python
# 在 call_llm_api 中设置 stream=True
result = llm_service.call_llm_api(
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "写一篇长文章"}
    ],
    model="openai/gpt-4o",
    stream=True  # 启用流式模式
)

# 虽然内部是流式接收，但返回的仍然是完整内容
print(result)  # 完整文章内容
```

### 方式三：使用便捷方法

```python
# 使用专门的流式方法
result = llm_service.call_llm_streaming(
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "写一篇长文章"}
    ],
    model="openai/gpt-4o"
)

print(result)  # 完整文章内容
```

## 工作原理

### 非流式模式（stream=False）

```
请求 → 等待完整响应 → 返回结果
```

- 适用于短回复、JSON 格式数据
- 简单直接，延迟较低

### 流式模式（stream=True）

```
请求 → 逐块接收 → 累积内容 → 返回完整结果
```

1. 发送请求时设置 `"stream": true`
2. API 返回 Server-Sent Events (SSE) 格式数据
3. 逐行解析 `data: {...}` 格式的数据块
4. 从每个数据块的 `choices[0].delta.content` 提取内容
5. 累积所有内容片段
6. 遇到 `[DONE]` 标记时结束
7. 返回完整的累积内容

## 支持的 Provider

| Provider | 流式支持 | 备注 |
|----------|---------|------|
| OpenRouter | ✅ | 完全支持 |
| OpenAI | ✅ | 完全支持 |
| DeepSeek | ✅ | 完全支持 |
| Grok | ✅ | 完全支持 |
| OpenAI-Compatible | ✅ | 取决于具体实现 |
| Google Gemini | ⚠️ | 暂不支持，会自动降级为非流式 |
| Ollama | ✅ | 完全支持 |

## 错误处理

### 流式模式的容错机制

```python
try:
    result = llm_service.call_llm_api(
        messages=[...],
        stream=True
    )
except ValueError as e:
    # 如果流式处理失败但有部分内容，会返回部分内容
    # 日志中会显示: "Returning partial streaming content: X characters"
    print(f"Error: {e}")
```

**容错策略**：
- 如果流式解析失败但已接收部分内容，会返回部分内容而非抛出异常
- 记录警告日志，便于调试
- 只在完全没有内容时才抛出异常

## 实际应用场景

### 场景 1：Polymarket 批量分析（JSON 模式）

```python
# 保持非流式模式（默认），适合结构化数据
result = llm_service.call_llm_api(
    messages=analysis_messages,
    use_json_mode=True,
    temperature=0.3
    # stream=False (默认)
)

analysis_data = json.loads(result)
```

### 场景 2：AI 代码生成（长文本）

```python
# 使用流式模式，适合长文本生成
code_response = llm_service.call_llm_api(
    messages=code_gen_messages,
    model="openai/gpt-4o",
    use_json_mode=False,
    stream=True  # 启用流式
)

# code_response 包含完整的代码内容
```

### 场景 3：聊天对话（实时响应）

```python
# 当前实现：流式接收但返回完整内容
# 未来可扩展：实时推送每个 chunk 到前端
response = llm_service.call_llm_streaming(
    messages=chat_messages,
    temperature=0.7
)
```

## 性能对比

| 模式 | 首字延迟 | 总耗时 | 内存占用 | 适用场景 |
|------|---------|--------|---------|---------|
| 非流式 | 高 | 相同 | 低 | 短回复、JSON |
| 流式 | 低 | 相同 | 中 | 长文本、实时体验 |

**注意**：
- 总耗时相同（都需要等待完整生成）
- 流式模式的"低延迟"是指首字出现更快
- 当前实现返回完整内容，如需实时推送需额外实现

## 扩展：真正的实时流式推送

如果需要将流式内容实时推送到前端（如 WebSocket），可以这样扩展：

```python
def stream_to_websocket(llm_service, messages, websocket):
    """实时流式推送到 WebSocket"""
    url = f"{llm_service.base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {llm_service.api_key}"}
    
    data = {
        "model": "openai/gpt-4o",
        "messages": messages,
        "stream": True
    }
    
    response = requests.post(url, headers=headers, json=data, stream=True)
    
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            chunk = json.loads(line[6:])
            content = chunk.get('choices', [{}])[0].get('delta', {}).get('content')
            
            if content:
                # 实时推送每个片段
                websocket.send(json.dumps({
                    "type": "chunk",
                    "content": content
                }))
```

## 向后兼容性

✅ **完全向后兼容**
- 所有现有代码无需修改
- `stream` 参数默认为 `False`
- 返回值类型保持一致（都是 `str`）
- 错误处理机制兼容

## 调试技巧

### 查看流式处理日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 运行时会看到详细的流式处理日志
# DEBUG: Streaming response completed: 1234 characters
```

### 测试流式模式

```python
# 测试不同模型的流式支持
test_models = ["openai/gpt-4o", "deepseek/deepseek-chat", "google/gemma-4-e4b"]

for model in test_models:
    try:
        result = llm_service.call_llm_api(
            messages=[{"role": "user", "content": "说你好"}],
            model=model,
            stream=True
        )
        print(f"✅ {model}: {len(result)} chars")
    except Exception as e:
        print(f"❌ {model}: {e}")
```

## 总结

- ✅ 默认非流式模式，保持向后兼容
- ✅ 通过 `stream=True` 启用流式
- ✅ 自动检测和解析 SSE 格式
- ✅ 累积所有内容并返回完整结果
- ✅ 完善的错误处理和容错机制
- ✅ 支持所有 OpenAI 兼容的 Provider
