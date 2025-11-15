"""
Dashboard simple para visualizar resultados de automatización
Usa Streamlit para interfaz web
"""
import streamlit as st
import json
import os
import pandas as pd
from glob import glob
from datetime import datetime


def load_reports(report_type, report_dir="data/reports"):
    """
    Carga reportes de un tipo específico
    
    Args:
        report_type: Tipo de reporte (onedrive_fix, outlook_fix, etc.)
        report_dir: Directorio de reportes
    
    Returns:
        list: Lista de reportes cargados
    """
    pattern = os.path.join(report_dir, f"{report_type}_*.json")
    files = sorted(glob(pattern), reverse=True)[:10]  # Últimos 10 reportes
    
    reports = []
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Si tiene múltiples hosts, expandir
                    for hostname, report_data in data.items():
                        if isinstance(report_data, dict) and "hostname" in report_data:
                            reports.append(report_data)
                        else:
                            reports.append({"hostname": hostname, **report_data})
                else:
                    reports.append(data)
        except:
            continue
    
    return reports


def main():
    """Función principal del dashboard"""
    st.set_page_config(
        page_title="Automatización IT - Dashboard",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Dashboard de Automatización IT")
    st.markdown("---")
    
    # Sidebar para selección de tipo de reporte
    st.sidebar.title("📊 Navegación")
    report_type = st.sidebar.selectbox(
        "Tipo de Reporte",
        [
            "wifi_analysis",
            "onedrive_fix",
            "outlook_fix",
            "vpn_fix",
            "sccm_fix",
            "wifi_force_5ghz"
        ]
    )
    
    # Cargar reportes
    reports = load_reports(report_type)
    
    if not reports:
        st.warning(f"⚠️ No se encontraron reportes de tipo '{report_type}'")
        st.info("💡 Ejecutá los scripts de análisis/remediación para generar datos")
        return
    
    st.success(f"✅ {len(reports)} reportes encontrados")
    
    # Mostrar datos según el tipo
    if report_type == "wifi_analysis":
        show_wifi_dashboard(reports)
    elif report_type.endswith("_fix"):
        show_remediation_dashboard(reports, report_type)
    elif report_type == "wifi_force_5ghz":
        show_force_5ghz_dashboard(reports)


def show_wifi_dashboard(reports):
    """Muestra dashboard de análisis Wi-Fi"""
    st.header("📡 Análisis de Wi-Fi")
    
    # Crear DataFrame
    data = []
    for report in reports:
        connection = report.get("connection", {})
        signal = report.get("signal", {})
        network = report.get("network", {})
        
        data.append({
            "Hostname": report.get("hostname", "N/A"),
            "SSID": connection.get("ssid", "N/A"),
            "BSSID": connection.get("bssid", "N/A"),
            "Señal (%)": signal.get("strength_percent", "N/A"),
            "RSSI (dBm)": signal.get("rssi", "N/A"),
            "Calidad": signal.get("quality", "N/A"),
            "Banda": network.get("band", "N/A"),
            "Canal": network.get("channel", "N/A"),
            "Velocidad (Mbps)": network.get("speed_mbps", "N/A"),
            "IP": network.get("ip", "N/A"),
            "Gateway": network.get("gateway", "N/A")
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        if "Calidad" in df.columns:
            quality_counts = df["Calidad"].value_counts()
            st.bar_chart(quality_counts)
            st.caption("Distribución de Calidad de Señal")
    
    with col2:
        if "Banda" in df.columns:
            band_counts = df["Banda"].value_counts()
            st.bar_chart(band_counts)
            st.caption("Distribución por Banda")


def show_remediation_dashboard(reports, report_type):
    """Muestra dashboard de remediación"""
    fix_name = report_type.replace("_fix", "").replace("_", " ").title()
    st.header(f"🔧 Reparaciones: {fix_name}")
    
    # Resumen
    success_count = sum(1 for r in reports if r.get("success", False))
    total_count = len(reports)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", total_count)
    with col2:
        st.metric("Exitosas", success_count)
    with col3:
        st.metric("Tasa de Éxito", f"{success_rate:.1f}%")
    
    # Tabla detallada
    data = []
    for report in reports:
        steps = report.get("steps", {})
        success_steps = sum(1 for v in steps.values() if v == "OK")
        total_steps = len(steps)
        
        data.append({
            "Hostname": report.get("hostname", "N/A"),
            "Estado": "✅ Exitoso" if report.get("success", False) else "⚠️ Parcial",
            "Pasos OK": f"{success_steps}/{total_steps}",
            "Timestamp": report.get("timestamp", "N/A")[:19] if report.get("timestamp") else "N/A"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    # Detalles por hostname
    if st.checkbox("Mostrar detalles por hostname"):
        selected_host = st.selectbox("Seleccionar hostname", df["Hostname"].unique())
        selected_report = next((r for r in reports if r.get("hostname") == selected_host), None)
        
        if selected_report:
            st.json(selected_report.get("steps", {}))


def show_force_5ghz_dashboard(reports):
    """Muestra dashboard de forzado 5GHz"""
    st.header("📡 Forzado de Conexión 5GHz")
    
    # Resumen
    success_count = sum(1 for r in reports if r.get("success", False))
    total_count = len(reports)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total_count)
    with col2:
        st.metric("Exitosos", success_count)
    
    # Tabla
    data = []
    for report in reports:
        data.append({
            "Hostname/Device": report.get("hostname") or report.get("device_id", "N/A"),
            "Plataforma": report.get("platform", "N/A"),
            "Estado": "✅ 5GHz" if report.get("success", False) else "⚠️ No 5GHz",
            "Banda Actual": report.get("current_band", "N/A"),
            "SSID": report.get("current_ssid", "N/A"),
            "Timestamp": report.get("timestamp", "N/A")[:19] if report.get("timestamp") else "N/A"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()

