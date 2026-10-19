import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

# 1. 先尝试加载本地 .env 文件
load_dotenv()

# 2. 【新增】再尝试从 Streamlit 云端 Secrets 读取 Key
# 如果是在云端，这步会把云端的 Key 塞进当前环境的“临时变量”里
try:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
except Exception:
    pass # 如果在你本地电脑跑，没有 st.secrets，就会跳过这步，继续用你系统的 Key

# ... 下面的网页代码和 Agent 代码保持原样完全不动 ...
# 1. 设置网页基本信息
st.set_page_config(page_title="超级 AI 助手", page_icon="🌐")
st.title("🌐 我的超级 AI 助手 (联网+记忆)")
st.caption("基于 LangChain、阿里云和 Tavily 搜索构建")


# 2. 初始化大模型和搜索工具
@st.cache_resource  # 缓存模型，防止每次刷新网页都重新加载
def get_agent():
    # 初始化模型（自动去 Mac 系统里找 OPENAI_API_KEY）
    model = ChatOpenAI(
        model="deepseek-v4.1-flash",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0
    )

    # 配置搜索工具（自动去 Mac 系统里找 TAVILY_API_KEY）
    search = TavilySearch(max_results=3)
    tools = [search]

    # 组装成智能体 (Agent)
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="你是一个强大的 AI 助手。你可以使用工具搜索最新的网络信息来回答问题。"
    )
    return agent


agent = get_agent()

# 3. 初始化聊天记录（存在浏览器的 session 里）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 把以前的聊天记录画在网页上（用气泡形式）
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

# 5. 接收用户的网页输入
if prompt := st.chat_input("想搜点什么？或者随便聊聊..."):
    # 把用户的话画在网页上
    with st.chat_message("user"):
        st.write(prompt)

    # 把用户的话存入历史记录
    st.session_state.messages.append(HumanMessage(content=prompt))

    # 调用 Agent（带联网功能）
    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考并决定是否要联网搜索..."):
            # 把全部历史记录传给 Agent
            res = agent.invoke({"messages": st.session_state.messages})

            # 提取最终回答
            final_answer = res["messages"][-1].content
            st.write(final_answer)

            # 把 AI 的回答也存入历史记录
            st.session_state.messages.append(AIMessage(content=final_answer))