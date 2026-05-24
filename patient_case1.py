CASE_DATA = {
    "case_meta": {
        "case_id": "TRAUMA-2026-046",
        "patient_name": "無名氏婦女 (46 y/o)",
        "age": 46,
        "gender": "Female",
        "scenario": (
            "46歲婦女在國道上車禍遭後方大貨車高速追撞後，車輛失控撞擊護欄且側邊受擊。"
            "當下安全氣囊已彈出，車體嚴重變形，且受困車內約20分鐘，由119送醫並以頸圈及長背板固定，到院後神智模糊。"
        )
    },
    
    "vitals_initial": {
        "BP": "88/52 mmHg (Shock)",
        "HR": "128 bpm (Tachycardia)",
        "RR": "28 bpm (Tachypnea)",
        "SpO2": "92% on NRM 15L",
        "BT": "36.2°C"
    },
    
    "medical_records": {
        "admission_note": """
【Admission Note】
Date/Time: 2026-05-06 15:00
Patient: 46 y/o Female
Chief Complaint: Altered consciousness and multiple injuries following a high-speed MVA.

Present Illness:
This 46-year-old female was involved in a high-speed rear-end collision with subsequent side impact and entrapment. On arrival, she was confused but responsive to painful stimuli. Due to the severe mechanism of injury, multiple fractures are suspected.

Primary Survey & Management:
- Airway: Patent with spontaneous breathing. Although oral blood and fractured teeth are noted, the patient maintains her own airway; therefore, endotracheal intubation is deferred to avoid aggravating potential C-spine injury.
- Breathing: RR 28, SpO2 92% on NRM 15L. Right chest bruising with paradoxical breathing noted. Plan: Apply tight chest elastic bandage wrapping to stabilize the flail segment and improve ventilation efficiency.
- Circulation: BP 88/52, HR 128. Cold extremities. Unstable pelvis on palpation. Management: Rapid infusion of 3,000 mL Normal Saline to restore blood pressure. Pelvic binder is deferred until Pelvis X-ray confirms fracture type to avoid unnecessary skin pressure.
- Disability: GCS E2V3M5 (Total 10). Pupils symmetric (3.0mm/3.0mm), Light reflex (+).
- Exposure: Right femur open fracture with active bleeding. Management: Immediate wound closure in the ER followed by a pressure dressing.

Initial Assessment:
1. Polytrauma with hemorrhagic shock.
2. Right flail chest.
3. Unstable pelvic fracture.
4. Right open femur fracture.

Plan:
1. Aggressive crystalloid resuscitation.
2. Arranged for Whole Body CT (WBCT) once BP > 90 mmHg.
3. Orthopedic consultation for definitive ORIF tonight to stabilize the femur and pelvis simultaneously.
""",

        "progress_note": """
【Progress Note】
Date/Time: 2026-05-07 02:00 (Post-OP Hour 4)
Subjective:
Patient underwent an 8-hour definitive surgery for pelvic ORIF and femur nailing.

Objective:
- Vital Signs: T: 35.1°C (Hypothermia), HR: 142 bpm, BP: 82/40 mmHg (on Dopamine).
- Physical Exam: Diffuse oozing from surgical wounds and IV sites. Abdomen is distended and firm.
- Labs:
  * Hb: 6.2 g/dL (dropped from 10.5).
  * pH: 7.15, HCO3: 14 mmol/L, Lactate: 8.5 mmol/L (Worsening metabolic acidosis).
  * PT/aPTT: Significantly prolonged (> 2x control).
- Urine Output: < 10 mL/hr for the last 4 hours.

Assessment:
1. Post-operative persistent hypotension, likely due to inadequate fluid volume.
2. Developing Acute Respiratory Distress Syndrome (ARDS).
3. Post-traumatic coagulopathy.

Plan:
1. Continue Normal Saline infusion (another 2,000 mL).
2. Increase Dopamine dose to maintain MAP > 65 mmHg.
3. Re-check labs in 4 hours.
""",

        "discharge_note": """
【Discharge Note】
Date: 2026-05-12
Discharge Diagnosis:
1. Polytrauma with irreversible Multi-Organ Dysfunction Syndrome (MODS).
2. Refractory Hemorrhagic Shock.
3. Disseminated Intravascular Coagulation (DIC).

Brief Clinical Course:
The patient was admitted with multiple traumas and initial shock. Despite aggressive crystalloid resuscitation (total 7,000 mL in the first 12 hours) and a successful 8-hour definitive surgical fixation of the pelvis and femur, the patient’s condition deteriorated rapidly post-operatively. 

She developed the Lethal Triad (hypothermia, acidosis, and coagulopathy). Despite maximal vasopressor support and late initiation of blood products, the patient progressed to MODS. Following a discussion with the family regarding the poor prognosis, a "Do Not Resuscitate" (DNR) order was signed. The patient expired on Day 6 of admission.
"""
    },
    
    # ─── 臨床檢查快捷鍵對應數據 ───
    "diagnostic_results": {
        "WBCT": (
            "【全景創傷電腦斷層報告 (WBCT)】\n"
            "- Chest: Multiple rib fractures from R't 3rd to 8th ribs with flail segment. Moderate right hemothorax.\n"
            "- Abdomen/Pelvis: Disruption of the sacroiliac joint and pubic symphysis diastasis (>3cm, Open Book type). "
            "Massive retroperitoneal hematoma extending to the paracolic gutter. Active contrast extravasation noted (出血中!).\n"
            "- Extremities: Comminuted open fracture of the right femur shaft with surrounding soft tissue hematoma."
        ),
        "Blood_Products_MTP": (
            "【血庫與大量輸血回報】\n"
            "通知血庫啟動 MTP (大量輸血流程)。\n"
            "目前急診並未第一時間給予血液製品，護理師回報：『學長，急診剛剛都在灌 Normal Saline，"
            "手術室開進去之後才開始叫大批的 pRBC, FFP 和 Platelets。但那時候病人已經開始 diffuse oozing (全身到處滲血) 了...』"
        ),
        "Pelvic_Binder_Check": (
            "【理學檢查 / 骨盆固定評估】\n"
            "骨盆橫向壓迫測試呈現明顯不穩定與骨擦音（Crepitus）。\n"
            "護理師說：『學長！急診當時為了等床邊 X-ray，真的沒有幫病人綁 Pelvic binder 或是用床單固定。"
            "在送去開刀房前，病人的骨盆處瘀青範圍明顯擴大，血壓一直掉。』"
        ),
        "Recheck_Vitals": (
            "【術後即時評估 - 致命三聯症確認】\n"
            "病人目前 T: 35.1°C, pH: 7.15, PT/aPTT 延長超過兩倍。\n"
            "這是典型的 Lethal Triad（低體溫、重度酸中毒、凝血功能障礙）。"
        )
    },
    
    # ─── 講評標準答案 ───
    "hidden_truth": {
        "pre_班_error": "急診與外科團隊在初期處置上犯了多項違反高級創傷生命支持（ATLS）與損害管制復甦（DCR）的嚴重錯誤，直接導致病人死於致命三聯症。",
        "correct_diagnosis": "Severe Polytrauma with Lethal Triad induced by Inappropriate Resuscitation & Over-surgery.",
        "missed_clues": [
            "❌ 錯誤 1 (Breathing)：對連枷胸（Flail chest）施加緊繃帶包紮。這會嚴重壓迫胸廓、限制肺部擴張，進一步惡化低血氧並加速酸中毒！正確做法應是維持氧合，必要時直接插管使用正壓通氣。",
            "❌ 錯誤 2 (Circulation)：出血性休克卻狂灌 3,000+2,000 mL 的 Normal Saline。過多的晶體溶液會破壞微小血栓、稀釋凝血因子、降低體溫，直接引爆致命三聯症（Lethal Triad）。應該實施限制性復甦並儘早啟動大量輸血流程（MTP）。",
            "❌ 錯誤 3 (Circulation)：骨盆不穩定卻延遲使用 Pelvic binder。Open-book型骨盆骨折會導致後腹腔大量失血，摸到不穩定就應立即在床邊固定止血，絕不能為了等 X-ray 而延誤。",
            "❌ 錯誤 4 (Exposure)：在急診直接縫合開放性骨折（Immediate wound closure）。這違反了污染傷口處置原則，極易將細菌及壞死組織鎖在深層。",
            "❌ 錯誤 5 (Plan/Surgery)：違反損害管制外科（Damage Control Surgery, DCS）原則。病人在嚴重休克與三聯症邊緣，竟然安排了長達 8 小時的解剖復位根治手術（definitive ORIF），這無異於在病人身上實施第二次打擊（Second Hit），直接加速死亡。"
        ]
    }
}