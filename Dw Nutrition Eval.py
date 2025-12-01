import streamlit as st
import numpy as np

st.set_page_config(page_title="DW 評価ツール", layout="wide")
st.title("💧 透析患者の Dry Weight (DW) 総合評価ツール")

# -----------------------
# 入力フォーム
# -----------------------
st.header("🔢 基本情報・臨床データ入力")
col1, col2, col3 = st.columns(3)

with col1:
    age = st.number_input("年齢", min_value=0, max_value=120)
    gender = st.selectbox("性別", ["男性", "女性"])
    pre_bw = st.number_input("透析前体重 (preBW) kg", step=0.1)
    post_bw = st.number_input("透析後体重 (postBW) kg", step=0.1)
    dw = st.number_input("DW (ドライウェイト) kg", step=0.1)

with col2:
    kr = st.number_input("Kr", step=0.1)
    pwi = st.number_input("PWI", step=0.1)
    bp = st.number_input("収縮期血圧 (BP)", step=1)
    ctr_now = st.number_input("今回CTR(%)", step=0.1)
    ctr_prev = st.number_input("前回CTR(%)", step=0.1)

with col3:
    alb = st.number_input("Alb (g/dL)", step=0.1)
    ideal_weight = st.number_input("理想体重 (kg)", step=0.1)
    hanp = st.number_input("HANP", step=1.0)
    bnp = st.number_input("BNP (pg/mL)", step=1.0)
    probnp = st.number_input("NT-proBNP (pg/mL)", step=1.0)
    arrhythmia = st.checkbox("不整脈あり")

# -----------------------
# 自動計算・補足表示
# -----------------------
delta_bw = pre_bw - post_bw if pre_bw and post_bw else 0.0
st.info(f"ΔBW（増加量）: {delta_bw:.1f} kg")

# CTR増加判定
ctr_alert = False
if ctr_now and ctr_prev:
    if ctr_now - ctr_prev >= 5.0:
        ctr_alert = True

# -----------------------
# 🧪 水分バランス評価
# -----------------------
st.header("💧 水分状態の評価")
status = "判定不能"
color = "gray"

if pwi and kr and bp:
    if pwi > 4.0:
        status = "① 体液過少状態"
        color = "#FFD700"
    elif 2.0 <= pwi <= 4.0:
        if 100 <= bp < 160:
            status = "③ 適正"
            color = "#90EE90"
        elif bp < 100:
            status = "① 体液過少状態"
            color = "#FFD700"
        else:
            status = "⑤ 体液過剰状態"
            color = "#FFA07A"
    elif pwi < 2.0:
        status = "⑤ 体液過剰状態"
        color = "#FFA07A"

st.markdown(f"<div style='padding:1em;background-color:{color};border-radius:10px'><b>DW評価: {status}</b></div>", unsafe_allow_html=True)

# CTR基準
if ctr_now:
    ctr_threshold = 50.0 if gender == "男性" else 55.0
    if ctr_now > ctr_threshold or ctr_alert:
        st.warning("CTRが基準を超えています。Wetの可能性あり。")

# -----------------------
# ❤️ 心負荷指標評価
# -----------------------
st.header("❤️ 心負荷・BNP評価")
if arrhythmia:
    st.warning("⚠️ 不整脈があるため、BNP/proBNPの評価は参考指標となります。")
else:
    if probnp:
        if probnp >= 8000:
            st.error("NT-proBNPが高値です（心不全・心機能異常の可能性）")
        else:
            st.success("NT-proBNPは許容範囲内です（<8000pg/mL）")

# -----------------------
# 🍽️ 栄養評価
# -----------------------
st.header("🍽️ 栄養状態の評価")
gnri = None
if alb and ideal_weight:
    gnri = (14.89 * alb) + (41.7 * (post_bw / ideal_weight)) if post_bw else None
    if gnri:
        if gnri < 92:
            gstatus = "High Risk"
            gcolor = "#FF9999"
        elif 92 <= gnri <= 98:
            gstatus = "Middle Risk"
            gcolor = "#FFD700"
        else:
            gstatus = "Low Risk"
            gcolor = "#90EE90"
        st.markdown(f"<div style='padding:1em;background-color:{gcolor};border-radius:10px'><b>GNRI: {gnri:.1f} → {gstatus}</b></div>", unsafe_allow_html=True)

# -----------------------
# 📋 画面サマリ
# -----------------------
st.header("🧾 総合判定サマリ（スクリーンショット推奨）")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("DW状態", status)
    st.metric("ΔBW", f"{delta_bw:.1f} kg")

with col2:
    st.metric("NT-proBNP", f"{probnp:.0f} pg/mL")
    st.metric("不整脈", "あり" if arrhythmia else "なし")

with col3:
    if gnri:
        st.metric("GNRI", f"{gnri:.1f} → {gstatus}")
    st.metric("CTR", f"{ctr_now:.1f}%")

st.markdown("""
---
📌 **スクリーンショット推奨**：この画面全体をコピー・保存してレポート利用してください。
📖 **参考文献**：[NT-proBNP研究（透析会誌）](https://example.com/pdf_link_placeholder)
""")
