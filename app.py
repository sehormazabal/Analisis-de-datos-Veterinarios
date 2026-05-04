import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Dashboard Veterinario", layout="wide", page_icon="🐾")

st.title("🐾 Dashboard Veterinario - Análisis de Desempeño")
st.markdown("Análisis comparativo del impacto de la expansión del equipo veterinario (Noviembre 2025).")

# Paths
path_solicitudes = r"g:\Mi unidad\09.Proyectos_Data\01.AnalisisdatosVet\00. SOLICITUD Y DENUNCIA 2026.csv"
path_atenciones = r"g:\Mi unidad\09.Proyectos_Data\01.AnalisisdatosVet\ATENCIONESREALIZADAS.csv"
path_lista_espera = r"g:\Mi unidad\09.Proyectos_Data\01.AnalisisdatosVet\LISTADEESPERA.csv"
path_operativos = r"g:\Mi unidad\09.Proyectos_Data\01.AnalisisdatosVet\OPERATIVOS vet móvil.csv"

@st.cache_data
def load_data():
    df_solicitudes = pd.read_csv(path_solicitudes, sep=';', encoding='latin1', on_bad_lines='skip')
    df_atenciones = pd.read_csv(path_atenciones, sep=';', encoding='latin1', on_bad_lines='skip')
    df_lista_espera = pd.read_csv(path_lista_espera, sep=';', encoding='latin1', on_bad_lines='skip')
    df_operativos = pd.read_csv(path_operativos, sep=';', encoding='latin1', on_bad_lines='skip')
    
    for df in [df_solicitudes, df_atenciones, df_lista_espera, df_operativos]:
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
    return df_solicitudes, df_atenciones, df_lista_espera, df_operativos

df_solicitudes, df_atenciones, df_lista_espera, df_operativos = load_data()

def parse_dates(df, col_name_hint):
    col = next((c for c in df.columns if col_name_hint in c), None)
    if col:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        return col
    return None

col_fecha_sol = parse_dates(df_solicitudes, 'FECHA')
col_fecha_ate = parse_dates(df_atenciones, 'FECHA')
col_fecha_esp = parse_dates(df_lista_espera, 'INSCRIP')
col_fecha_ope = parse_dates(df_operativos, 'REALIZA')

col_total_ope = next((c for c in df_operativos.columns if 'TOTAL' in c), None)
if col_total_ope:
    df_operativos[col_total_ope] = pd.to_numeric(df_operativos[col_total_ope], errors='coerce').fillna(0)
col_estado_sol = next((c for c in df_solicitudes.columns if 'ESTADO' in c), None)

def get_period_mask(df, date_col):
    if not date_col or date_col not in df.columns:
        return [pd.Series(False, index=df.index)] * 4
    dates = df[date_col]
    p1_mask = (dates >= '2025-01-01') & (dates <= '2025-12-31') # Año 2025 Completo
    p2_mask = (dates >= '2026-01-01') & (dates <= '2026-12-31') # Año 2026 (a la fecha)
    c25_mask = (dates >= '2025-02-01') & (dates <= '2025-03-31') # Feb - Mar 2025
    c26_mask = (dates >= '2026-02-01') & (dates <= '2026-03-31') # Feb - Mar 2026
    return p1_mask, p2_mask, c25_mask, c26_mask

def contar_listos(mask):
    if col_estado_sol:
        estados = df_solicitudes.loc[mask, col_estado_sol].astype(str).str.strip().str.upper()
        return (estados == 'LISTO').sum()
    return 0

df_resumen = pd.DataFrame({
    'Periodo': ['Año 2025 Completo', 'Año 2026 (a la fecha)', 'Feb-Mar 2025', 'Feb-Mar 2026'],
    'Atenciones Box': [get_period_mask(df_atenciones, col_fecha_ate)[i].sum() for i in range(4)],
    'Mascotas Móvil': [df_operativos.loc[get_period_mask(df_operativos, col_fecha_ope)[i], col_total_ope].sum() if col_total_ope else 0 for i in range(4)],
    'Denuncias/Sol. Ingresadas': [len(df_solicitudes[get_period_mask(df_solicitudes, col_fecha_sol)[i]]) for i in range(4)],
    'Denuncias/Sol. LISTO': [contar_listos(get_period_mask(df_solicitudes, col_fecha_sol)[i]) for i in range(4)]
})
df_resumen['Total Atenciones (Box + Móvil)'] = df_resumen['Atenciones Box'] + df_resumen['Mascotas Móvil']

# Quarterly Comparison
def get_trimestre_mask(df, date_col):
    if not date_col or date_col not in df.columns:
        return pd.Series(False, index=df.index), pd.Series(False, index=df.index)
    dates = df[date_col]
    m_q1_25 = (dates >= '2025-01-01') & (dates <= '2025-03-31')
    m_q1_26 = (dates >= '2026-01-01') & (dates <= '2026-03-31') 
    return m_q1_25, m_q1_26

m_sol_q1_25, m_sol_q1_26 = get_trimestre_mask(df_solicitudes, col_fecha_sol)
m_ate_q1_25, m_ate_q1_26 = get_trimestre_mask(df_atenciones, col_fecha_ate)
m_ope_q1_25, m_ope_q1_26 = get_trimestre_mask(df_operativos, col_fecha_ope)

box_q1_25 = m_ate_q1_25.sum()
box_q1_26 = m_ate_q1_26.sum()
movil_q1_25 = df_operativos.loc[m_ope_q1_25, col_total_ope].sum() if col_total_ope else 0
movil_q1_26 = df_operativos.loc[m_ope_q1_26, col_total_ope].sum() if col_total_ope else 0

df_q1 = pd.DataFrame({
    'Periodo': ['Ene-Mar 2025 (1er Trim)', 'Ene-Mar 2026 (1er Trim)'],
    'Atenciones Box': [box_q1_25, box_q1_26],
    'Mascotas Móvil': [movil_q1_25, movil_q1_26],
    'Total Atenciones (Box + Móvil)': [box_q1_25 + movil_q1_25, box_q1_26 + movil_q1_26],
    'Denuncias/Sol. Ingresadas': [len(df_solicitudes[m_sol_q1_25]), len(df_solicitudes[m_sol_q1_26])],
    'Denuncias/Sol. LISTO': [contar_listos(m_sol_q1_25), contar_listos(m_sol_q1_26)]
})

# Time Series Data
if col_fecha_ate and col_fecha_ope:
    df_atenciones['MesAño'] = df_atenciones[col_fecha_ate].dt.to_period('M')
    df_operativos['MesAño'] = df_operativos[col_fecha_ope].dt.to_period('M')
    
    ts_box = df_atenciones.groupby('MesAño').size().reset_index(name='Atenciones Box')
    ts_movil = df_operativos.groupby('MesAño')[col_total_ope].sum().reset_index(name='Mascotas Móvil')
    
    ts_total = pd.merge(ts_box, ts_movil, on='MesAño', how='outer').fillna(0)
    ts_total['Total Atenciones'] = ts_total['Atenciones Box'] + ts_total['Mascotas Móvil']
    ts_total['MesAño'] = ts_total['MesAño'].dt.to_timestamp()
    ts_total = ts_total.sort_values('MesAño')
    ts_total = ts_total[ts_total['MesAño'] >= '2025-01-01']
else:
    ts_total = pd.DataFrame()

# TABS
tab1, tab2, tab3 = st.tabs(["📊 Resumen Global", "📅 Análisis Trimestral / Semestral", "📈 Evolución Mensual"])

with tab1:
    st.subheader("Comparativa Rendimiento: Equipos")
    
    # KPIs General
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    at_tot_pre = df_resumen.iloc[0]['Total Atenciones (Box + Móvil)']
    at_tot_post = df_resumen.iloc[1]['Total Atenciones (Box + Móvil)']
    
    col_kpi1.metric("Atenciones Totales (2026)", f"{at_tot_post:,.0f}")
    col_kpi2.metric("Atenciones Box (2026)", f"{df_resumen.iloc[1]['Atenciones Box']:,.0f}")
    col_kpi3.metric("Sol. Ingresadas (2026)", f"{df_resumen.iloc[1]['Denuncias/Sol. Ingresadas']:,.0f}")
    col_kpi4.metric("Sol. Resueltas (2026)", f"{df_resumen.iloc[1]['Denuncias/Sol. LISTO']:,.0f}")

    df_melt = df_resumen.iloc[0:2].melt(id_vars='Periodo', value_vars=['Atenciones Box', 'Mascotas Móvil', 'Total Atenciones (Box + Móvil)', 'Denuncias/Sol. LISTO'], var_name='Métrica', value_name='Cantidad')
    fig = px.bar(df_melt, x='Métrica', y='Cantidad', color='Periodo', barmode='group', text_auto=True, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(title_text='Comparativa Anual: 2025 Completo vs 2026 a la fecha', hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Comparativa Trimestral (Ene-Mar 2025 vs Ene-Mar 2026)")
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        st.dataframe(df_q1.style.format(precision=0), use_container_width=True)
    with col_t2:
        df_q1_melt = df_q1.melt(id_vars='Periodo', value_vars=['Atenciones Box', 'Mascotas Móvil', 'Total Atenciones (Box + Móvil)', 'Denuncias/Sol. LISTO'], var_name='Métrica', value_name='Cantidad')
        fig_q1 = px.bar(df_q1_melt, x='Métrica', y='Cantidad', color='Periodo', barmode='group', text_auto=True, color_discrete_sequence=px.colors.qualitative.Set2)
        fig_q1.update_layout(title_text='Primer Trimestre: LÍNEA BASE vs IMPACTO NUEVO EQUIPO', hovermode="x unified")
        st.plotly_chart(fig_q1, use_container_width=True)

with tab3:
    st.subheader("Evolución Mensual de Atenciones Totales")
    if not ts_total.empty:
        fig_ts = px.line(ts_total, x='MesAño', y='Total Atenciones', markers=True, title="Atenciones Totales por Mes")
        
        # Línea vertical para el hito (Noviembre 2025)
        fig_ts.add_vline(x="2025-11-01", line_width=3, line_dash="dash", line_color="red")
        fig_ts.add_annotation(x="2025-11-01", y=ts_total['Total Atenciones'].max() * 0.9, 
                              text="Ingreso 2do Veterinario (Nov 25)", showarrow=True, arrowhead=1, ax=-50, ay=0)
        
        fig_ts.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Atenciones", hovermode="x unified")
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.warning("No se pudieron cargar los datos de evolución temporal.")
