import streamlit as st
import pandas as pd
import io

# Fungsi pemrosesan data
def process_excel_data(df):
    df = df[:-1]
    df = df[df["Document Number"].str.startswith("JE-PRG")]

    dataku = df[["Document Number", "COA Description", "Amount (Debit)"]].sort_values(by="Amount (Debit)")
    data_fix = dataku[dataku["Amount (Debit)"] != 0].sort_index()

    dataz = pd.pivot_table(
        data_fix,
        index="Document Number",
        values="Amount (Debit)",
        columns="COA Description",
        aggfunc="sum"
    ).reset_index()

    required_cols = [
        "Cash Clearance Prigen", "A/R - Credit Card BCA", "A/R - Credit Card Mandiri",
        "A/R - Credit Card", "Mandiri by TF (temp)", "A/R - Website Online",
        "Tiket Clearance", "VOUCHER (temp)", "Charge To Room", "DP - Website On Line"
    ]
    for col in required_cols:
        if col not in dataz.columns:
            dataz[col] = 0

    dataz.iloc[:, 1:] = dataz.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').fillna(0)

    pajak_journals = df[df["COA Description"].str.contains("pajak", case=False, na=False)]["Document Number"].unique()
    dataz.loc[~dataz["Document Number"].isin(pajak_journals), "Tiket Clearance"] = 0

    key_df = df[["Document Number", "Memo (Main)"]].drop_duplicates()
    final_data = dataz.merge(key_df, on="Document Number", how="left")

    if "DP - Website On Line" in final_data.columns:
        final_data["A/R - Website Online"] += final_data["DP - Website On Line"]

    final_data = final_data[[
        "Memo (Main)", "Cash Clearance Prigen", "A/R - Credit Card BCA", "A/R - Credit Card Mandiri",
        "Mandiri by TF (temp)", "A/R - Credit Card", "A/R - Website Online",
        "Tiket Clearance", "VOUCHER (temp)", "Charge To Room"
    ]]

    final_data["Memo (Main)"] = final_data["Memo (Main)"].fillna("Biru")
    final_data["Total"] = final_data.sum(numeric_only=True, axis=1)
    final_data = final_data.groupby("Memo (Main)").sum().reset_index()
    final_data = final_data.sort_values(by="Total", ascending=False)
    final_data = final_data.replace(0, "")

    return final_data


# ====== STREAMLIT APP ======

st.title("📊 Revenue Processing App - TSI")

uploaded_file = st.file_uploader("Upload file CSV (delimiter koma `,`)", type=["csv"])

if uploaded_file is not None:
    try:
        # Baca file CSV
        df = pd.read_csv(uploaded_file)

        # Proses file
        result = process_excel_data(df)

        # Tampilkan hasil di Streamlit
        st.success("✅ Proses selesai! Berikut hasilnya:")
        st.dataframe(result)

        # Download sebagai CSV
        csv_data = result.to_csv(index=False, sep=",").encode("utf-8")
        st.download_button(
            label="📥 Download hasil sebagai CSV",
            data=csv_data,
            file_name="hasil_revenue_tsi.csv",
            mime="text/csv"
        )

        # Download sebagai Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            result.to_excel(writer, index=False, sheet_name='Hasil')
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Download hasil sebagai Excel (.xlsx)",
            data=excel_buffer,
            file_name="hasil_revenue_tsi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Gagal memproses file: {e}")
