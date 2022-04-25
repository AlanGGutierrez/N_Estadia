import base64
import os
import os.path
import platform
from datetime import datetime
import hydralit_components as hc
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from PIL import Image
from st_aggrid import AgGrid
from streamlit_lottie import st_lottie

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Estadia Dashboard", page_icon=":bar_chart:", layout="wide")

def create_onedrive_directdownload (onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    return resultUrl


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def listToString(s):
    # initialize an empty string
    str1 = ""

    # traverse in the string
    for ele in s:
        str1 += ele

        # return string
    return str1

def ceil_date(date, **kwargs):
    secs = pd.Timedelta(**kwargs).total_seconds()
    return datetime.fromtimestamp(date.timestamp() + secs - date.timestamp() % secs)

def floor_date(date, **kwargs):
    secs = pd.Timedelta(**kwargs).total_seconds()
    return datetime.fromtimestamp(date.timestamp() - date.timestamp() % secs)




# -------------------------Hidralit theme-------------------------

# can apply customisation to almost all the properties of the card, including the progress bar
theme_bad = {'bgcolor': '#B22222', 'title_color': 'white', 'content_color': 'whithe', 'icon_color': 'white',
             'progress_color': 'red'}

# -------------------------- LOAD ASSETS ---------------------------
lottie_car = load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_v92o72md.json")
lottie_chart = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_S2eIOQ.json")
lottie_tower = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_jznvojh3.json")
lottie_time = load_lottieurl("https://assets1.lottiefiles.com/private_files/lf30_a3g6x26d.json")
lottie_truck = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_hutlkiuf.json")
lottie_list = load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_emujvwjt.json")
img_control_Tower = Image.open("images/ControlTowerwhite.png")


#-----Read onedrive Excel-------------
onedrive_link = "https://1drv.ms/x/s!AsyQPQRa2P2OjH24em4_r9PBRIKx?e=fZyqf9"
onedrive_directlink = create_onedrive_directdownload(onedrive_link)

#--------------------------------DF--------------------------
df = pd.read_excel(onedrive_directlink)
# Dataframe General
df = df.drop(df[df['A'] == 0].index)
today = datetime.now()
df["fecha_actual"] = today
df["total_Permamencia_Lugar"] = np.where(df["Salida"].isnull(), round((df["fecha_actual"]-df["Llegada"])/ pd.Timedelta(hours=1)), round((df["Salida"]-df["Llegada"])/ pd.Timedelta(hours=1))).astype("float")
#df["Salida"].fillna(df["fecha_actual"], inplace=True)

#----------------------------Calculo Zona de Espera----------------
df['zona_Espera'] = np.where((df['GeoCerca'].str.contains('- ZONA DE ESPERA')) & (df["Salida"].isnull()),1,0 )
total_Unidades_Zona_Espera = df['zona_Espera'].sum().astype("float")
df["horas_Zona_Espera"] = np.where(df['zona_Espera'] == 1,df["total_Permamencia_Lugar"], 0 )
total_horas_Zona_Espera = df['horas_Zona_Espera'].sum().astype("float")
if total_Unidades_Zona_Espera == 0:
    promedio_Zona_Espera = 0
else:
    promedio_Zona_Espera = round(total_horas_Zona_Espera / total_Unidades_Zona_Espera,1)
#--------------------------Calculo  en Planta ---------------------------------------
df['zona_EnPlanta'] = np.where((~df['GeoCerca'].str.contains('- ZONA DE ESPERA',na=False)) & (df["Salida"].isnull()),1,0 )
total_Unidades_En_Planta = df['zona_EnPlanta'].sum().astype("float")
df["horas_Zona_EnPlanta"] = np.where(df['zona_EnPlanta'] == 1,df["total_Permamencia_Lugar"], 0 )
total_horas_Zona_EnPlanta = df['horas_Zona_EnPlanta'].sum().astype("float")
if total_Unidades_En_Planta == 0:
    promedio_Zona_EnPlanta = 0
else:
    promedio_Zona_EnPlanta = round(total_horas_Zona_EnPlanta / total_Unidades_En_Planta,1)

AgGrid(df)

#-------------------------------Top 5----------------------
df_Top_General = df.loc[df['zona_Espera'] > 0]
df_Top = df_Top_General.groupby('GeoCerca')['horas_Zona_Espera'].agg(['sum', "mean", "count"]).round(2)
df_Top = df_Top.sort_values('mean', ascending=False)
df_Top = df_Top.reset_index()
tam_df = (len(df_Top))
conti = 0
for i in range(5):
    if tam_df < 5:
        conti = conti + 1
        df_Top.loc[tam_df] = [f'Sin datos{conti}', 0, 0]
        tamdf = tamdf + 1
st.dataframe(df_Top)

#-----------------Placas Top 5-------------
placasT1 = df_Top_General.loc[df_Top_General["GeoCerca"] == df_Top['GeoCerca'][0], ["Matricula1"]]
placasT2 = df_Top_General.loc[df_Top_General["GeoCerca"] == df_Top['GeoCerca'][1], ["Matricula1"]]
placasT3 = df_Top_General.loc[df_Top_General["GeoCerca"] == df_Top['GeoCerca'][2], ["Matricula1"]]
placasT4 = df_Top_General.loc[df_Top_General["GeoCerca"] == df_Top['GeoCerca'][3], ["Matricula1"]]
placasT5 = df_Top_General.loc[df_Top_General["GeoCerca"] == df_Top['GeoCerca'][4], ["Matricula1"]]

# ---- -----------------------------SIDEBAR ---------------------------------
st.sidebar.header("Filtra aquí:")

geocerca = st.sidebar.multiselect(
    "Selecciona el destino:",
    options=df_Top_General["GeoCerca"].unique(),
    default=df_Top_General["GeoCerca"].unique()
)

# zona = st.sidebar.multiselect(
#     "Selecciona la zona:",
#     options=df["ZONA_VENTA"].unique(),
#     default=df["ZONA_VENTA"].unique()
# )

# fi = st.sidebar.date_input('Fecha Inicial:', key="fecha_inicial")
# ff = st.sidebar.date_input('Fecha Final:', key="fecha_final")

df_selection = df_Top_General.query(
    # "ESTATUS MONITOREO == @estatus & Cerveceria == @cerveceria & Transportista == @transportista & Destino ==
    # @destino & ZONA_VENTA == @zona"
    "GeoCerca == @geocerca "
)


# -------------------------- MAINPAGE --------------

left_column, mid_column, right_column = st.columns(3)
with left_column:
    st_lottie(lottie_car, height=300, key="car")
with mid_column:
    st.markdown("<h1 style='text-align: center; color: white;'>Estadias Dashboard</h1>", unsafe_allow_html=True)
    st.image(img_control_Tower)

with right_column:
    st_lottie(lottie_chart, height=300, key="chart")

st.markdown("""---""")

#-------------------------KPI------------------------
left_column1, left_column2, right_column1, right_column2 = st.columns([1, 2, 1, 2])
with left_column1:
    st_lottie(lottie_truck, height=200, key="time")
with left_column2:
    st.subheader("Unidades en Espera")
    st.subheader(f" {promedio_Zona_Espera}  hrs.")
    st.subheader(f" Placas: {total_Unidades_Zona_Espera}")
with right_column1:
    st_lottie(lottie_list, height=200, key="list")
with right_column2:
    st.subheader("Unidades en Planta")
    st.subheader(f"{promedio_Zona_EnPlanta} hrs.")
    st.subheader(f" Placas: {total_Unidades_En_Planta}")

st.markdown("""---""")


# ------------------------------Indicadores Top 5----------------------

left_column, mid_column, right_column = st.columns(3)
with left_column:
    st.write(" ")
with mid_column:
    st.markdown("<h1 style='text-align: center; color: white;'>Top 5 General</h1>", unsafe_allow_html=True)
with right_column:
    st.write(" ")

with st.container():
    left_column, mid_column1, mid_column2, mid_column3, right_column = st.columns(5)
    with left_column:
        hc.info_card(title=df_Top['GeoCerca'][0], content=f"{df_Top['mean'][0]} hrs.",
                     theme_override=theme_bad, bar_value=100, key="top1")
        unsafe_allow_html = True
    with mid_column1:
        hc.info_card(title=df_Top['GeoCerca'][1], content=f"{df_Top['mean'][1]} hrs.",
                     theme_override=theme_bad, bar_value=95, key="top2")
    with mid_column2:
        hc.info_card(title=df_Top['GeoCerca'][2], content=f"{df_Top['mean'][2]} hrs.",
                     theme_override=theme_bad, bar_value=90, key="top3")
    with mid_column3:
        hc.info_card(title=df_Top['GeoCerca'][3], content=f"{df_Top['mean'][3]} hrs.",
                     theme_override=theme_bad, bar_value=85, key="top4")
    with right_column:
        hc.info_card(title=df_Top['GeoCerca'][4], content=f"{df_Top['mean'][4]} hrs.",
                     theme_override=theme_bad, bar_value=80, key="top5")

with st.container():
    left_column, mid_column1, mid_column2, mid_column3, right_column = st.columns(5)
    with left_column:
        st.write(f"Unidades en Espera: {df_Top['count'][0]}")
        with st.expander("Placas"):
            st.dataframe(placasT1)
    with mid_column1:
        st.write(f"Unidades en Espera: {df_Top['count'][1]}")
        with st.expander("Placas"):
            st.dataframe(placasT2)
    with mid_column2:
        st.write(f"Unidades en Espera: {df_Top['count'][2]}")
        with st.expander("Placas"):
            st.dataframe(placasT3)
    with mid_column3:
        st.write(f"Unidades en Espera: {df_Top['count'][3]}")
        with st.expander("Placas"):
            st.dataframe(placasT4)
    with right_column:
        st.write(f"Unidades en Espera: {df_Top['count'][4]}")
        with st.expander("Placas"):
            st.dataframe(placasT5)

st.markdown("""---""")

# --------------------------Estadia Arribo[BAR CHART]-------------------
estadia_zonaEspera = df_selection.groupby(by=["GeoCerca"]).mean()[["horas_Zona_Espera"]].round(2)
# filtro = estadia_arribo['estadia_vs_arribo_sum'] > 0
# estadia_arribo = estadia_arribo[filtro]
estadia_zonaEspera = estadia_zonaEspera.sort_values('horas_Zona_Espera', ascending=False)
grafico_estadia_ZonaEspera = px.bar(
    estadia_zonaEspera,
    x=estadia_zonaEspera.index,
    y="horas_Zona_Espera",
    title="<b>Estadia zona de Espera</b>",
    color_discrete_sequence=["#1E90FF"] * len(estadia_zonaEspera),
    template="plotly_white", text_auto=True, labels={'horas_Zona_Espera': 'Horas Promedio Espera'}, height=600
)
grafico_estadia_ZonaEspera.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False)),
)



left_column, mid_column, right_column = st.columns(3)
left_column.plotly_chart(grafico_estadia_ZonaEspera, use_container_width=True)
#mid_column.plotly_chart(grafico_estadia_cita, use_container_width=True)
#right_column.plotly_chart(grafico_zona, use_container_width=True)
st.markdown("""---""")

# ------------------------- HIDE STREAMLIT STYLE ------------------------
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
