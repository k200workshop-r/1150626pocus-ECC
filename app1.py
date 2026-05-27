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

# 計時器啟動後在背景持續走時，一秒都不會停
if st.session_state.start_time is not None and not st.session_state.time_up:
    st_autorefresh(interval=1000, key="timer_counter")

def reset_simulation():
    st.session_state.start_time = None
    st.session_state.time_up = False
    st.session_state.round_count = 0
    st.session_state.messages = [
        {
            "role": "model", 
            "content": "急診創傷重症室報告：車禍送入一名 46 歲女性。目前意識模糊，GCS 13分，面色蒼白，左大腿明顯畸形。監視器顯示心跳 125 次/分，血壓 88/52 mmHg，呼吸 24 次/分，血氧 94%。醫師，請問現在第一步指令是什麼？",
            "image_url": None,
            "image_caption": None
        }
    ]

# ─── 🗄️ Pydantic 結構化輸出 ───
class NurseResponse(BaseModel):
    response_text: str = Field(description="資深 NP 的 Markdown 回應文字")
    trigger_crisis: bool = Field(description="是否觸發休克惡化")
    image_url: str = Field(default=None, description="需要跳出的醫學影像網址，無則填 None")
    image_caption: str = Field(default=None, description="影像圖說，無則填 None")

# ─── 🤖 Gemini API 核心 ───
def call_gemini_trauma_api(user_message: str) -> NurseResponse:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    system_instruction = """# Role
你是一位在醫學中心急診重症急救室工作 15 年的資深重症NP。說話極度簡潔、冷靜。嚴格遵循 ATLS 流程與被動應對機制。

# Interaction & Image Logic
1. 若學員指令提及「電腦斷層」、「CT」或「排影像檢查」：
   - 護理師文字告知 CT 報告。
   - 將 JSON 中的 image_url 設為 'pan_ct.jpg'，image_caption 設為 '圖：全身電腦斷層(WBCT)評估病灶'。
   
2. 若學員遲遲沒有大量輸液或輸血，且對話達3輪以上：
   - 護理師文字告知生命徵象惡化休克。
   - 將 JSON 中的 image_url 設為 'efast.jpg'，image_caption 設為 '圖：急診床邊超音波(EFAST)腹腔內出血'。
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