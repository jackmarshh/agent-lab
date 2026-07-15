import os
import time
import json
import concurrent.futures
from typing import List, Dict, Any
from openai import OpenAI
from app.models import DiagnoseRequest, DiagnoseResponse, Evidence
from app.tools import get_weather, get_flight_price, search_knowledge

# --- 全局状态与配置 ---
MEMORY_STORE = {}
GLOBAL_STATE = {}

# 价格参考 (DeepSeek-V3 价格: 输入 $0.01/1M tokens, 输出 $0.1/1M tokens)
# 为了演示方便，我们按 1M tokens = 7元人民币折算
PRICE_INPUT_PER_1K = 0.00007  
PRICE_OUTPUT_PER_1K = 0.0007

MANAGER_PROMPT = """你是一个旅游咨询经理。
你的职责是：
1. 分析用户的旅游需求。
2. 调用【气象专家】获取天气和穿衣建议。
3. 调用【旅游专家】获取深度玩法和机票信息。
4. 汇总各方意见，将初步方案提交给【审计员】进行终审。
5. 根据审计反馈，给出最终回复。

回复格式：
总结：(概括专家的核心发现)
建议：(汇总专家的具体行动建议)
状态：(completed)"""

WEATHER_AGENT_PROMPT = """你是一个资深气象专家。请根据提供的天气数据，给出专业的出行天气评估和穿衣建议。"""
TRAVEL_AGENT_PROMPT = """你是一个资深导游专家。请根据提供的攻略库和机票数据，给出深度玩法建议。"""
CRITIC_PROMPT = """你是一个严苛的旅行审计员。任务是检查经理汇总的方案是否逻辑自洽且信息完整。
检查项：1. 建议是否与天气证据冲突？ 2. 建议是否包含了专家亮点？ 3. 是否有明显幻觉？
通过请回复：【通过】。否则指出问题要求重做。"""

def get_or_create_state(conversation_id):
    if conversation_id not in GLOBAL_STATE:
        GLOBAL_STATE[conversation_id] = {
            "messages": [{"role": "system", "content": MANAGER_PROMPT}],
            "evidence": [],
            "specialist_reports": {},
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_calls": 0}
        }
    return GLOBAL_STATE[conversation_id]

def track_usage(state: dict, usage_obj):
    """累加 Token 消耗"""
    if usage_obj:
        state["usage"]["prompt_tokens"] += usage_obj.prompt_tokens
        state["usage"]["completion_tokens"] += usage_obj.completion_tokens
        state["usage"]["total_calls"] += 1

def run_agent_specialist(client, role_prompt, evidence_text, user_query, state):
    """通用的子 Agent 执行器"""
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": f"用户问题：{user_query}\n相关证据：{evidence_text}"}
        ]
    )
    track_usage(state, response.usage)
    return response.choices[0].message.content

def handle_tool_call(tool_call, client, request, state):
    """处理单个工具调用的逻辑，供并行调用使用"""
    function_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    city = args.get('city', '未知城市')
    
    if function_name == "consult_weather_expert":
        raw_evidence = get_weather(city)
        evidence_text = "\n".join([e.detail for e in raw_evidence])
        expert_opinion = run_agent_specialist(client, WEATHER_AGENT_PROMPT, evidence_text, request.incident, state)
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "content": f"【气象专家报告】：{expert_opinion}",
            "evidence": raw_evidence,
            "expert": "weather",
            "opinion": expert_opinion,
            "trace": "指派【气象专家】(并行执行)"
        }
    elif function_name == "consult_travel_expert":
        raw_evidence = [*get_flight_price(city), *search_knowledge(city, city)]
        evidence_text = "\n".join([e.detail for e in raw_evidence])
        expert_opinion = run_agent_specialist(client, TRAVEL_AGENT_PROMPT, evidence_text, request.incident, state)
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "content": f"【旅游专家报告】：{expert_opinion}",
            "evidence": raw_evidence,
            "expert": "travel",
            "opinion": expert_opinion,
            "trace": "指派【旅游专家】(并行执行)"
        }
    return None

def diagnose(request: DiagnoseRequest) -> DiagnoseResponse:
    start_time = time.time()
    state = get_or_create_state(request.conversation_id)
    
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    tools_definition = [
        {"type": "function", "function": {"name": "consult_weather_expert", "description": "向气象专家咨询天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}},
        {"type": "function", "function": {"name": "consult_travel_expert", "description": "向旅游专家咨询玩法", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
    ]

    state["messages"].append({"role": "user", "content": request.incident})
    execution_trace = [f"接入全局状态机 (Session: {request.conversation_id})"]
    
    # --- ReAct 调度循环 ---
    for i in range(3):
        execution_trace.append(f"经理调度轮次 {i+1}")
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=state["messages"][-6:],
            tools=tools_definition,
        )
        track_usage(state, response.usage)
        
        message = response.choices[0].message
        state["messages"].append(message)

        if not message.tool_calls:
            break
        
        # 🚀 并行执行优化：使用 ThreadPoolExecutor 同时指派多个专家
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(handle_tool_call, tc, client, request, state) for tc in message.tool_calls]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    state["messages"].append({"role": "tool", "tool_call_id": result["tool_call_id"], "content": result["content"]})
                    state["evidence"].extend(result["evidence"])
                    state["specialist_reports"][result["expert"]] = result["opinion"]
                    execution_trace.append(result["trace"])

    # --- 仲裁机制 ---
    execution_trace.append("经理生成初步汇总，提交审计...")
    summary_res = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=state["messages"][-5:],
    )
    track_usage(state, summary_res.usage)
    preliminary_summary = summary_res.choices[0].message.content

    evidence_summary = "\n".join([e.detail for e in state["evidence"]])
    
    # 审计员调用
    audit_res = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": CRITIC_PROMPT},
            {"role": "user", "content": f"初步方案：\n{preliminary_summary}\n\n原始证据：\n{evidence_summary}"}
        ]
    )
    track_usage(state, audit_res.usage)
    audit_result = audit_res.choices[0].message.content
    
    if "【通过】" in audit_result:
        execution_trace.append("审计通过！✅")
        reply = preliminary_summary
    else:
        execution_trace.append(f"审计未通过！❌ 原因：{audit_result[:50]}...")
        correction_res = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                *state["messages"][-3:],
                {"role": "assistant", "content": preliminary_summary},
                {"role": "user", "content": f"审计员发现你的方案有问题，请根据建议修正：{audit_result}"}
            ]
        )
        track_usage(state, correction_res.usage)
        reply = correction_res.choices[0].message.content
        execution_trace.append("方案已修正。")

    state["messages"].append({"role": "assistant", "content": reply})

    # 计算费用
    cost = (state["usage"]["prompt_tokens"] * PRICE_INPUT_PER_1K + 
            state["usage"]["completion_tokens"] * PRICE_OUTPUT_PER_1K)
    
    latency = time.time() - start_time
    
    return DiagnoseResponse(
        status="completed",
        summary=reply.split("总结：")[-1].split("建议：")[0].strip() if "总结：" in reply else reply,
        recommended_action=reply.split("建议：")[-1].split("状态：")[0].strip() if "建议：" in reply else "建议参考专家报告。",
        evidence=state["evidence"],
        trace=execution_trace,
        metadata={
            "token_usage": state["usage"],
            "estimated_cost_rmb": round(cost, 5),
            "latency_seconds": round(latency, 2),
            "parallel_optimized": True
        }
    )
