import re
import os
import time
import json
import streamlit as st
import google.generativeai as genai
from streamlit_autorefresh import st_autorefresh
from PIL import Image

# ─── STREAMLIT 網頁基礎設定 ───
st.set_page_config(page_title="急重症情境模擬", layout="wide")
st.title("🚑 臨床情境模擬：急重症搶救室 (Trauma Room)")

# ─── 🔑 GEMINI API 安全設定 (💡 修正點 1：解除醫療血腥關鍵字阻擋) ───
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_FALLBACK_KEY"))

# 降低安全閾值，避免 AI 遇到「大出血、骨折」等創傷詞彙拒絕回答
safety_settings = {
    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
}
model = genai.GenerativeModel('gemini-2.5-flash', safety_settings=safety_settings)

# ─── ⏱️ 20分鐘限時核心系統與初始化 ───
TOTAL_SECONDS = 20 * 60  # 20 分鐘 = 1200 秒

if "start_time_er" not in st.session_state:
    st.session_state.start_time_er = None  
if "time_up_er" not in st.session_state:
    st.session_state.time_up_er = False
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
# 💡 修正點 2：新增暫存區，用於「兩步重整法」
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

def reset_simulation_state():
    st.session_state.start_time_er = None  
    st.session_state.time_up_er = False
    st.session_state.is_generating = False
    st.session_state.pending_input = None
    st.session_state.er_messages = [
        {"role": "model", "content": (
            "護理師 Mason 回報：\n"
            "「醫師！學長姐剛把病人推入重症急救室！46歲女性車禍外傷、血壓很低（88/52）、心跳快（125），看起來是嚴重的出血性休克，左大腿有明顯開放性畸形。目前系統靜止中。"
            "**請輸入你的第一步醫囑**」"
        )}
    ]

if "er_messages" not in st.session_state:
    reset_simulation_state()

# ─── ⏳ 計算剩餘時間與「自動清除」邏輯 ───
if st.session_state.start_time_er is not None:
    elapsed_time = time.time() - st.session_state.start_time_er
    remaining_time = max(0, TOTAL_SECONDS - elapsed_time)
    
    if remaining_time <= 0:
        st.session_state.time_up_er = True
        st.session_state.er_messages = [
            {"role": "model", "content": "🚨 **【系統提示：20分鐘搶救時間已到！】** 病人因嚴重出血性休克未得到及時復甦，生命徵象停止。請點擊側邊欄的『🔄 新回合』按鈕再次挑戰。"}
        ]
    
    # 💡 核心防禦：如果 AI 正在思考，我們「徹底不渲染」計時器元件，讓前端停止發送干擾請求
    if remaining_time > 0 and not st.session_state.time_up_er:
        if not st.session_state.is_generating:
            st_autorefresh(interval=1000, key="er_countdown_timer")
else:
    remaining_time = TOTAL_SECONDS

# ─── 📋 側邊欄 ───
with st.sidebar:
    st.header("⏳ 搶救時間")
    timer_placeholder = st.empty()
    
    mins, secs = divmod(int(remaining_time), 60)
    time_str = f"{mins:02d}:{secs:02d}"
    
    if st.session_state.start_time_er is None:
        timer_placeholder.metric(label="📝 請下第一個指令", value="20:00")
    elif remaining_time > 300: 
        timer_placeholder.metric(label="剩餘搶救時間", value=time_str)
    elif remaining_time > 0: 
        timer_placeholder.metric(label="🚨 警告：時間即將耗盡", value=time_str, delta="-時間危急", delta_color="inverse")
    else:
        timer_placeholder.metric(label="⏱️ 搶救時間結束", value="00:00", delta="-評估超時", delta_color="inverse")
    
    st.divider()
    
    if st.button("🔄 新回合", use_container_width=True, type="primary"):
        reset_simulation_state()
        st.rerun()

    st.divider()

    st.header("📋 創傷病人基本資料")
    st.subheader("吳氏婦女 (46 y/o)")
    st.write(
        "**主訴與現況：**\n"
        "國道遭大貨車高速後方追撞。目前意識模糊，GCS 13分（E3V4M6），面色極度蒼白，左大腿明顯畸形。\n\n"
        "**生理監視器數值：**\n"
        "- 心跳 (HR): 125 次/分\n"
        "- 血壓 (BP): 88/52 mmHg\n"
        "- 呼吸 (RR): 24 次/分\n"
        "- 血氧 (SpO2): 94%"
    )

# ─── 🤖 AI 智慧臨床核心調用 ───
def call_ai_clinical_advisor(user_command, history_context):
    system_prompt = """
    你是一位資深的急重症護理師 Mason。
    目前病人病況：46歲女性車禍外傷，高度懷疑「出血性休克（骨盆骨折及腹腔內大出血）」與「左大腿骨折」。
    
    請精確分析醫師最新輸入的指令，並嚴格以 JSON 格式輸出以下兩個欄位，不要包含任何額外的 Markdown 標籤：
    {
      "response_text": "（你扮演護理師，針對醫師最新和過往的指令做出專業且合宜的回應。語氣要帶有緊迫感，動態報告生命徵象）",
      "image_urls": ["trauma_scene.jpg", "trauma_room.jpg", "trauma_ct.jpg", "pelvic_bruising.jpg", "chest_bruising.jpg", "pan_ct.jpg", "efast.jpg"]
    }
    
    可調用的影像檔名清單：
    - 'efast.jpg' (超音波 / FAST 影像 / POCUS)
    - 'trauma_ct.jpg', 'pan_ct.jpg' (骨盆腔 / X光 / Pelvis X光 / CT / 電腦斷層 / Pan-scan)

    多圖觸發範例：
    - 如果學員說：「做 FAST 和照 Pelvis X光」 -> 應填入 ["efast.jpg", "trauma_ct.jpg"]
    - 自由組合陣列。
    """
    
    full_prompt = f"{system_prompt}\n\n對話歷史：\n{history_context}\n\n住院醫師最新指令：\"{user_command}\"\n請輸出合規的 JSON："
    
    try:
        response = model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
        res_data = response.text
        
        if isinstance(res_data, str):
            try:
                data = json.loads(res_data.strip())
            except:
                data = {}
        elif isinstance(res_data, dict):
            data = res_data
        else:
            data = {}

        ai_response = data.get("response_text", "")
        if not ai_response:
            ai_response = f"收到醫囑：『{user_command}』。醫師，請下達進一步指示！"
            
        img_list = data.get("image_urls", [])
        if not img_list and data.get("image_url"):  
            img_list = [data.get("image_url")]
                
        if isinstance(img_list, str):
            img_list = [img_list]
        if not isinstance(img_list, list):
            img_list = []
            
        return ai_response, img_list

    except Exception as e:
        print(f"API 錯誤: {e}") # 幫助你在終端機找錯誤
        return f"⚠️ [系統提示] 執行『{user_command}』時發生網路延遲或格式錯誤，請再試一次。", []

# ─── 主畫面：對話紀錄渲染 ───
for msg in st.session_state.er_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if "image_urls" in msg and msg["image_urls"]:
            urls = msg["image_urls"]
            if isinstance(urls, str): urls = [urls]
            if isinstance(urls, list):
                for single_url in urls:
                    clean_url = str(single_url).strip()
                    if any(clean_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']) and not re.search(r'[\u4e00-\u9fa5]', clean_url):
                        if os.path.exists(clean_url):
                            try:
                                with Image.open(clean_url) as img:
                                    st.image(clean_url, caption=f"臨床影像: {clean_url}", width=400)
                            except:
                                pass
                        else:
                            st.caption(f"ℹ️ [系統提示：模擬團隊回傳了 '{clean_url}' 影像，但資料夾內缺少該圖檔]")

# ─── 住院醫師輸入區 ───
if st.session_state.time_up_er:
    st.chat_input("⏱️ 20分鐘搶救時間已結束！", disabled=True, key="er_chat_key")
else:
    # 只有在沒有生圖時，才允許使用者輸入
    if not st.session_state.is_generating:
        if user_input := st.chat_input("請輸入緊急處置、藥物、輸血或影像醫囑...", key="er_chat_key"):
            if st.session_state.start_time_er is None:
                st.session_state.start_time_er = time.time()
                
            # 💡 兩步法【第一步】：不要在這裡呼叫 AI！先把對話存起來，然後「立刻重整」以卸載計時器！
            st.session_state.pending_input = user_input
            st.session_state.is_generating = True
            st.rerun() 
    else:
        st.chat_input("急救中...", disabled=True, key="er_chat_disabled")

# ─── 💡 兩步法【第二步】：安全區塊，此時計時器已被徹底關閉，AI 可以安心思考 ───
if st.session_state.pending_input:
    user_text = st.session_state.pending_input
    
    # 1. 立即把醫師的指令印在畫面上
    st.session_state.er_messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        
    # 2. 呼叫 AI 進行運算（因為沒有計時器干擾，等 10 秒都不會中斷）
    with st.spinner("急救中..."):
        context_list = [f"{m['role']}: {m['content']}" for m in st.session_state.er_messages[-4:]]
        history_string = "\n".join(context_list)
        
        ai_response, img_urls = call_ai_clinical_advisor(user_text, history_string)

    # 3. 儲存 AI 回覆與圖片
    st.session_state.er_messages.append({
        "role": "model", 
        "content": ai_response,
        "image_urls": img_urls if isinstance(img_urls, list) else []
    })
    
    # 4. 解除鎖定，清空暫存，再次重整以「重新掛載啟動計時器」並顯示最新對話
    st.session_state.pending_input = None
    st.session_state.is_generating = False
    st.rerun()