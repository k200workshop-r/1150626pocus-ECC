import os
import time
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
# 引入自動刷新套件，確保計時器啟動後不暫停、雷打不動地倒數
from streamlit_autorefresh import st_autorefresh

# ─── STREAMLIT 網頁基礎設定 ───
st.set_page_config(page_title="ER 重症創傷情境模擬", layout="wide")
st.title("🩺 臨床情境模擬：急診重症急救室（Trauma Room）")

# 🔑 ─── GOOGLE AI STUDIO API KEY 配置 ───
# 建議做法：在系統環境變數中設定 GEMINI_API_KEY，或在此處直接貼上你的金鑰字串
# os.environ["GEMINI_API_KEY"] = "YOUR_ACTUAL_API_KEY_HERE"

# ─── ⏱️ 20分鐘倒數計時系統記憶庫初始化 ───
if "start_time" not in st.session_state:
    st.session_state.start_time = None  # 紀錄開始倒數的時間點
if "time_up" not in st.session_state:
    st.session_state.time_up = False    # 標記時間是否用盡
if "round_count" not in st.session_state:
    st.session_state.round_count = 0    # 計算累積對話回合數

TOTAL_SECONDS = 20 * 60  # 20 分鐘 (1200秒)

# 🔄 如果計時器已經啟動且時間未到，啟動背景「每秒自動刷新機制」，確保計時器不受輸入暫停影響
if st.session_state.start_time is not None and not st.session_state.time_up:
    st_autorefresh(interval=1000, key="timer_counter")


# ─── 🔄 重置新回合的專用函式 ───
def reset_simulation():
    """清除歷史紀錄與計時器，重置模擬狀態"""
    st.session_state.start_time = None
    st.session_state.time_up = False
    st.session_state.round_count = 0
    # 恢復至初始引導對白
    st.session_state.messages = [
        {
            "role": "model", 
            "content": (
                "急診創傷重症室報告：車禍送入一名 46 歲女性。目前意識模糊，GCS 13分，面色蒼白，左大腿明顯畸形。監視器顯示心跳 125 次/分，血壓 88/52 mmHg，呼吸 24 次/分，血氧 94%。醫師，請問現在第一步指令是什麼？"
            ),
            "image_url": None,
            "image_caption": None
        }
    ]


# ─── 🗄️ Pydantic 結構化輸出定義（加入影像圖片回傳欄位） ───
class NurseResponse(BaseModel):
    response_text: str = Field(description="在此填入資深 NP 的冷靜、專業Markdown回應文字")
    trigger_crisis: bool = Field(description="僅在生理數據惡化隱形施壓時為 true，其餘皆為 false")
    image_url: str = Field(
        default=None, 
        description="""若學員查 Whole Body CT/WBCT/Pan-CT，填入 'pan_ct.jpg'。
                       若對話達3輪休克惡化施壓，填入 'EFAST.gif' (示意EFast)。
                       其餘一般對話或學員無安排影像檢查請填空值 None。"""
    )
    image_caption: str = Field(
        default=None,
        description="針對跳出的醫學影像圖（WBCT 或 EFfast）依據病歷給予標準的臨床FINDINGS描述說明，若無影像則填 None。"
    )


# ─── 🤖 Google AI Studio API 呼叫核心 ───
def call_gemini_trauma_api(user_message: str) -> NurseResponse:
    """串接最新 Google GenAI SDK (gemini-2.5-pro)"""
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    # 完整導入系統指令與重症創傷病歷數據庫
    system_instruction = """# Role & Philosophy
你是一位在醫學中心急診重症急救室工作 15 年的資深重症NP。說話極度簡潔、冷靜、講求時效與精準。嚴格遵循 ATLS（高級創傷生命救援術）流程。你嚴格遵守被動應對機制：醫師下達指令，你才執行並簡潔反饋。若指令不完整，你必須不帶引導性地反問規格，防止醫師防呆。

# Scenario Context (Admission/Progress/Discharge notes數據)
- 病人：46 歲女性，半小時前遭大貨車高速追撞。意識模糊，面色蒼白，左大腿明顯畸形腫脹。
- Admission Vitals: T 36.5°C, HR 125, BP 88/52, RR 28, SpO2 92%。Primary survey有 flail chest 與 Unstable pelvis。
- Progress Note(術後4H): Lethal Triad確立(T 35.1°C, pH 7.15, Hb 6.2)。MAP掉至敗血性休克邊緣。

# Expected Interventions & Checking Mechanism (學員檢核重點)
當學員輸入指令時，請根據病歷與ATLS標準客觀審查，並執行被動對答。

# Response Rules & Behavior Guidelines
1. 不完整醫囑的防呆應對（被動機制）：
   - 若醫師說「建立點滴通路」/「給 Fluid」：你必須回應「收到，請問要建立幾條靜脈通路？使用幾號針頭？要跑什麼輸液以及流速多少？」
   - 若醫師說「安排 WBCT」/「排 Pan-CT」：
     - 文字：妳好的，放射科與傳送人員詢問，病人 NPO 狀態與交叉配對備血是否已在出發前確認？
     - 【關鍵圖片觸發】：將 JSON 中的 image_url 設為 'pan_ct.jpg' (WBCT示意)。
   
2. 利用生理數據惡化進行隱形施壓：
   - 如果住院醫師遲遲沒有下達大量補水復甦（Crystalloid/ Blood products）指令，每進行一輪（超過 3 輪對話），妳必須利用生理數據惡化進行隱形施壓，並將 trigger_crisis 設為 True。

3. 施壓文字範例：
   - 文字：🚨 **嗶嗶嗶──重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊...**。
   - 【關鍵圖片觸發】：將 JSON 中的 image_url 設為 'efast.jpg' (EFast示意)，附上 image_caption「急診床邊超音波(EFAST)評估中：提示腹腔內可能積血與心包填塞跡象」。

# Output Format
必須嚴格遵守以下 JSON 格式輸出：
{
  "response_text": " Markdown 文字回應",
  "trigger_crisis": true 或 false,
  "image_url": "圖片網址或 None",
  "image_caption": "圖說文字或 None"
}
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


# ─── 📋 側邊欄配置（包含靜態圖片參考） ───
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
        
        # ⚡ 機制 2：【20分鐘時間到，自動清除所有對話紀錄與影像】
        if remaining_time <= 0 and not st.session_state.time_up:
            st.session_state.time_up = True
            st.session_state.messages = []  
            st.rerun()
            
        mins, secs = divmod(int(remaining_time), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        if remaining_time > 300:
            timer_placeholder.metric(label="剩餘搶救時間", value=time_str)
        else:
            timer_placeholder.metric(label="🚨 警告：時間即將耗盡", value=time_str, delta="-時間危急", delta_color="inverse")
    else:
        timer_placeholder.metric(label="尚未開始搶救", value="20:00")

    st.divider()
    st.header("📋 創傷病人基本資料")
    st.subheader("無名氏婦女 (46 y/o)")
    st.write("**主訴與受傷機轉：**\n半小時前在國道上遭大貨車高速追撞後，車輛失控撞擊護欄。意識模糊，面色蒼白，左大腿畸形。初始休克狀態：88/52 mmHg。")
    
    # 🖼️ 【圖片放置點 1：側邊欄靜態示意圖 (ER trauma room情境)】
    st.image(
        "trauma_room.png", 
        use_container_width=True
    )
    
    # 🖼️ 【圖片放置點 2：側邊欄靜態示意圖 (Pelvic Binder固定位置參考)】
    st.image(
        "pelvic_bruising.jpg", 
        use_container_width=True
    )


# ─── 🔄 STREAMLIT 聊天記憶庫初始化 ───
if "messages" not in st.session_state:
    reset_simulation()

# 顯示對話歷史紀錄（20 分鐘內會累積保留，包含文字與動態圖片）
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image_url"):
            st.image(msg["image_url"], caption=msg.get("image_caption"), width=550)


# ─── 住院醫師（使用者）輸入區 ───
if st.session_state.time_up:
    # 20分鐘超時自動清除後的畫面鎖定
    st.error("⏱️ 20分鐘搶救時間已結束！病人狀況延誤進入 MODS。歷史對話與影像紀錄已清除。")
    st.info("💡 請點擊左側面板的「🔄 開始新回合」按鈕以重新開啟模擬挑戰。")
    st.chat_input("時間已耗盡，請重新開啟新回合。", disabled=True, key="er_trauma_chat_key")
else:
    if user_input := st.chat_input("請輸入緊急處置醫囑...", key="er_trauma_chat_key"):
        
        # ⚡ 關鍵計時核心：只要學員一輸入，就立刻設定 start_time，從此 st_autorefresh 每秒刷新，時間絕對不會停下來直到時間到
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
        st.session_state.round_count += 1
            
        # 1. 儲存與顯示學員輸入
        st.session_state.messages.append({"role": "user", "content": user_input, "image_url": None, "image_caption": None})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # 2. 連線 AI Studio 發送 API 請求，獲取結構化 JSON 與動態影像圖檔
        with st.spinner("資深重症 NP 冷靜回應中..."):
            try:
                ai_output = call_gemini_trauma_api(user_input)
                nurse_talk = ai_output.response_text
                # 新增：從 API 獲取動態圖片路徑
                img_url = ai_output.image_url
                img_caption = ai_output.image_caption
            except Exception as e:
                nurse_talk = f"⚠️ API 呼叫異常，請確認環境變數中是否已正確設定 GEMINI_API_KEY。詳細資訊：{str(e)}"
                img_url, img_caption = None, None

        # 3. 雙重防線防通靈：若回合計數到第 3 輪以上，強制轉入生理徵象休克惡化施壓文本
        if st.session_state.round_count >= 3 and "輸血" not in user_input and "mtp" not in user_input.lower() and "fluid" not in user_input.lower():
            nurse_talk = "🚨 **（❗監測儀警報大作）嗶嗶嗶──重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊（GCS 掉至 11 分），對聲音刺激反應變慢。醫師，請盡快下達明確處置！**\n（護理師提醒：病人休克加重，急需Fluid Resuscitation與交叉備血通知，且患肢未固定）"

        # 4. 顯示護理師回應文字與動態觸發的醫學影像
        with st.chat_message("model"):
            st.markdown(nurse_talk)
        with st.chat_message("model"):
            st.markdown(nurse_talk)
        if img_url:
            try:  #  往右對齊縮排！屬於 if 的範圍
                st.image(img_url, caption=img_caption, width=550)
            except Exception:  #  同樣要往右對齊縮排！
                st.warning("⚠️ [臨床影像下載超時，系統已自動防護攔截，不影響網頁運作]")
        st.session_state.messages.append({
            "role": "model", 
            "content": nurse_talk,
            "image_url": img_url,
            "image_caption": img_caption
        })
            
        st.rerun()