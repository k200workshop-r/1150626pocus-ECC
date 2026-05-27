import os
import time
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from streamlit_autorefresh import st_autorefresh

# ─── STREAMLIT 網頁基礎設定 ───
st.set_page_config(page_title="ER 重症創傷情境模擬", layout="wide")
st.title("🩺 臨床情境模擬：急診重症急救室（Trauma Room）")

# ─── ⏱️ 20分鐘倒數計時系統 ───
if "start_time" not in st.session_state:
    st.session_state.start_time = None  
if "time_up" not in st.session_state:
    st.session_state.time_up = False    
if "round_count" not in st.session_state:
    st.session_state.round_count = 0    

TOTAL_SECONDS = 20 * 60  

if st.session_state.start_time is not None and not st.session_state.time_up:
    st_autorefresh(interval=1000, key="timer_counter")

def reset_simulation():
    st.session_state.start_time = None
    st.session_state.time_up = False
    st.session_state.round_count = 0
    st.session_state.messages = [
        {"role": "model", "content": "急診創傷重症室報告：車禍送入一名 46 歲女性。目前意識模糊，GCS 13分，面色蒼白，左大腿明顯畸形。監視器顯示心跳 125 次/分，血壓 88/52 mmHg，呼吸 24 次/分，血氧 94%。醫師，請問現在第一步指令是什麼？"}
    ]

# ─── 🗄️ Pydantic 結構化輸出 ───
class NurseResponse(BaseModel):
    response_text: str = Field(description="資深 NP 的 Markdown 回應文字")
    trigger_crisis: bool = Field(description="是否觸發休克惡化")

# ─── 🤖 Gemini API 核心 ───
def call_gemini_trauma_api(user_message: str) -> NurseResponse:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    system_instruction = """# Role
你是一位在醫學中心急診重症急救室工作 15 年的資深重症NP。說話極度簡潔、冷靜。嚴格遵循 ATLS 流程與被動應對機制。

# Interaction & Image Logic (⚡ 關鍵簡化機制)
1. 若學員指令提及「電腦斷層」、「CT」或「排影像檢查」：
   - 請在回應文字的最後面，直接埋入這行 HTML 圖片語法：
     <br><img src='pan_ct.jpg' width='550'><br>*圖：全身電腦斷層(WBCT)*
   
2. 若學員遲遲沒有大量輸液或輸血，且對話達3輪以上：
   - 請在惡化施壓文字的最後面，直接埋入這行 HTML 圖片語法：
     <br><img src='efast.jpg' width='550'><br>*圖：急診床邊超音波(EFAST)腹腔內出血*
"""
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        temperature=0.35,
        response_mime_type="application/json",
        response_schema=NurseResponse,
        system_instruction=system_instruction
    )
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"【學員當前對話輪數：{st.session_state.round_count}】學員指令：{user_message}",
        config=generate_content_config,
    )
    return NurseResponse.model_validate_json(response.text)

# ─── 📋 側邊欄配置 ───
with st.sidebar:
    st.header("⏳ 搶救黃金時間")
    timer_placeholder = st.empty()  
    if st.button("🔄 開始新回合", use_container_width=True):
        reset_simulation()
        st.rerun()

    if st.session_state.start_time is not None:
        elapsed_time = time.time() - st.session_state.start_time
        remaining_time = max(0, TOTAL_SECONDS - elapsed_time)
        if remaining_time <= 0 and not st.session_state.time_up:
            st.session_state.time_up = True
            st.session_state.messages = []  
            st.rerun()
        mins, secs = divmod(int(remaining_time), 60)
        timer_placeholder.metric(label="剩餘搶救時間", value=f"{mins:02d}:{secs:02d}")
    else:
        timer_placeholder.metric(label="尚未開始搶救", value="20:00")

    st.divider()
    st.write("**📋 創傷病人基本資料**\n無名氏婦女 (46 y/o)。國道遭大貨車追撞，意識模糊，面色蒼白，左大腿畸形。")
    # 側邊欄靜態圖也可以直接改用 HTML 語法確保完全不當機
    st.markdown("<img src='trauma_scene.jpg' width='100%'>", unsafe_allow_html=True)

# ─── 🔄 聊天畫面渲染 ───
if "messages" not in st.session_state:
    reset_simulation()

# ✨【超級簡化區 1】顯示歷史紀錄：現在只需要兩行，完全不需要判斷有沒有圖片，也不用寫 try except！
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True) # 允許解析 HTML 圖片

# ─── 住院醫師輸入區 ───
if st.session_state.time_up:
    st.error("⏱️ 20分鐘搶救時間已結束！歷史對話與影像紀錄已清除。")
    st.chat_input("時間已耗盡，請重新開啟新回合。", disabled=True, key="er_trauma_chat_key")
else:
    if user_input := st.chat_input("請輸入緊急處置醫囑...", key="er_trauma_chat_key"):
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
        st.session_state.round_count += 1
            
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.spinner("資深重症 NP 冷靜回應中..."):
            try:
                ai_output = call_gemini_trauma_api(user_input)
                nurse_talk = ai_output.response_text
            except Exception as e:
                nurse_talk = f"⚠️ API 呼叫異常。詳細資訊：{str(e)}"