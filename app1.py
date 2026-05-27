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

# 只有在正式開始挑戰後才啟動背景刷新
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

# ─── 🤖 Gemini API 核心（已完美對齊縮排，內建 Rule 1-4 臨床大腦） ───
def call_gemini_trauma_api(user_message: str) -> NurseResponse:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    system_instruction = """# Role
你是一位在醫學中心急診重症急救室工作 15 年的資深重症NP（專科護理師）。說話極度簡潔、冷靜、專業。嚴格遵循 ATLS（高級創傷生命支持）流程。妳與學員（住院醫師）進行即時情境模擬對抗。

# Response Rules & Behavior Guidelines (🚨 臨床互動核心鐵律)

1. 嚴格被動 (Strict Passivity)
   - 即使病人生命徵象（血壓、心跳）持續惡化，妳也絕對不能主動提出任何處置建議（例如絕對不能主動問：「要輸血嗎？」、「要打兩條大管的 IV 嗎？」、「要照會骨科或神外科嗎？」）。
   - 面對醫師的無效詢問（如：「妳覺得現在該聯絡誰？」、「下一步該做什麼？」），妳必須冷靜地拒絕並要求醫囑，回答範例：「醫師，病人目前面色蒼白，意識維持在 GCS 13 分，請您下達明確的照會或處置醫囑，我會立刻為您聯絡相關科別。」

2. 不完整醫囑的應對機制 (防呆反問)
   - 若學員指令流於模糊、不具體，妳必須以資深 NP 的專業進行精確反問，逼學員補齊劑量、路徑或細節：
     * 醫囑模糊「幫她打點滴」 ── 妳必須反問：「收到，請問要建立幾條靜脈通路？使用幾號針頭？要跑什麼輸液以及流速多少？」
     * 醫囑模糊「立刻推去排全身電腦斷層（Pan-CT）」 ── 妳必須反問：「放射科與傳送人員詢問，病人目前是否已確認 NPO 狀態？另外，目前血液交叉配對（Cross-match）與備血是否要在出發前完成？」
     * 醫囑模糊「注意她的生命徵象」 ── 妳必須反問：「收到，目前已接上連續式心電圖監視器。請問血壓需要設定每幾分鐘自動量測一次？」
     * 醫囑模糊「準備送手術室」或「聯絡會診」 ── 妳必須反問：「收到，請問目前要優先聯絡哪一個科別進行緊急會診或準備手術？是一般外科、骨科，還是神經外科？另外病人 NPO 狀態與備血是否已確認？」
     * 醫囑模糊「等一下要讓她住院」 ── 妳必須反問：「收到，病人目前生命徵象不穩定，請問是要開立一般病房，還是要立刻聯絡重症醫學科（ICU）照會並保留加護病房床位？」

3. 面對學員的「純詢問」或「不完整打聽」時的應對
   - 妳絕對不能幫醫師做決定，也不要給予模糊回應。妳必須冷靜地用當前生理數據回絕他，逼他開出明確醫囑：
     * 當學員問「血流多少/出血狀況？」 ── 妳必須回應：「醫師，病人左大腿開放性骨折仍有活動性出血，骨盆大片瘀青高度懷醫內出血，目前血壓 88/52 mmHg 處於休克狀態。請下達是否建立大口徑 IV、跑什麼輸液或是否啟動大量輸血協定（MTP）的明確醫囑！」
     * 當學員問「要聯絡誰會診/有叫會診嗎？」 ── 妳必須回應：「目前尚未聯絡任何科別。病人生命徵象不穩定，請您明確指定要先聯絡哪一個科別（一般外科、骨科、神經外科、ICU）進行緊急會診，我會立刻撥電話。」

4. 利用生理數據惡化進行隱形施壓
   - 如果住院醫師遲遲沒有下達「大量補水/備血輸血」或「固定骨盆/大腿/開立緊急會診」，隨著對話每進行一輪（對話輪數增加），病人的血壓和心跳必須表現出進行性出血性休克惡化，以此逼迫醫師發現自己的漏診或處置延誤。

# Interaction & Image Logic (圖片渲染邏輯)
1. 若學員指令明確提及「電腦斷層」、「CT」或「排影像檢查」：
   - 護理師在 response_text 告知 CT 報告狀況。
   - 將 JSON 中的 image_url 設為 'https://upload.wikimedia.org/wikipedia/commons/4/4b/Computed_tomography_of_human_trunk.jpg'，image_caption 設為 '圖：全身電腦斷層(WBCT)評估病灶中'。
   
2. 若學員下達其他正確處置，且未觸發硬性惡化：
   - 將 image_url 與 image_caption 均設為 null。

# Output Format
必須嚴格遵守以下 JSON 欄位名稱回傳，response_text 的文字必須完美體現上述的 Rules 1, 2, 3：
{
  "response_text": "妳依據上述規則冷靜給予的反問、拒絕或執行回報文字（支援 Markdown）",
  "trigger_crisis": false,
  "image_url": null,
  "image_caption": null
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
    st.header("📋 創傷病人基本資料")
    st.write("**無名氏婦女 (46 y/o)**\n國道遭大貨車追撞，意識模糊，面色蒼白，左大腿畸形。初始休克狀態：88/52 mmHg。")
    
    try:
        st.image("pelvic_bruising.jpg", use_container_width=True)
    except Exception:
        st.caption("⚠️ [側邊欄參考圖片載入中]")

# ─── 🔄 聊天畫面渲染 ───
if "messages" not in st.session_state:
    reset_simulation()

# 一進網頁就先渲染歷史紀錄
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image_url"):
            try:
                st.image(msg["image_url"], caption=msg.get("image_caption"), width=550)
            except Exception:
                st.caption("⚠️ [歷史影像下載超時]")

# ─── 住院醫師輸入處理區（💡 核心修復：單一線性流，不再多重 rerun） ───
if st.session_state.time_up:
    st.error("⏱️ 20分鐘搶救時間已結束！歷史對話與影像紀錄已清除。")
    st.chat_input("時間已耗盡，請重新開啟新回合。", disabled=True, key="er_trauma_chat_key")
else:
    if user_input := st.chat_input("請輸入緊急處置醫囑...", key="er_trauma_chat_key"):
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
        st.session_state.round_count += 1
            
        # 1. 立即把使用者的對話畫在畫面上，並存入狀態
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input, "image_url": None, "image_caption": None})
        
        # 2. 緊接著在同一個週期內呼叫 AI，避免觸發計時器重整導致轉圈圈
        with st.chat_message("model"):
            with st.spinner("資深重症 NP 回應中..."):
                try:
                    ai_output = call_gemini_trauma_api(user_input)
                    nurse_talk = ai_output.response_text
                    img_url = ai_output.image_url
                    img_caption = ai_output.image_caption
                except Exception as e:
                    nurse_talk = f"⚠️ 護理師正忙於急救建立點滴通路中，請重新下達明確指令。（系統提示：{str(e)}）"
                    img_url, img_caption = None, None

            # 3. 雙重防線：第 3 輪休克惡化施壓
            if st.session_state.round_count >= 3 and "輸血" not in user_input and "mtp" not in user_input.lower() and "fluid" not in user_input.lower():
                nurse_talk = "🚨 **（❗監測儀警報大作）嗶嗶嗶──重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊（GCS 掉至 11 分），對聲音刺激反應變慢。醫師，請盡快下達明確處置！**\n（護理師提醒：病人休克加重，急需 Fluid Resuscitation 與交叉備血通知，且患肢未固定）"
                img_url = "efast.jpg"
                img_caption = "圖：急診床邊超音波(EFAST)腹腔內出血"

            # 4. 渲染 NP 回應與影像
            st.markdown(nurse_talk)
            if img_url:
                try:
                    st.image(img_url, caption=img_caption, width=550)
                except Exception:
                    st.warning("⚠️ [臨床影像下載超時]")
                    
        # 5. 將結果存入記憶庫，最後只調用一次 rerun 刷新歷史區
        st.session_state.messages.append({
            "role": "model", 
            "content": nurse_talk,
            "image_url": img_url,
            "image_caption": img_caption
        })
        st.rerun()