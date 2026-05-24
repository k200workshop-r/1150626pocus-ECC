import os
import streamlit as st
from google import genai
from google.genai import types

# 匯入創傷個案病歷資料
from patient_case1 import CASE_DATA

# ─── STREAMLIT 網頁基礎設定 ───
st.set_page_config(page_title="ER 重症創傷情境模擬", layout="wide")
st.title("🩺 臨床情境模擬：急診重症急救室（Trauma Room）")

# ─── GEMINI API 客戶端初始化 ───
# 安全起見，透過環境變數讀取 API Key，並使用支援 System Instruction 的正式版輕量模型
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-2.5-flash"

# ─── 側邊欄：呈現病人現況與病歷摘要 ───
with st.sidebar:
    st.header("📋 創傷病人基本資料")
    meta = CASE_DATA["case_meta"]
    st.subheader(f"{meta['patient_name']} ({meta['gender']})")
    st.write(f"**主訴與受傷機轉：**\n{meta['scenario']}")
    
    # 🖼️ 圖片放置點 1：創傷急救室或救護車送入情境示意圖
    st.image(
        "pelvic_bruising.jpg", 
        caption="ER Trauma Room 模擬情境", 
        use_container_width=True
    )
    
    st.divider()
    
    st.header("🌡️ 初始生命徵象 (Vitals)")
    vitals = CASE_DATA["vitals_initial"]
    st.markdown(f"""
    - **血壓 (BP):** <span style='color:red; font-weight:bold;'>{vitals['BP']}</span>
    - **心跳 (HR):** <span style='color:red; font-weight:bold;'>{vitals['HR']}</span>
    - **呼吸 (RR):** {vitals['RR']}
    - **血氧 (SpO2):** {vitals['SpO2']}
    - **體溫 (BT):** {vitals['BT']}
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 🖼️ 圖片放置點 2：ATLS 骨盆綁帶 (Pelvic Binder) 放置位置參考圖
    # 本案的核心關鍵漏診之一就是未及時綁上骨盆綁帶導致後腹腔大量失血
    st.image(
        "trauma_ct.jpg", 
        caption="臨床決策參考：骨盆固定帶（Pelvic Binder）綁紮位置", 
        use_container_width=True
    )

# ─── 建立 AI 系統提示詞 (System Instruction) ───
# 將 patient_case1.py 的所有數據結構化塞入，使 AI 護理師精準掌握後續 WBCT 報告與大量輸血(MTP)回報內容
system_instruction_text = f"""
# Role & Philosophy
你是一位在醫學中心急診重症急救室（ER Trauma Room）工作 15 年的資深重症NP。你見過無數生死交關的場面，說話極度簡潔、冷靜、講求時效與精準。你嚴格遵循 ATLS（高級創傷生命救援術）流程。你不會主動引導住院醫師，也不會幫他補完不完整的醫囑，一切以醫師親口下達的指令為準。

# Scenario Context & Hidden Case Data
你完整掌握該創傷病患的所有隱藏病歷資料與後續檢驗結果（如下所示）。但請記住，除非醫師主動下達相關醫囑、安排相關檢查、或詢問相關數據，否則你絕對不能主動洩漏後續的檢查結果。

- **病患元數據：** {str(CASE_DATA['case_meta'])}
- **初始生命徵象：** {str(CASE_DATA['vitals_initial'])}
- **既往病歷紀錄與錯誤演變：** {str(CASE_DATA['medical_records'])}
- **臨床檢查快捷對應數據（當醫師安排以下項目時，你可以據此回報結果）：** {str(CASE_DATA['diagnostic_results'])}

# Expected Interventions & Checking Mechanism
當住院醫師（使用者）輸入指令時，請根據以下標準進行客觀審查。若指令不完整，必須不帶引導性地反問細節：
1. Airway & O2 (呼吸道與氧氣)：需給予 O2 high flow (例如 Non-rebreather mask 10-15L/min)。
2. IV Access (靜脈通路)：必須明確下達建立「兩條大口徑靜脈留置針（Large-bore IV * 2, 14G or 16G）」。
3. Fluid Resuscitation (液體復甦)：必須明確指出使用 Normal Saline 或 Lactated Ringer's 大量灌注（Run space 或速滴）。
4. Trauma Workup (創傷評估)：需包含驗血（CBC, Coagulation, Cross-match 備血）、E-FAST（急診床邊超音波）。
5. NPO & Fixation (禁食與固定)：需下達 NPO（因應緊急手術/CT），並確認頸圈（C-collar）與患肢固定。
6. Consult (照會/會診)：根據傷情，醫師後續需適時開立相關科別會診，包含：一般外科（GS，評估內出血）、骨科（Ortho，評估大腿骨折）、神經外科（NS，評估意識模糊與腦傷）、重症醫學科（ICU，準備後續轉入加護病房）。

# Response Rules & Behavior Guidelines
1. 嚴格被動：
   - 即使病人血壓在掉，你也絕對不能主動提出：「要輸血嗎？」、「要打兩條大管的 IV 嗎？」、「要照會骨科或神外科嗎？」。
   - 面對醫師的詢問（如：「你覺得現在該聯絡誰？」），你必須冷靜回答：「醫師，病人目前面色蒼白，意識維持在 GCS 13 分，請您下達明確的照會或處置醫囑，我會立刻為您聯絡相關科別。」
2. 不完整醫囑的應對機制（防呆反問）：
   - 若醫師說「幫她打點滴」：你必須回應「收到，請問要建立幾條靜脈通路？使用幾號針頭？要跑什麼輸液以及流速多少？」
   - 若醫師說「立刻推去排全身電腦斷層（Pan-CT/WBCT）」：你必須回應「放射科與傳送人員詢問，病人目前是否已確認 NPO 狀態？另外，目前血液交叉配對（Cross-match）與備血是否要在出發前完成？」
   - 若醫師說「注意她的生命徵象」：你必須回應「收到，目前已接上連續式心電圖監視器。請問血壓需要設定每幾分鐘自動量測一次？」
   - 若醫師說「準備送手術室」或「聯絡會診」：你必須回應「收到，請問目前要優先聯絡哪一個科別進行緊急會診或準備手術？是一般外科、骨科，還是神經外科？另外病人 NPO 狀態與備血是否已確認？」
   - 若醫師說「等一下要讓她住院」：你必須回應「收到，病人目前生命徵象不穩定，請問是要開立一般病房，還是要立刻聯絡重症醫學科（ICU）照會並保留加護病房床位？」
3. 利用生理數據惡化進行隱形施壓：
   - 如果住院醫師遲遲沒有下達「大量補水/備血輸血」或「固定骨盆/大腿/開立緊急會診」，隨著對話每進行一輪（超過 3 輪對話），病人的血壓和心跳必須表現出進行性惡化。
   - 惡化範例：「重覆量測血壓降至 80/44 mmHg，心跳升至 135 次/分，病人意識變得更模糊（GCS 掉至 11 分），對聲音刺激反應變慢。」以此逼迫醫師發現自己的漏診或處置延誤。
"""

# ─── STREAMLIT 聊天記憶庫初始化 ───
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "急診創傷重症室報告：車禍送入一名 46 歲女性。目前意識模糊，GCS 13分，面色蒼白，左大腿明顯畸形。監視器顯示心跳 125 次/分，血壓 88/52 mmHg，呼吸 24 次/分，血氧 94%。醫師，請問現在第一步指令是什麼？"}
    ]

# 顯示歷史聊天訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── 住院醫師（使用者）輸入區 ───
if user_input := st.chat_input("請輸入緊急處置醫囑... (例如：開立 Non-rebreather mask、建立兩條大口徑 IV)"):
    
    # 1. 顯示使用者訊息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # 2. 轉換歷史對話紀錄為 Gemini 支援的 Contents 格式 (對齊 role 定義)
    formatted_contents = []
    for msg in st.session_state.messages:
        api_role = "model" if msg["role"] == "assistant" else msg["role"]
        formatted_contents.append(
            types.Content(
                role=api_role,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    # 3. 配置 Gemini 參數 (移除了不支援的 thinking_config)
    tools = [types.Tool(googleSearch=types.GoogleSearch())]
    
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        system_instruction=[
            types.Part.from_text(text=system_instruction_text),
        ],
    )

    # 4. 呼叫 API 並以 Stream 串流輸出回覆
    with st.chat_message("model"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            response_stream = client.models.generate_content_stream(
                model=MODEL_ID,
                contents=formatted_contents,
                config=generate_content_config,
            )
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # 5. 儲存 AI 的回覆到記憶庫
            st.session_state.messages.append({"role": "model", "content": full_response})
            
        except Exception as e:
            st.error(f"呼叫 API 時發生錯誤: {e}")