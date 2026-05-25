import os
import time
import streamlit as st

# 匯入創傷個案病歷資料
from patient_case1 import CASE_DATA

# ─── STREAMLIT 網頁基礎設定 ───
st.set_page_config(page_title="ER 重症創傷情境模擬", layout="wide")
st.title("🩺 臨床情境模擬：急診重症急救室（Trauma Room）")

# ─── 🔊 警報音效播放函式 ───
def play_alarm_sound():
    """在網頁前端播放真實的急診監視器警報聲"""
    alarm_url = "https://www.soundjay.com/buttons/sounds/beep-11.mp3"
    sound_html = f"""
    <iframe src="{alarm_url}" allow="autoplay" style="display:none;" id="iframeAudio"></iframe>
    <audio autoplay style="display:none;">
        <source src="{alarm_url}" type="audio/mp3">
    </audio>
    """
    st.components.v1.html(sound_html, height=0)


# ─── ⏱️ 20分鐘倒數計時系統記憶庫初始化 ───
if "start_time" not in st.session_state:
    st.session_state.start_time = None  # 紀錄開始倒數的時間點
if "time_up" not in st.session_state:
    st.session_state.time_up = False    # 標記時間是否用盡

TOTAL_SECONDS = 20 * 60  # 20 分鐘總秒數 (1200秒)


# ─── 側邊欄：呈現病人現況與計時器 ───
with st.sidebar:
    # ⏱️ 頂部動態計時器顯示區
    st.header("⏳ 搶救黃金時間")
    timer_placeholder = st.empty()  # 建立動態更新的容器
    
    # 計算並更新賸餘時間
    if st.session_state.start_time is not None:
        elapsed_time = time.time() - st.session_state.start_time
        remaining_time = max(0, TOTAL_SECONDS - elapsed_time)
        
        if remaining_time <= 0:
            st.session_state.time_up = True
            
        # 格式化為 分:秒
        mins, secs = divmod(int(remaining_time), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # 根據剩餘時間顯示不同顏色
        if remaining_time > 300:
            timer_placeholder.metric(label="剩餘搶救時間", value=time_str)
        else:
            timer_placeholder.metric(label="🚨 警告：時間即將耗盡", value=time_str, delta="-時間危急", delta_color="inverse")
    else:
        # 學員尚未開始互動時，定格在 20:00
        timer_placeholder.metric(label="尚未開始搶救", value="20:00")

    st.divider()

    st.header("📋 創傷病人基本資料")
    meta = CASE_DATA.get("case_meta", {})
    p_name = meta.get("patient_name", "無名氏婦女 (46 y/o)")
    p_gender = meta.get("gender", "Female")
    st.subheader(f"{p_name} ({p_gender})")
    st.write(f"**主訴與受傷機轉：**\n{meta.get('scenario', '')}")
    
    # 🖼️ 圖片放置點 1
    st.image(
        "pelvic_bruising.jpg", 
        use_container_width=True
    )
    
    st.divider()
    
    st.header("🌡️ 初始生命徵象 (Vitals)")
    vitals = CASE_DATA.get("vitals_initial", {})
    st.markdown(f"""
    - **血壓 (BP):** <span style='color:red; font-weight:bold;'>{vitals.get('BP', '')}</span>
    - **心跳 (HR):** <span style='color:red; font-weight:bold;'>{vitals.get('HR', '')}</span>
    - **呼吸 (RR):** {vitals.get('RR', '')}
    - **血氧 (SpO2):** {vitals.get('SpO2', '')}
    - **體溫 (BT):** {vitals.get('BT', '')}
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 🖼️ 圖片放置點 2
    st.image(
        "chest_bruising.jpg", 
        use_container_width=True
    )

# ─── STREAMLIT 聊天記憶庫初始化 ───
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "急診創傷重症室報告：車禍送入一名 46 歲女性。目前意識模糊，GCS 13分，面色蒼白，左大腿明顯畸形。監視器顯示心跳 125 次/分，血壓 88/52 mmHg，呼吸 24 次/分，血氧 94%。醫師，搶救計時將在您下達第一道指令後啟動，請問第一步指令是什麼？"}
    ]
if "round_count" not in st.session_state:
    st.session_state.round_count = 0  # 用於計算對話輪數

# 顯示歷史聊天訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── 🤖 本機邏輯模擬器 ───
def local_response_simulator(user_text):
    text = user_text.lower()
    st.session_state.round_count += 1
    
    # 觸發倒數計時：當學員輸入第一句話，且計時器尚未啟動過
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    
    should_trigger_alarm = False
    response_text = ""

    # 規則 4：拒絕引導
    if any(q in text for q in ["建議", "怎麼辦", "該做什麼", "你覺得", "what to do"]):
        response_text = "醫師，病人目前面色蒼白，意識維持在 GCS 13 分，請您下達明確的照會或處置醫囑，我會立刻為您聯絡相關科別。"

    # 規則 2：醫囑明確性檢查 & 快捷鍵數據回報
    elif "點滴" in text or "iv" in text or "fluid" in text or "輸液" in text:
        if any(kw in text for kw in ["條", "大口徑", "14g", "16g"]) and any(kw in text for kw in ["ns", "normal saline", "lr", "ringer"]):
            response_text = "收到，兩條大口徑靜脈通路已建立，Normal Saline 大量灌注中。目前重覆量測血壓暫時維持在 90/56 mmHg，心跳 120 次/分。"
        else:
            response_text = "（冷靜回應）收到，請問要建立幾條靜脈通路？使用幾號針頭？要跑什麼輸液以及流速多少？"
            
    elif "電腦斷層" in text or "ct" in text or "pan-ct" in text or "wbct" in text:
        response_text = f"放射科與傳送人員詢問，病人目前是否已確認 NPO 狀態？另外，目前血液交叉配對（Cross-match）與備血是否要在出發前完成？\n\n**【附帶後台報告】**\n{CASE_DATA['diagnostic_results']['WBCT']}"
        
    elif "輸血" in text or "mtp" in text or "備血" in text or "blood" in text:
        response_text = f"收到，立刻連絡血庫。{CASE_DATA['diagnostic_results']['Blood_Products_MTP']}"
        
    elif "骨盆" in text or "binder" in text or "固定" in text:
        response_text = f"（NP 迅速動作）已協助進行固定。{CASE_DATA['diagnostic_results']['Pelvic_Binder_Check']}"
        
    elif "生命徵象" in text or "vitals" in text or "監視器" in text:
        response_text = "收到，目前已接上連續式心電圖監視器。請問血壓需要設定每幾分鐘自動量測一次？"
        
    elif "手術" in text or "or" in text or "開刀" in text or "會診" in text or "照會" in text:
        response_text = "收到，請問目前要優先聯絡哪一個科別進行緊急會診或準備手術？是一般外科(GS)，還是骨科(Ortho)？另外病人 NPO 狀態與備血是否已確認？"
        
    elif "住院" in text or "icu" in text or "加護" in text:
        response_text = "收到，病人目前生命徵象不穩定，請問是要開立一般病房，還是要立刻聯絡重症醫學科（ICU）照會並保留加護病房床位？"
    
    else:
        response_text = "請醫師下達明確醫囑（如給氧流速、點滴針號與水別、照會科別等）。"

    # 規則 3：生理數據惡化隱形施壓（超過 3 輪對話且沒有給予正確處置時）
    if st.session_state.round_count >= 3:
        response_text = "🚨 **（❗監測儀警報大作）** 嗶嗶嗶── 重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊（GCS 掉至 11 分），對聲音刺激反應變慢。醫師，請盡快下達明確處置！"
        should_trigger_alarm = True 

    return response_text, should_trigger_alarm


# ─── 住院醫師（使用者）輸入區 ───
# 檢查時間是否已經用盡，若用盡則鎖死輸入框 (disabled=True)
if st.session_state.time_up:
    st.chat_input("⏱️ 20分鐘搶救時間已結束！病人已發生不可逆休克，無法再下達醫囑。", disabled=True, key="er_trauma_chat_key")
else:
    if user_input := st.chat_input("請輸入緊急處置醫囑...", key="er_trauma_chat_key"):
        
        # 1. 顯示使用者訊息
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # 2. 透過本機模擬器計算回應與音效標記
        full_response, trigger_alarm = local_response_simulator(user_input)

        # 3. 顯示 AI 模擬回應
        with st.chat_message("model"):
            st.markdown(full_response)
            
        # 4. 儲存至記憶庫維持畫面
        st.session_state.messages.append({"role": "model", "content": full_response})
        
        # 5. 🔊 如果觸發條件成立，立刻呼叫前端播放真實警報聲！
        if trigger_alarm:
            play_alarm_sound()
            
        # 6. 強制觸發 Streamlit 頁面重新渲染，讓側邊欄的計時器秒數立刻跳動
        st.rerun()