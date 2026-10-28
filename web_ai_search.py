import sys
sys.stdout.reconfigure(encoding='utf-8')
import streamlit as st
import requests
from openai import OpenAI

st.title("🌐 会自己上网的 AI")
st.caption("已接入博查搜索 + DeepSeek 大脑")

# ================= 1. 填入你的两个钥匙 =================
deepseek_key = "你的APIKEY"
bocha_key = "你的APIKEY"

client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")

# ================= 2. 定义“上网搜索”的函数 =================
def search_web(query):
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {bocha_key}",
        "Content-Type": "application/json"
    }
    # 我们只要前3条最相关的结果，节约Token
    payload = {"query": query, "count": 3} 
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('webPages', {}).get('value', [])
            
            # 把搜到的标题和摘要拼接成一段文本
            search_text = ""
            for res in results:
                search_text += f"标题：{res.get('name')}\n摘要：{res.get('snippet')}\n\n"
            return search_text
        else:
            return "搜索接口报错了，请稍后再试。"
    except Exception as e:
        return f"搜索发生异常：{e}"

# ================= 3. 网页界面与记忆 =================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= 4. 核心交互逻辑 =================
if prompt := st.chat_input("问点今天发生的新鲜事吧！"):
    
    # 显示用户的话
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 核心动作：先偷偷上网搜索！
    with st.spinner("正在全网搜索最新情报..."):
        search_results = search_web(prompt)
        
    # 组装给 AI 的“超级提示词”
    # 我们把搜到的网页内容当成背景知识，强行塞给 AI
    system_instruction = f"""
    【极其重要】：今天是 2026年10月27日。你是一个活在当下的 AI，请绝对不要认为今天是过去或未来。
    
    你是一个强大的 AI 助手。请结合我为你提供的【最新网页搜索结果】来回答用户的问题。
    ...
    """
    system_instruction = f"""
    你是一个强大的 AI 助手。请结合我为你提供的【最新网页搜索结果】来回答用户的问题。
    如果搜索结果里没有相关信息，你可以用你原有的知识回答，并说明搜索结果缺失。
    
    【最新网页搜索结果】：
    {search_results}
    """
    
    # 发给 AI 的消息包含：系统指令（带搜索结果） + 用户问题
    api_messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]
    
    # 呼叫 AI 并展示回复
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=api_messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        
    st.session_state.messages.append({"role": "assistant", "content": reply})
