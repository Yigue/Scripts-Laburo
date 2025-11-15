"""
Generador de reportes Wi-Fi
Procesa datos de análisis y genera reportes en diferentes formatos
"""
import json
import os
import csv
from datetime import datetime
from glob import glob


def load_wifi_data(report_dir="data/reports"):
    """
    Carga todos los reportes de Wi-Fi disponibles
    
    Args:
        report_dir: Directorio donde están los reportes
    
    Returns:
        list: Lista de datos de Wi-Fi
    """
    wifi_files = glob(os.path.join(report_dir, "wifi_analysis_*.json"))
    all_data = []
    
    for filepath in wifi_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Si es un dict con múltiples hosts
                    for hostname, wifi_data in data.items():
                        all_data.append(wifi_data)
                elif isinstance(data, list):
                    all_data.extend(data)
        except Exception as e:
            print(f"⚠ Error cargando {filepath}: {e}")
    
    return all_data


def generate_summary_report(wifi_data, output_file="data/reports/wifi_summary.csv"):
    """
    Genera un reporte resumen en CSV
    
    Args:
        wifi_data: Lista de datos de Wi-Fi
        output_file: Archivo de salida CSV
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Hostname", "SSID", "BSSID", "Señal (%)", "RSSI (dBm)", "Calidad",
            "Banda", "Canal", "Velocidad (Mbps)", "IP", "Gateway", "Estado"
        ])
        
        for data in wifi_data:
            connection = data.get("connection", {})
            signal = data.get("signal", {})
            network = data.get("network", {})
            
            if "error" in connection:
                writer.writerow([
                    data.get("hostname", "N/A"),
                    "ERROR", "N/A", "N/A", "N/A", "N/A",
                    "N/A", "N/A", "N/A", "N/A", "N/A", connection["error"]
                ])
            else:
                writer.writerow([
                    data.get("hostname", "N/A"),
                    connection.get("ssid", "N/A"),
                    connection.get("bssid", "N/A"),
                    signal.get("strength_percent", "N/A"),
                    signal.get("rssi", "N/A"),
                    signal.get("quality", "N/A"),
                    network.get("band", "N/A"),
                    network.get("channel", "N/A"),
                    network.get("speed_mbps", "N/A"),
                    network.get("ip", "N/A"),
                    network.get("gateway", "N/A"),
                    "OK"
                ])
    
    print(f"✅ Reporte CSV generado: {output_file}")


def classify_devices(wifi_data):
    """
    Clasifica dispositivos por calidad de conexión
    
    Returns:
        dict: Dispositivos clasificados por categoría
    """
    classified = {
        "excelente": [],
        "buena": [],
        "aceptable": [],
        "debil": [],
        "muy_debil": [],
        "error": []
    }
    
    for data in wifi_data:
        signal = data.get("signal", {})
        quality = signal.get("quality", "").lower()
        connection = data.get("connection", {})
        
        if "error" in connection:
            classified["error"].append(data)
        elif quality == "excelente":
            classified["excelente"].append(data)
        elif quality == "buena":
            classified["buena"].append(data)
        elif quality == "aceptable":
            classified["aceptable"].append(data)
        elif quality == "débil":
            classified["debil"].append(data)
        elif quality == "muy débil":
            classified["muy_debil"].append(data)
        else:
            classified["error"].append(data)
    
    return classified


def generate_classification_report(classified, output_file="data/reports/wifi_classification.json"):
    """
    Genera reporte de clasificación
    
    Args:
        classified: Diccionario con dispositivos clasificados
        output_file: Archivo de salida
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "excelente": len(classified["excelente"]),
            "buena": len(classified["buena"]),
            "aceptable": len(classified["aceptable"]),
            "debil": len(classified["debil"]),
            "muy_debil": len(classified["muy_debil"]),
            "error": len(classified["error"])
        },
        "devices": classified
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Reporte de clasificación generado: {output_file}")
    print(f"\n📊 Resumen:")
    print(f"  🟢 Excelente: {report['summary']['excelente']}")
    print(f"  🟡 Buena: {report['summary']['buena']}")
    print(f"  🟠 Aceptable: {report['summary']['aceptable']}")
    print(f"  🔴 Débil: {report['summary']['debil']}")
    print(f"  ⚫ Muy débil: {report['summary']['muy_debil']}")
    print(f"  ❌ Error: {report['summary']['error']}")


def main():
    """Función principal"""
    print("=" * 60)
    print("📊 GENERADOR DE REPORTES WI-FI")
    print("=" * 60)
    
    # Cargar datos
    print("\n📂 Cargando datos de análisis...")
    wifi_data = load_wifi_data()
    
    if not wifi_data:
        print("❌ No se encontraron datos de análisis Wi-Fi")
        print("   Ejecutá primero wifi_analyzer.py")
        input("\nPresioná ENTER para salir...")
        return
    
    print(f"✅ {len(wifi_data)} dispositivos encontrados")
    
    # Generar reporte CSV
    print("\n📄 Generando reporte CSV...")
    generate_summary_report(wifi_data)
    
    # Clasificar y generar reporte
    print("\n📊 Clasificando dispositivos...")
    classified = classify_devices(wifi_data)
    generate_classification_report(classified)
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

