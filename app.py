import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import io

# ----------------- Sayfa Ayarı -----------------
st.set_page_config(page_title="FLO Stok Dashboard", layout="wide")

# ----------------- Stil -----------------
st.markdown("""
<style>
.metric-box {
    background-color: #2c3e50;
    color: white;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
}
.metric-label {
    font-size: 16px;
    color: white;
}
.metric-value {
    font-size: 22px;
    font-weight: bold;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 FLO Stok & Transfer Dashboard")

# ----------------- Mağaza Konumları -----------------
magaza_konum = {
    "İstanbul Merkez": {"lat": 41.015137, "lon": 28.979530},
    "Ankara Kızılay": {"lat": 39.92077, "lon": 32.85411},
    "İzmir Konak": {"lat": 38.4192, "lon": 27.1287},
    "Bursa FSM": {"lat": 40.1956, "lon": 29.0601},
    "Antalya Lara": {"lat": 36.8570, "lon": 30.9028}
}

urunler = ["Spor Ayakkabı", "Bot", "Sneaker", "Topuklu Ayakkabı", "Sandalet"]
kategoriler = ["Erkek", "Kadın", "Çocuk"]

# ----------------- Sahte Veri -----------------
data = []
for magaza in magaza_konum.keys():
    for urun in urunler:
        kategori = random.choice(kategoriler)
        stok = random.randint(0, 200)
        guvenli_stok = random.randint(50, 100)
        data.append([magaza, urun, kategori, stok, guvenli_stok])

df = pd.DataFrame(data, columns=["Mağaza", "Ürün", "Kategori", "Stok", "Güvenli Stok"])

# ----------------- Hesaplamalar -----------------
df["Durum"] = df.apply(lambda x: "Fazla Stok" if x["Stok"] > x["Güvenli Stok"] 
                       else ("Eksik Stok" if x["Stok"] < x["Güvenli Stok"] else "Tamam"), axis=1)
df["Fazla Miktar"] = df.apply(lambda x: max(0, x["Stok"] - x["Güvenli Stok"]), axis=1)
df["Eksik Miktar"] = df.apply(lambda x: max(0, x["Güvenli Stok"] - x["Stok"]), axis=1)

# ----------------- Sidebar Filtreler -----------------
st.sidebar.header("Filtreler")
selected_magaza = st.sidebar.multiselect("Mağaza", options=magaza_konum.keys(), default=list(magaza_konum.keys()))
selected_urun = st.sidebar.multiselect("Ürün", options=urunler, default=urunler)
selected_kategori = st.sidebar.multiselect("Kategori", options=kategoriler, default=kategoriler)
selected_durum = st.sidebar.multiselect("Stok Durumu", options=["Fazla Stok","Eksik Stok","Tamam"], default=["Fazla Stok","Eksik Stok","Tamam"])

# Filtrelenmiş DataFrame
df_filtered = df[(df["Mağaza"].isin(selected_magaza)) & 
                 (df["Ürün"].isin(selected_urun)) & 
                 (df["Kategori"].isin(selected_kategori)) &
                 (df["Durum"].isin(selected_durum))]

# ----------------- Transfer Hesaplama -----------------
fazla_df = df_filtered[df_filtered["Fazla Miktar"]>0]
eksik_df = df_filtered[df_filtered["Eksik Miktar"]>0]

transfer_listesi = []
for _, f_row in fazla_df.iterrows():
    for _, e_row in eksik_df.iterrows():
        if f_row["Ürün"] == e_row["Ürün"]:
            transfer_miktar = min(f_row["Fazla Miktar"], e_row["Eksik Miktar"])
            if transfer_miktar>0:
                transfer_listesi.append([f_row["Mağaza"], e_row["Mağaza"], f_row["Ürün"], transfer_miktar])

transfer_df = pd.DataFrame(transfer_listesi, columns=["Gönderen Mağaza","Alan Mağaza","Ürün","Miktar"])

# ----------------- Özet Kartlar -----------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class='metric-box'><div class='metric-label'>🏬 Toplam Mağaza</div><div class='metric-value'>{df_filtered['Mağaza'].nunique()}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class='metric-box'><div class='metric-label'>📦 Toplam Stok</div><div class='metric-value'>{int(df_filtered['Stok'].sum())}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class='metric-box'><div class='metric-label'>✅ Fazla Stok</div><div class='metric-value'>{int(df_filtered['Fazla Miktar'].sum())}</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class='metric-box'><div class='metric-label'>❌ Eksik Stok</div><div class='metric-value'>{int(df_filtered['Eksik Miktar'].sum())}</div></div>""", unsafe_allow_html=True)

# ----------------- Stok Grafiği -----------------
st.subheader("📊 Stok Durumu Grafiği")
fig = px.bar(df_filtered, x="Ürün", y="Stok", color="Durum", barmode="group", facet_col="Mağaza", color_discrete_map={"Fazla Stok":"green","Eksik Stok":"red","Tamam":"gray"})
st.plotly_chart(fig, use_container_width=True)

# ----------------- Transfer Tablosu -----------------
st.subheader("🚚 Transfer Önerileri")
st.dataframe(transfer_df, use_container_width=True)

# ----------------- Harita -----------------
st.subheader("🗺 Transfer Haritası")
map_fig = go.Figure()

# Mağaza noktaları
for magaza, coords in magaza_konum.items():
    map_fig.add_trace(go.Scattermapbox(lat=[coords['lat']], lon=[coords['lon']], mode='markers+text',
                                       marker=dict(size=12,color='blue'), text=[magaza], textposition='top right'))

# Transfer çizgileri + ok başı
for _, row in transfer_df.iterrows():
    start = magaza_konum[row['Gönderen Mağaza']]
    end = magaza_konum[row['Alan Mağaza']]
    dx = end['lon'] - start['lon']
    dy = end['lat'] - start['lat']
    arrow_lon = end['lon'] - dx*0.1
    arrow_lat = end['lat'] - dy*0.1

    # Ana çizgi
    map_fig.add_trace(go.Scattermapbox(lat=[start['lat'], end['lat']], lon=[start['lon'], end['lon']], mode='lines', line=dict(width=2,color='orange'), name=f"{row['Ürün']} - {row['Miktar']} adet"))
    # Ok başı
    map_fig.add_trace(go.Scattermapbox(lat=[arrow_lat,end['lat']], lon=[arrow_lon,end['lon']], mode='lines', line=dict(width=4,color='orange'), showlegend=False))

map_fig.update_layout(mapbox=dict(style='open-street-map', center=dict(lat=39.5, lon=35.0), zoom=5), margin=dict(r=0,t=0,l=0,b=0))
st.plotly_chart(map_fig, use_container_width=True)

# ----------------- Detaylı Tablo -----------------
with st.expander("📋 Detaylı Stok Listesi"):
    st.dataframe(df_filtered, use_container_width=True)

# ----------------- Rapor İndirme -----------------
st.subheader("💾 Rapor İndir")

# Excel indirme
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_filtered.to_excel(writer, index=False, sheet_name='Stok')
processed_data = output.getvalue()

st.download_button(
    label="Excel Olarak İndir",
    data=processed_data,
    file_name='stok_raporu.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# CSV indirme
csv_file = df_filtered.to_csv(index=False)
st.download_button(
    label="CSV Olarak İndir",
    data=csv_file,
    file_name='stok_raporu.csv',
    mime='text/csv'
)
