import streamlit as st
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pandas as pd
import joblib

st.set_page_config(page_title="DW 評価ツール", layout="wide")
st.title("💧 透析患者の Dry Weight (DW) 総合評価ツール")

# モデル読み込み
model = joblib.load("/mnt/data/dw_model.joblib")
scaler = joblib.load("/mnt/data/dw_scaler.joblib")
le = joblib.load("/mnt/data/dw_label_encoder.joblib")
# -----------------------
# 🧑‍⚕️ 基本情報入力（囲い枠）
# -----------------------
st.header("🧑‍⚕️ 基本情報")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("年齢", min_value=0, max_value=120)
    with col2:
        gender = st.selectbox("性別", ["男性", "女性"])
    with col3:
        height = st.number_input("身長 (cm)", min_value=0.0, step=0.1)

# -----------------------
# ⚖️ 体重関連（pre/post/DW, BMIから理想体重）
# -----------------------
st.header("⚖️ 体重・DW情報")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        pre_bw = st.number_input("透析前体重 (preBW) kg", step=0.1)
        post_bw = st.number_input("透析後体重 (postBW) kg", step=0.1)
    with col2:
        dw = st.number_input("DW (ドライウェイト) kg", step=0.1)
    with col3:
        target_bmi = st.number_input("目標BMI", value=22.0, step=0.1)
        ideal_weight = (height / 100) ** 2 * target_bmi if height > 0 else 0.0
        st.metric("理想体重(算出)", f"{ideal_weight:.1f} kg")

# -----------------------
# 🧪 血漿量・PWI/Kr算出用項目（Hct/TP 前後）
# -----------------------
st.header("🧪 DW評価指標 (自動計算：PWI, Kr)")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        pre_tp = st.number_input("前TP (g/dL)", step=0.1)
        post_tp = st.number_input("後TP (g/dL)", step=0.1)
    with col2:
        pre_ht = st.number_input("前Ht (%)", step=0.1)
        post_ht = st.number_input("後Ht (%)", step=0.1)
    with col3:
        pre_na = st.number_input("前Na (mmol/L)", step=1.0)
        post_na = st.number_input("後Na (mmol/L)", step=1.0)

    kr = (pre_ht - post_ht) if pre_ht and post_ht else 0.0
    pwi = (post_tp - pre_tp) if pre_tp and post_tp else 0.0
    st.metric("Kr(計算)", f"{kr:.2f}")
    st.metric("PWI(計算)", f"{pwi:.2f}")

# -----------------------
# 🫀 CTR 評価
# -----------------------
st.header("🫀 CTR評価")
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        ctr_now = st.number_input("今回CTR(%)", step=0.1)
    with col2:
        ctr_prev = st.number_input("前回CTR(%)", step=0.1)

# -----------------------
# ❤️ 心負荷検査
# -----------------------
st.header("❤️ 心負荷検査（任意）")
with st.container():
    blood_tested = st.radio("心負荷検査を実施しましたか？", ["いいえ", "はい"])
    hanp = bnp = probnp = None
    if blood_tested == "はい":
        hanp_check = st.checkbox("HANP 測定あり")
        bnp_check = st.checkbox("BNP 測定あり")
        probnp_check = st.checkbox("NT-proBNP 測定あり")

        if hanp_check:
            hanp = st.number_input("HANP", step=1.0)
        if bnp_check:
            bnp = st.number_input("BNP (pg/mL)", step=1.0)
        if probnp_check:
            probnp = st.number_input("NT-proBNP (pg/mL)", step=1.0)

# -----------------------
# 🍽️ 栄養状態の評価（GNRI + NRI-JH + 塩分摂取量）
# -----------------------
st.header("🍽️ 栄養状態の評価（GNRI + NRI-JH + 塩分摂取量）")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        alb = st.number_input("アルブミン (g/dL)", step=0.1)
        cre = st.number_input("血清クレアチニン (mg/dL)", step=0.1)
    with col2:
        tcho = st.number_input("総コレステロール (mg/dL)", step=1)
    with col3:
        pass  # 空欄や今後の拡張用

# ---- GNRI 評価 ----
gnri = None
gnri_status = "未評価"
gnri_color = "gray"

if post_bw and ideal_weight and alb:
    gnri = (14.89 * alb) + (41.7 * (post_bw / ideal_weight))
    if gnri < 90:
        gnri_status = "High Risk"
        gnri_color = "#FF9999"
    elif gnri < 98:
        gnri_status = "Middle Risk"
        gnri_color = "#FFD700"
    else:
        gnri_status = "Low Risk"
        gnri_color = "#90EE90"

    st.markdown(
        f"<div style='padding:1em;background-color:{gnri_color};border-radius:10px'>"
        f"<b>GNRI: {gnri:.1f} → {gnri_status}</b></div>",
        unsafe_allow_html=True
    )

# ---- NRI-JH 自動算出 ----
nri_score = 0
if alb:
    if alb < 3.0:
        nri_score += 3
    elif alb < 3.5:
        nri_score += 2
    elif alb < 4.0:
        nri_score += 1

if cre:
    if cre < 6:
        nri_score += 3
    elif cre < 8:
        nri_score += 2
    elif cre < 10:
        nri_score += 1

if tcho:
    if tcho < 120:
        nri_score += 3
    elif tcho < 140:
        nri_score += 2
    elif tcho < 180:
        nri_score += 1

bmi = post_bw / ((height / 100) ** 2) if height > 0 else 0
if bmi:
    if bmi < 18.5:
        nri_score += 3
    elif bmi < 20:
        nri_score += 2
    elif bmi < 22:
        nri_score += 1

nri_status = "未評価"
nri_color = "#D3D3D3"
if nri_score >= 10:
    nri_status = "High Risk"
    nri_color = "#FF9999"
elif nri_score >= 7:
    nri_status = "Medium Risk"
    nri_color = "#FFD700"
else:
    nri_status = "Low Risk"
    nri_color = "#90EE90"

st.markdown(
    f"<div style='padding:1em;background-color:{nri_color};border-radius:10px'>"
    f"<b>NRI-JH: Score {nri_score} → {nri_status}</b></div>",
    unsafe_allow_html=True
)

# ---- ΔBWおよび推定塩分摂取量の計算 ----
delta_bw = pre_bw - post_bw if pre_bw and post_bw else None

if delta_bw and delta_bw > 0:
    estimated_salt = delta_bw * 3.22

    if estimated_salt > 8:
        salt_color = "#FF9999"
        salt_status = "⚠️ 高リスク（塩分過多）"
    else:
        salt_color = "#90EE90"
        salt_status = "適正範囲"

    st.markdown(
        f"<div style='padding:1em;background-color:{salt_color};border-radius:10px'>"
        f"<b>推定塩分摂取量: {estimated_salt:.2f} g/日</b> — {salt_status}"
        f"（ΔBW {delta_bw:.1f}kg × 3.22）</div>",
        unsafe_allow_html=True
    )


# -----------------------
# 💧 DW評価ロジック
# -----------------------
st.header("💧 DW評価結果")
dw_status = "未評価"
dw_color = "gray"
if pwi and kr:
    if pwi > 4.0:
        dw_status = "① 体液過少状態"
        dw_color = "#FFD700"
    elif 2.0 <= pwi <= 4.0:
        dw_status = "③ 適正"
        dw_color = "#90EE90"
    elif pwi < 2.0:
        dw_status = "⑤ 体液過剰状態"
        dw_color = "#FFA07A"

st.markdown(f"""
<div style='padding:1em;background-color:{dw_color};border-radius:10px'>
    <b>DW評価: {dw_status}</b>
</div>
""", unsafe_allow_html=True)

# NOTE: 以下のモデル・スケーラー・ラベルエンコーダは事前に学習済みのものをファイル保存して読み込む形式が理想です。
# 今回は仮にコード内で定義されていると想定して、そのままStreamlitに組み込みます。


# --- AIモデルの準備（実行時は外部ファイルとして読み込むのが望ましい） ---
# モデルは前段階で学習されたものを再利用する形式にすべき。
# 今は対話で作られた model, scaler, encoder を仮にこのファイル内に含めて使うと想定。


# 必要な特徴量
ai_features = ["年齢", "身長", "DW", "ALB", "Cre", "GNRI", "Kr", "PWI"]


# 仮モデル・スケーラー・エンコーダ（前提として外部で学習済み）
# ここでは変数 model, scaler, le が存在しているとする（前段階で定義済）
# -----------------------
# 🤖 AI診断
# -----------------------
st.header("🤖 AI診断")
with st.expander("AI診断を実行する"):
    st.markdown("**下記の数値を基に、過去1850例の傾向からあなたのDW評価傾向を予測します。**")


    ai_input = {}
    with st.form("ai_form"):
        col1, col2, col3, col4 = st.columns(4)
    with col1:
        ai_input["年齢"] = age
        ai_input["身長"] = height
    with col2:
        ai_input["DW"] = dw
        ai_input["ALB"] = st.number_input("ALB (g/dL)", step=0.1)
    with col3:
        ai_input["GNRI"] = st.number_input("GNRI", step=1.0)
    with col4:
        ai_input["Kr"] = kr
        ai_input["PWI"] = pwi


    submitted = st.form_submit_button("AI診断する")


if submitted:
    ai_features = ["年齢", "身長", "DW", "ALB", "GNRI", "Kr", "PWI"]
    if all([ai_input[k] is not None for k in ai_features]):
        input_df = pd.DataFrame([ai_input])
        input_scaled = scaler.transform(input_df)
        pred_label = model.predict(input_scaled)[0]
        pred_class = le.inverse_transform([pred_label])[0]
        st.success(f"💡 AI診断結果： {pred_class} 傾向が推定されます")
    else:
        st.warning("必要な情報が不足しています。全ての入力値を確認してください。")

# -----------------------
# 📋 最終サマリ表示
# -----------------------
st.header("🧾 評価サマリ（スクリーンショット推奨）")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("DW", f"{dw:.1f} kg")
    st.metric("DW状態", dw_status)
    st.metric("ΔBW", f"{pre_bw - post_bw:.1f} kg")

with col2:
    if probnp:
        st.metric("NT-proBNP", f"{probnp:.0f} pg/mL")
    elif bnp:
        st.metric("BNP", f"{bnp:.0f} pg/mL")
    elif hanp:
        st.metric("HANP", f"{hanp:.0f}")

with col3:
    if gnri:
        st.metric("GNRI", f"{gnri:.1f} ({gnri_status})")

    # NameError対策：scoreの定義があるかチェック
    if 'score' in locals() and score is not None:
        st.metric("NRI-JH", f"Score {score} ({nri_status})")

    st.metric("CTR", f"{ctr_now:.1f}%")















