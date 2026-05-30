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

# ─── 🔑 GEMINI API 安全設定 ───
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_FALLBACK_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')

# ─── ⏱️ 20分鐘限時核心系統與初始化 ───
TOTAL_SECONDS = 20 * 60  # 20 分鐘 = 1200 秒

# 💡 修改點 1：初始狀態設為 None，代表尚未開始計時
if "start_time_er" not in st.session_state:
    st.session_state.start_time_er = None  
if "time_up_er" not in st.session_state:
    st.session_state.time_up_er = False

# 初始化對話紀錄與狀態
def reset_simulation_state():
    st.session_state.start_time_er = None  
    st.session_state.time_up_er = False
    st.session_state.er_messages = [
        {"role": "model", "content": (
            "護理師 Mason 回報：\n"
            "「醫師！學長姐剛把病人推入重症急救室！46歲女性車禍外傷、血壓很低（88/52）、心跳快（125），看起來是嚴重的出血性休克，左大腿有明顯開放性畸形。目前系統靜止中。"
            "**請輸入你的醫囑**」"
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
    
    if remaining_time > 0 and not st.session_state.time_up_er:
        st_autorefresh(interval=1000, key="er_countdown_timer")
else:
    # 尚未開始計時的預設值
    remaining_time = TOTAL_SECONDS

# ─── 📋 側邊欄（計時器、病人資料、重新開始按鈕） ───
with st.sidebar:
    st.header("⏳ 搶救時間")
    timer_placeholder = st.empty()
    
    # 呈現倒數計時格式
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
    
    # 「重新開始」按鈕機制
    if st.button("🔄 新回合", use_container_width=True, type="primary"):
        reset_simulation_state()
        st.rerun()

    st.divider()

    st.header("⚙️ 後台圖片管理")
    uploaded_files = st.file_uploader(
        "請選擇並上傳多張臨床影像圖片（如：trauma_ct.jpg, trauma_echo.jpg 等）", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_bytes = uploaded_file.read()
            with open(file_name, "wb") as f:
                f.write(file_bytes)
        st.success(f"🎉 成功同步上傳 {len(uploaded_files)} 張圖片至系統中！")

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
    
    img_path_er = "trauma_scene.jpg"
    if os.path.exists(img_path_er):
        try:
            with Image.open(img_path_er) as img:
                st.image(img_path_er, width="stretch")
        except:
            pass

# ─── 主畫面：對話紀錄渲染 ───
for msg in st.session_state.er_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image_urls" in msg and msg["image_urls"]:
            # 如果是複數張圖片，用橫向（或縱向）呈現
            for single_url in msg["image_urls"]:
                if os.path.exists(single_url):
                    st.image(single_url, caption=f"臨床影像: {single_url}", width=400)

# ─── 🤖 AI 智慧臨床核心調用 ───
def call_ai_clinical_advisor(user_command, history_context):
    system_prompt = """
    你是一位資深的急重症護理師 Mason。
    目前病人病況：46歲女性車禍外傷，高度懷疑「出血性休克（骨盆骨折及腹腔內大出血）」與「左大腿骨折」。
    你可以根據學員的指令，一次回傳「多張」或「零張」圖片。
    請精確分析醫師最新輸入的指令，並嚴格以 JSON 格式輸出三個欄位，不要包含任何額外的 Markdown 標籤：
    {
      "response_text": "（你扮演護理師，針對醫師當前指令和過往指令做出專業、合宜、條理分明且帶有急診緊迫口吻的回應。適度報告生命徵象數字變化）",
      "image_urls": "['trauma_scene.jpg', 'trauma_room.jpg', 'trauma_ct.jpg', 'pelvic_bruising.jpg', 'chest_bruising.jpg', 'pan_ct.jpg', 'efast.jpg'
    
    ]
    }
    
    可調用的影像檔名清單：
    - 'efast.jpg' (超音波 / FAST 影像)
    - 'trauma_ct.jpg' (骨盆腔 X 光)
    - 'pan_ct.jpg' (電腦斷層 / Pan-scan)

    多圖觸發範例：
    - 如果學員說：「排常規外傷影像檢查，做 FAST 和照 Pelvis X光」 -> 你的 image_urls 應填入 ['trauma_ct.jpg', 'efast.jpg']
    - 如果學員下達多重檢查指令 -> 自由組合陣列。
    """
    
    full_prompt = f"{system_prompt}\n\n對話歷史：\n{history_context}\n\n住院醫師最新指令：\"{user_command}\"\n請輸出合規的 JSON："
    
    try:
        response = model.generate_content(
            full_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        img_list = data.get("image_urls", [])
        if not isinstance(img_list, list):
            img_list = [img_list] if img_list else []
        return data.get("response_text", ""), img_list
    except Exception as e:
        return f"收到醫囑：『{user_command}』，團隊正加緊處理中！", []

# ─── 住院醫師（使用者）輸入區 ───
if st.session_state.time_up_er:
    st.chat_input("⏱️ 20分鐘搶救時間已結束！請點擊側邊欄按鈕重新開始。", disabled=True, key="er_chat_key")
else:
    if user_input := st.chat_input("請輸入緊急處置、藥物、輸血或影像醫囑...", key="er_chat_key"):
        
        if st.session_state.start_time_er is None:
            st.session_state.start_time_er = time.time()
            
        st.session_state.er_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        context_list = [f"{m['role']}: {m['content']}" for m in st.session_state.er_messages[-4:]]
        history_string = "\n".join(context_list)
        
        with st.spinner("急救團隊執行醫囑中..."):
            ai_response, img_url, img_caption = call_ai_clinical_advisor(user_input, history_string)

        valid_img_urls = [url for url in img_urls if os.path.exists(url)]

        if img_url and not os.path.exists(img_url):
            img_url = None

        # 渲染 AI 回應
        with st.chat_message("model"):
            st.markdown(ai_response)
            if valid_img_urls:
                # 這裡可以用 st.columns() 讓多張圖橫向排版，或者直接上下堆疊
                for valid_url in valid_img_urls:
                    try:
                        with Image.open(valid_url) as img:
                            st.image(valid_url, caption=f"檢查影像: {valid_url}", width=400)
                    except:
                        pass

        # 將結果存入歷史紀錄
        st.session_state.er_messages.append({
            "role": "model", 
            "content": ai_response,
            "image_urls": valid_img_urls
        })
        
        st.rerun()