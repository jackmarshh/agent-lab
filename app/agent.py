import os
from app.models import DiagnoseRequest, DiagnoseResponse, Evidence
from app.tools import get_weather, get_flight_price, get_local_food, search_knowledge

# 新增：简单的内存记忆存储 { conversation_id: [history_messages] }
MEMORY_STORE = {}

SYSTEM_PROMPT = """你是一个专业的旅游规划助手。
你的任务是根据提供的【天气】、【机票】、【美食】以及【内部专家攻略】证据，结合我们的【对话历史】，为用户提供一份简明扼要的旅行建议。

请特别注意：
1. 如果证据中包含【资深导游攻略库】的信息，请务必将其中的亮点（如特定景点、预约提醒）加入到建议中。
2. 保持专业、亲切的语气。

请严格遵守以下输出格式：
总结：(一句话概括当地情况)
建议：(给出具体的行动建议)
状态：(如果建议去，返回 completed；否则返回 needs_attention)"""


def _demo_response(request: DiagnoseRequest, evidence: list[Evidence]) -> DiagnoseResponse:
    # 简单的规则引擎模拟
    weather = next((e.detail for e in evidence if "天气" in e.detail), "")
    price_info = next((e.detail for e in evidence if "机票" in e.detail), "")
    
    status = "completed"
    if "小雨" in weather:
        status = "needs_attention"
        action = "天气不太好，建议推迟行程或准备室内活动。"
    else:
        action = f"天气不错，机票价格也合适（{price_info}），建议立即预订！"

    return DiagnoseResponse(
        status=status,
        summary=f"已为你查询到 {request.incident} 的信息：{weather}",
        recommended_action=action,
        evidence=evidence,
        trace=["接收到旅游咨询", "查询实时天气", "对比机票价格", "生成人工规则建议"],
    )


def diagnose(request: DiagnoseRequest) -> DiagnoseResponse:
    # 0. 获取历史记忆
    history = MEMORY_STORE.get(request.conversation_id, [])
    
    # 如果没有开启智能模式，走 Demo 逻辑
    if os.getenv("AGENT_MODE", "demo").lower() != "openai":
        # (为了简洁，这里省略 Demo 逻辑，实际中可保留)
        return _demo_response(request, [])

    # 1. 配置推理大脑
    from openai import OpenAI
    import json
    
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # 定义可用的工具集（供模型选择）
    tools_definition = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气情况",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_flight_price",
                "description": "查询指定城市的机票价格",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_knowledge",
                "description": "从资深导游库中检索深度旅游攻略",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "关键词或问题"},
                        "city_filter": {"type": "string", "description": "限定城市名，如'三亚'或'北京'"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-4:])
    messages.append({"role": "user", "content": request.incident})

    collected_evidence = []
    execution_trace = ["接收到旅游咨询"]
    
    # 2. 进入 ReAct 循环 (最多思考 3 轮，防止死循环)
    for i in range(3):
        execution_trace.append(f"第 {i+1} 轮思考中...")
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
        )
        
        message = response.choices[0].message
        messages.append(message) # 记录模型内心的 Thought

        # 检查模型是否想调用工具 (Action)
        if not message.tool_calls:
            break
        
        # 执行工具调用 (Observation)
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            execution_trace.append(f"决定行动：调用 {function_name} ({args})")
            
            # 动态执行对应的函数
            if function_name == "get_weather":
                obs = get_weather(args['city'])
            elif function_name == "get_flight_price":
                obs = get_flight_price(args['city'])
            elif function_name == "search_knowledge":
                obs = search_knowledge(args.get('query', ''), args.get('city_filter'))
            else:
                obs = []

            collected_evidence.extend(obs)
            
            # 把观察到的结果反馈给模型
            obs_text = "\n".join([e.detail for e in obs])
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": obs_text
            })
            execution_trace.append(f"观察到结果：{obs_text[:30]}...")

    # --- 修复：如果循环结束是因为 tool_calls 或达到上限，强制进行最后一次总结 ---
    if message.tool_calls or i == 2:
        execution_trace.append("进行最终汇总推理...")
        final_response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=messages,
        )
        reply = final_response.choices[0].message.content
    else:
        reply = message.content

    # 3. 最终回复 (Final Answer)
    reply = reply or "抱歉，我还在思考中，请稍后再试。"
    
    # 更新长期记忆
    history.append({"role": "user", "content": request.incident})
    history.append({"role": "assistant", "content": reply})
    MEMORY_STORE[request.conversation_id] = history

    # 解析结构化输出
    lines = {line.split("：", 1)[0].strip().lower(): line.split("：", 1)[1].strip()
             for line in reply.splitlines() if "：" in line}
    if not lines:
        lines = {line.split(":", 1)[0].strip().lower(): line.split(":", 1)[1].strip()
                 for line in reply.splitlines() if ":" in line}

    return DiagnoseResponse(
        status="completed" if lines.get("状态", "completed").lower() == "completed" else "needs_attention",
        summary=lines.get("总结", reply),
        recommended_action=lines.get("建议", "建议咨询当地地接社获取更多信息。"),
        evidence=collected_evidence,
        trace=execution_trace,
    )
