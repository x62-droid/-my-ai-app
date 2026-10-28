import streamlit as st
from openai import OpenAI
import requests

st.title("🌐 会自己上网的 AI")
st.caption("已接入博查搜索 + DeepSeek 大脑")

# ================= 1. 读取密钥 =================
# 云端部署时，从后台 Secrets 读取；如果本地跑，直接写死
try:
    deepseek_key = st.secrets["DEEPSEEK_API_KEY"]
    bocha_key = st.secrets["BOCHA_API_KEY"]
except:
    # 【注意】在这里填入你的真实 Key，确保前后没有空格！
    deepseek_key = "sk-你的真实DeepSeekKey" 
    bocha_key = "sk-你的真实博查Key"

client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")

# ================= 2. 联网搜索函数 =================
def search_web(query):
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {bocha_key}",
        "Content-Type": "application/json"
    }
    payload = {"query": query, "count": 3}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('webPages', {}).get('value', [])
            search_text = ""
            for res in results:
                search_text += f"标题：{res.get('name')}\n摘要：{res.get('snippet')}\n\n"
            return search_text
        else:
            return "搜索接口报错"
    except Exception as e:
        return f"搜索异常：{e}"

# ================= 3. 网页界面与记忆 =================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= 4. 核心交互 =================
if prompt := st.chat_input("问点今天发生的新鲜事吧！"):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("正在全网搜索最新情报..."):
        search_results = search_web(prompt)
        
    system_instruction = f"""
    你是一个强大的 AI 助手。请结合我为你提供的【最新网页搜索结果】来回答用户的问题。
    如果搜索结果里没有相关信息，你可以用你原有的知识回答，并说明搜索结果缺失。
    
    【最新网页搜索结果】：
    {search_results}
    """
    
    api_messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]
    
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=api_messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
        except Exception as e:
            # 如果还是报错，直接把错误打印在网页上，方便我们看
            st.error(f"AI 接口出错了：{e}")
            reply = "抱歉，我刚刚走神了。"
            
    st.session_state.messages.append({"role": "assistant", "content": reply})
