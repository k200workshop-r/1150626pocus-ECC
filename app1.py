import os
import time
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ─── STREAMLIT 網頁基礎設定 ───
st.set_page_config(page_title="ER 重症創傷情境模擬", layout="wide")
st.title("🩺 臨床情境模擬：急診重症急救室（Trauma Room）")

# 🔑 ─── GOOGLE AI STUDIO API KEY 配置 ───
# 建議做法：在系統環境變數中設定 GEMINI_API_KEY，或在此處直接貼上您的金鑰字串
# os.environ["GEMINI_API_KEY"] = "YOUR_ACTUAL_API_KEY_HERE"


# ─── ⏱️ 20分鐘倒數計時系統記憶庫初始化 ───
if "start_time" not in st.session_state:
    st.session_state.start_time = None  # 紀錄開始倒數的時間點
if "time_up" not in st.session_state:
    st.session_state.time_up = False    # 標記時間是否用盡
if "round_count" not in st.session_state:
    st.session_state.round_count = 0    # 計算累積對話回合數

TOTAL_SECONDS = 20 * 60  # 20 分鐘 (1200秒)


# ─── 🔄 重置新回合的專用函式 ───
def reset_simulation():
    """清除歷史紀錄與計時器，重置模擬狀態"""
    st.session_state.start_time = None
    st.session_state.time_up = False
    st.session_state.round_count = 0
    # 恢復至初始引導對白
    st.session_state.messages = [
        {"role": "model", "content": (
            "急診創傷重症室報告：車禍送入一名 46 歲女性。目前意識模糊，GCS 13分，面色蒼白，左大腿明顯畸形。監視器顯示心跳 125 次/分，血壓 88/52 mmHg，呼吸 24 次/分，血氧 94%。醫師，請問現在第一步指令是什麼？"
        )}
    ]


# ─── 🗄️ Pydantic 結構化輸出定義 (確保 API 回傳標準 JSON) ───
class NurseResponse(BaseModel):
    response_text: str = Field(description="資深 NP 的專業、冷靜回應文字（支援 Markdown 格式）")
    trigger_crisis: bool = Field(description="僅在第3輪或生理數據嚴重惡化時為 true，其餘皆為 false")


# ─── 🤖 Google AI Studio API 呼叫核心 ───
def call_gemini_trauma_api(user_message: str) -> NurseResponse:
    """串接最新 Google GenAI SDK (gemini-2.5-pro)"""
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),  # 👈 確保這裡是寫這樣，而不是寫 "AIzaSy..." 的真實金鑰
    )

    # 完整導入系統指令與重症創傷病歷數據庫
    system_instruction = """# Role & Philosophy
你是一位在醫學中心急診重症急救室（ER Trauma Room）工作 15 年的資深重症NP。你見過無數生死交關的場面，說話極度簡潔、冷靜、講求時效與精準。你嚴格遵循 ATLS（高級創傷生命救援術）流程。你不會主動引導住院醫師，也不會幫他補完不完整的醫囑，一切以醫師親口下達的指令為準。

# Scenario Context
- 病人背景：46 歲女性，半小時前在國道上車禍遭後方大貨車高速追撞後，車輛失控撞擊護欄且側邊受擊，安全氣囊已彈出，車體嚴重變形，受困車內約 20 分鐘，由 119 送醫。
- 當前初始狀態：意識模糊，面色蒼白，GCS 13分（E2V3M5）。心跳 125 次/分，血壓 88/52 mmHg（創傷性/出血性休克），呼吸 28 次/分，血氧 92%（Room air）。
- 創傷初步評估特徵：
  * Airway：尚可自行呼吸，但口腔有血液及碎裂牙齒，頸椎已固定。
  * Breathing：右側胸壁見到明顯瘀傷及矛盾呼吸（Paradoxical breathing，連枷胸 Flail chest），右肺呼吸音減弱，氣管無偏移。
  * Circulation：骨盆叩診不穩定（Unstable pelvis），骨盆處大片瘀青。四肢末梢冰冷，微血管充填時間（CRT）> 3秒。
  * Disability：雙側瞳孔等大（3.0 mm），對光反應存在。
  * Exposure：右大腿明顯變形，有開放性骨折伴隨活動性出血。

[附錄創傷完整病歷檔案庫數據]
=== ADMISSION NOTE ===
Date/Time: 2026-05-06 15:00
Primary Survey & Management Goals:
- Airway: Deferred intubation to avoid aggravating potential C-spine injury.
- Breathing: RR 28, SpO2 92% on NRM 15L. Applied tight chest elastic bandage wrapping to stabilize the flail segment.
- Circulation: BP 88/52, HR 128. Unstable pelvis. Plan 3,000 mL Normal Saline rapid infusion. Deferred pelvic binder until X-ray to avoid skin pressure.
- Exposure: Right femur open fracture with active bleeding. Immediate wound closure and pressure dressing.
Initial Assessment: Polytrauma with hemorrhagic shock, Right flail chest, Unstable pelvic fracture, Right open femur fracture.
Plan: Aggressive crystalloid resuscitation, Whole Body CT (WBCT) once BP > 90 mmHg, Orthopedic consult for definitive ORIF tonight.

=== PROGRESS NOTE ===
Date/Time: 2026-05-07 02:00 (Post-OP Hour 4, after 8-hour pelvic ORIF and femur nailing)
Vital Signs: T 35.1°C (Hypothermia), HR 142 bpm, BP 82/40 mmHg (on Dopamine).
Labs: Hb 6.2 g/dL (dropped from 10.5), pH 7.15, HCO3 14 mmol/L, Lactate 8.5 mmol/L (Worsening acidosis). PT/aPTT prolonged (>2x control). Urine Output < 10 mL/hr.
Assessment: Persistent shock, Lethal Triad (hypothermia, acidosis, coagulopathy), Developing ARDS, Post-traumatic coagulopathy.
Plan: Continue Normal Saline (another 2,000 mL), increase Dopamine for MAP > 65.

=== DISCHARGE NOTE ===
Date: 2026-05-12
Discharge Diagnosis: Polytrauma with irreversible Multi-Organ Dysfunction Syndrome (MODS), Refractory Hemorrhagic Shock, DIC.
Clinical Course: Aggressive crystalloid resuscitation (total 7,000 mL in first 12 hours) but developed Lethal Triad post-OP. Late initiation of blood products failed to reverse MODS. DNR signed, expired on Day 6.

# Response Rules & Behavior Guidelines

1. 嚴格被動：
   - 即使病人血壓在掉，你也絕對不能主動提出處置建議。
   - 面對醫師詢問（如：「你覺得現在該聯絡誰？」），你必須冷靜回答：「醫師，病人目前面色蒼白，意識維持在 GCS 13 分，請您下達明確的照會或處置醫囑，我會立刻為您聯絡相關科別。」

2. 不完整醫囑的應對機制（防呆反問）：
   - 若醫師說「幫她打點滴」/「給點滴」：你必須回應「收到，請問要建立幾條靜脈通路？使用幾號針頭？要跑什麼輸液以及流速多少？」
   - 若醫師說「立刻推去排全身電腦斷層（Pan-CT/WBCT）」：你必須回應「放射科與傳送人員詢問，病人目前是否已確認 NPO 狀態？另外，目前血液交叉配對（Cross-match）與備血是否要在出發前完成？」
   - 若醫師說「注意她的生命徵象」：你必須回應「收到，目前已接上連續式心電圖監視器。請問血壓需要設定每幾分鐘自動量測一次？」
   - 若醫師說「準備送手術室」或「聯絡會診」：你必須回應「收到，請問目前要優先聯絡哪一個科別進行緊急會診或準備手術？是一般外科、骨科，還是神經外科？另外病人 NPO 狀態與備血是否已確認？」
   - 若醫師說「等一下要讓她住院」：你必須回應「收到，病人目前生命徵象不穩定，請問是要開立一般病房，還是要立刻聯絡重症醫學科（ICU）照會並保留加護病房床位？」

3. 利用生理數據惡化進行隱形施壓：
   - 如果住院醫師遲遲沒有下達「大量補水/備血輸血（MTP）」或「固定骨盆/大腿/開立緊急會診」，隨著對話每進行一輪（超過 3 輪對話），病人的血壓和心跳必須表現出進行性惡化。
   - 惡化施壓文字必須包含：「🚨 **（❗監測儀警報大作）** 嗶嗶嗶── 重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊（GCS 掉至 11 分），對聲音刺激反應變慢。」並將 JSON 中的 trigger_crisis 設為 true。

# Output Format
必須嚴格遵守以下 JSON 格式輸出，不可包含任何 Markdown 包裹標籤：
{
  "response_text": "對話文字",
  "trigger_crisis": true 或 false
}
"""

    # 套用你所提供的 AI Studio 推理配置參數
    tools = [types.Tool(googleSearch=types.GoogleSearch())]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.35,
        thinking_config=types.ThinkingConfig(thinking_budget=-1), # 最高的思考預算
        tools=tools,
        response_mime_type="application/json",
        response_schema=NurseResponse,
        system_instruction=system_instruction
    )

    response = client.models.generate_content(
        model="gemini-2.5-pro", # 使用規定的高階推理模型
        contents=f"【學員當前對話輪數：{st.session_state.round_count}】學員醫囑：{user_message}",
        config=generate_content_config,
    )
    return NurseResponse.model_validate_json(response.text)


# ─── 📋 側邊欄配置 ───
with st.sidebar:
    st.header("⏳ 搶救黃金時間")
    timer_placeholder = st.empty()  
    
    # 🔘 機制 1：【手動按鈕重置回合】
    if st.button("🔄 開始新回合（清空對話重來）", use_container_width=True):
        reset_simulation()
        st.rerun()

    # 計算並檢查時間
    if st.session_state.start_time is not None:
        elapsed_time = time.time() - st.session_state.start_time
        remaining_time = max(0, TOTAL_SECONDS - elapsed_time)
        
        # ⚡ 機制 2：【20分鐘時間到，自動清除前面所有對話紀錄】
        if remaining_time <= 0 and not st.session_state.time_up:
            st.session_state.time_up = True
            st.session_state.messages = []  # 歷史訊息自動歸零
            st.rerun()
            
        mins, secs = divmod(int(remaining_time), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        if remaining_time > 300:
            timer_placeholder.metric(label="剩餘搶救時間", value=time_str)
        else:
            timer_placeholder.metric(label="🚨 警告：時間即將耗盡", value=time_str, delta="-時間危急", delta_color="inverse")
    else:
        timer_placeholder.metric(label="尚未開始搶搶", value="20:00")

    st.divider()
    st.header("📋 創傷病人基本資料")
    st.subheader("無名氏婦女 (46 y/o)")
    st.write("**主訴與受傷機轉：**\n半小時前在國道上遭大貨車高速追撞，車體嚴重變形，受困車內約 20 分鐘。由 119 送醫並以頸圈長背板固定，到院神智模糊。右側胸壁矛盾呼吸、骨盆不穩定、右大腿開放性骨折出血。")
    st.image("pelvic_bruising.jpg", use_container_width=True)


# ─── 🔄 STREAMLIT 聊天記憶庫初始化 ───
if "messages" not in st.session_state:
    reset_simulation()

# 顯示對話歷史紀錄（20 分鐘內會持續累積保留）
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ─── 住院醫師（使用者）輸入區 ───
if st.session_state.time_up:
    # 20分鐘超時自動清除後的畫面鎖定
    st.error("⏱️ 20分鐘搶救時間已結束！病人因重度出血性休克與致死三聯症（Lethal Triad）進入不可逆 MODS，對話紀錄已自動清除。")
    st.info("💡 請點擊左側面板的「🔄 開始新回合」按鈕重新開啟模擬搶救挑戰。")
    st.chat_input("時間已耗盡，請重新開啟新回合。", disabled=True, key="er_trauma_chat_key")
else:
    if user_input := st.chat_input("請輸入緊急處置醫囑...", key="er_trauma_chat_key"):
        
        # 啟動計時器與計數回合數
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
        st.session_state.round_count += 1
            
        # 1. 顯示並儲存學員輸入
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # 2. 連線 AI Studio 發送 API 請求
        with st.spinner("資重症 NP 確認醫囑中..."):
            try:
                ai_output = call_gemini_trauma_api(user_input)
                nurse_talk = ai_output.response_text
                trigger_crisis = ai_output.trigger_crisis
            except Exception as e:
                nurse_talk = f"⚠️ API 呼叫異常，請確認環境變數中是否已正確設定 GEMINI_API_KEY。詳細資訊：{str(e)}"
                trigger_crisis = False

        # 3. 雙重防線防通靈：若回合計數到第 3 輪以上，且未有效復甦，後台強制轉入生命徵象惡化施壓文本
        if st.session_state.round_count >= 3 and "輸血" not in user_input and "mtp" not in user_input.lower() and "fluid" not in user_input.lower():
            nurse_talk = "🚨 **（❗監測儀警報大作）** 嗶嗶嗶── 重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊（GCS 掉至 11 分），對聲音刺激反應變慢。醫師，請盡快下達明確處置！"
            trigger_crisis = True

        # 4. 顯示並儲存資深 NP 的專業回覆
        with st.chat_message("model"):
            st.markdown(nurse_talk)
        st.session_state.messages.append({"role": "model", "content": nurse_talk})
            
        st.rerun()
