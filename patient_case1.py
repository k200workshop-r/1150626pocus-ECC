CASE_DATA = {
    "case_meta": {
        "case_id": "TRAUMA_CASE_002",
        "scenario": (
            "46歲婦女在國道上車禍遭後方大貨車高速追撞後，車輛失控撞擊護欄且側邊受擊，"
            "當下安全氣囊已彈出，車體嚴重變形，且受困車內約20分鐘，由119送醫並以頸圈及長背板固定，"
            "到院後神智模糊。"
        )
    },
    "vitals_initial": {
        "Temperature": "36.2 °C",
        "Heart Rate (HR)": "128 bpm",
        "Respiratory Rate (RR)": "28 bpm",
        "Blood Pressure (BP)": "88/52 mmHg",
        "SpO2": "92% (on NRM 15L)"
    },
    "medical_records": {
        "admission_note": """[Admission Note]
Date/Time: 2026-05-06 15:00
Patient: 46 y/o Female
Chief Complaint: Altered consciousness and multiple injuries following a high-speed MVA.

Present Illness:
This 46-year-old female was involved in a high-speed rear-end collision with subsequent side impact and entrapment. On arrival, she was confused but responsive to painful stimuli. Due to the severe mechanism of injury, multiple fractures are suspected.

Primary Survey & Management:
- Airway: Patent with spontaneous breathing. Although oral blood and fractured teeth are noted, the patient maintains her own airway; therefore, endotracheal intubation is deferred to avoid aggravating potential C-spine injury.
- Breathing: RR 28, SpO2 92% on NRM 15L. Right chest bruising with paradoxical breathing noted. Plan: Apply tight chest elastic bandage wrapping to stabilize the flail segment and improve ventilation efficiency.
- Circulation: BP 88/52, HR 128. Cold extremities. Unstable pelvis on palpation. Management: Rapid infusion of 3,000 mL Normal Saline to restore blood pressure. Pelvic binder is deferred until Pelvis X-ray confirms fracture type to avoid unnecessary skin pressure.
- Disability: GCS E2V3M5. Pupils symmetric.
- Exposure: Right femur open fracture with active bleeding. Management: Immediate wound closure in the ER followed by a pressure dressing.

Initial Assessment:
1. Polytrauma with hemorrhagic shock.
2. Right flail chest.
3. Unstable pelvic fracture.
4. Right open femur fracture.

Plan:
- Aggressive crystalloid resuscitation.
- Arranged for Whole Body CT (WBCT) once BP > 90 mmHg.
- Orthopedic consultation for definitive ORIF tonight to stabilize the femur and pelvis simultaneously.""",

        "progress_note": """[Progress Note]
Date/Time: 2026-05-07 02:00 (Post-OP Hour 4)
Subjective: Patient underwent an 8-hour definitive surgery for pelvic ORIF and femur nailing.

Objective:
- Vital Signs: T: 35.1°C (Hypothermia), HR: 142 bpm, BP: 82/40 mmHg (on Dopamine).
- Physical Exam: Diffuse oozing from surgical wounds and IV sites. Abdomen is distended and firm.
- Labs:
  * Hb: 6.2 g/dL (dropped from 10.5).
  * pH: 7.15, HCO3: 14 mmol/L, Lactate: 8.5 mmol/L (Worsening acidosis).
  * PT/aPTT: Significantly prolonged (> 2x control).
- Urine Output: < 10 mL/hr for the last 4 hours.

Assessment:
1. Post-operative persistent hypotension, likely due to inadequate fluid volume.
2. Developing Acute Respiratory Distress Syndrome (ARDS).
3. Post-traumatic coagulopathy.

Plan:
- Continue Normal Saline infusion (another 2,000 mL).
- Increase Dopamine dose to maintain MAP > 65 mmHg.
- Re-check labs in 4 hours."""
    },
    "diagnostic_results": {
        "WBCT": (
            "【全景創傷電腦斷層 (WBCT) 報告】\n"
            "1. 右側多根肋骨骨折伴隨連枷胸 (Flail Chest) 與血氣胸。\n"
            "2. 骨盆嚴重骨折變形 (Open-Book Pelvic Fracture)，且後腹腔可見 active extravasation (動態活動性大出血)。\n"
            "3. 腹腔與後腹腔大量血腫。"
        ),
        "Blood_Products_MTP": (
            "【輸血與大量輸血協定 (MTP) 紀錄】\n"
            "急診及術中前段皆以生理食鹽水Resuscitation為主。大量輸血協定（Packed RBC:FFP = 1:1）直到術後第3個小時（病患全身 diffuse oozing）才正式啟動，目前正處於備血延遲狀態。"
        ),
        "Pelvic_Binder_Check": (
            "【護理紀錄：骨盆固定帶確認】\n"
            "急診當時因計畫安排 Pelvis X-ray 及 WBCT 以釐清骨折分型，『暫不予以綁上 Pelvic binder』，避免皮膚壓傷。病患送入手術室前，骨盆及周圍血腫範圍有肉眼可見的顯著擴大。"
        ),
        "Recheck_Vitals": (
            "【動態檢驗數據評估：致命三聯症 Lethal Triad】\n"
            "- 體溫：35.1°C (嚴重失溫)\n"
            "- 酸鹼度：pH 7.15 (嚴重代謝性酸中毒)\n"
            "- 凝血功能：PT/aPTT 超過正常值 2 倍 (嚴重凝血功能障礙)\n"
            "👉 病患已完全進入創傷致命三聯症的醫源性連鎖悲劇。"
        )
    },
    "hidden_truth": {
        "correct_diagnosis": "骨盆開放型骨折引發之後腹腔嚴重出血性休克，併創傷致命三聯症 (Lethal Triad) 與醫源性處置失當。",
        "pre_班_error": (
            "1. 違反 ATLS 復甦準則：對出血性休克過度灌注晶體溶液 (3,000+2,000mL NS)，導致血液稀釋及低體溫，加劇凝血障礙。\n"
            "2. 未進行緊急骨盆固定：Unstable pelvis 應立即在床邊使用 Pelvic binder，而非為了等 X-ray 分型而延遲固定，造成後腹腔空間擴大並持續大出血。\n"
            "3. 缺乏損害管制手術 (Damage Control Surgery) 概念：病人已處於嚴重休克與三聯症早期，骨科卻進行了長達 8 小時的確定性內固定手術 (Definitive ORIF)，而非使用外固定後送 ICU 復甦，導致病人在手術台上耗盡所有凝血因子。"
        ),
        "missed_clues": [
            "❌ 盲點 1：急診對連枷胸使用『彈性繃帶緊綁』(Elastic bandage wrapping)，這會嚴重限制胸廓起伏，進一步惡化缺氧並誘發後續的呼吸衰竭。",
            "❌ 盲點 2：術後低血壓與擴散性滲血 (Diffuse oozing) 是典型的凝血功能瓦解，此時 Plan 居然是『繼續灌 2,000mL 生理食鹽水』並狂加升壓劑 (Dopamine)，這會把殘存的血塊沖刷掉，無異於雪上加霜。",
            "❌ 盲點 3：急診為了避免插管加重頸椎損傷而推遲氣道處置 (Deferred intubation)，但在 RR 28、神智模糊 (GCS 10分) 的 polytrauma 病人身上，應改用 MILS (手動軸向穩定) 立即建立安全氣道。"
        ]
    }
}
