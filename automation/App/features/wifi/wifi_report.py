"""
Generador de reportes Wi-Fi
Procesa datos de análisis y genera reportes en diferentes formatos
"""
import json
import os
import csv
import sys
from datetime import datetime
from glob import glob

# Agregar directorio padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.common import clear_screen


def get_report_dir():
    """Obtiene el directorio de reportes (relativo al script)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "data", "reports")


def load_wifi_data(report_dir=None):
    """
    Carga todos los reportes de Wi-Fi disponibles
    
    Args:
        report_dir: Directorio donde están los reportes
    
    Returns:
        list: Lista de datos de Wi-Fi
    """
    if report_dir is None:
        report_dir = get_report_dir()
    
    wifi_files = glob(os.path.join(report_dir, "wifi_analysis_*.json"))
    all_data = []
    
    print(f"📂 Buscando reportes en: {report_dir}")
    print(f"   Archivos encontrados: {len(wifi_files)}")
    
    for filepath in wifi_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                filename = os.path.basename(filepath)
                
                if isinstance(data, dict):
                    # Si es un dict con múltiples hosts
                    for hostname, wifi_data in data.items():
                        if isinstance(wifi_data, dict):
                            # Agregar información del archivo fuente
                            wifi_data["_source_file"] = filename
                            wifi_data["hostname"] = hostname
                            all_data.append(wifi_data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item["_source_file"] = filename
                            all_data.append(item)
        except Exception as e:
            print(f"⚠ Error cargando {filepath}: {e}")
    
    return all_data


def generate_summary_report(wifi_data, output_file=None):
    """
    Genera un reporte resumen en CSV
    
    Args:
        wifi_data: Lista de datos de Wi-Fi
        output_file: Archivo de salida CSV
    """
    if output_file is None:
        output_file = os.path.join(get_report_dir(), "wifi_summary.csv")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Hostname", "SSID", "BSSID", "Señal (%)", "RSSI (dBm)", "Calidad",
            "Banda", "Canal", "Velocidad (Mbps)", "IP", "Gateway", "Estado", "Archivo Fuente"
        ])
        
        for data in wifi_data:
            connection = data.get("connection", {})
            signal = data.get("signal", {})
            network = data.get("network", {})
            
            if "error" in connection:
                writer.writerow([
                    data.get("hostname", "N/A"),
                    "ERROR", "N/A", "N/A", "N/A", "N/A",
                    "N/A", "N/A", "N/A", "N/A", "N/A", 
                    connection["error"],
                    data.get("_source_file", "N/A")
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
                    "OK",
                    data.get("_source_file", "N/A")
                ])
    
    print(f"✅ Reporte CSV generado: {output_file}")
    return output_file


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
        elif quality in ["débil", "debil"]:
            classified["debil"].append(data)
        elif quality in ["muy débil", "muy debil"]:
            classified["muy_debil"].append(data)
        else:
            # Si no tiene clasificación, intentar clasificar por porcentaje
            strength = signal.get("strength_percent", "")
            try:
                percent = int(str(strength).replace("%", ""))
                if percent >= 80:
                    classified["excelente"].append(data)
                elif percent >= 60:
                    classified["buena"].append(data)
                elif percent >= 40:
                    classified["aceptable"].append(data)
                elif percent >= 20:
                    classified["debil"].append(data)
                else:
                    classified["muy_debil"].append(data)
            except (ValueError, TypeError):
                classified["error"].append(data)
    
    return classified


def generate_classification_report(classified, output_file=None):
    """
    Genera reporte de clasificación
    
    Args:
        classified: Diccionario con dispositivos clasificados
        output_file: Archivo de salida
    """
    if output_file is None:
        output_file = os.path.join(get_report_dir(), "wifi_classification.json")
    
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
        "total": sum(len(v) for v in classified.values()),
        "devices": {
            k: [{"hostname": d.get("hostname", "N/A"), 
                 "ssid": d.get("connection", {}).get("ssid", "N/A"),
                 "signal": d.get("signal", {}).get("strength_percent", "N/A")} 
                for d in v]
            for k, v in classified.items()
        }
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Reporte de clasificación generado: {output_file}")
    print(f"\n📊 Resumen ({report['total']} dispositivos):")
    print(f"  🟢 Excelente: {report['summary']['excelente']}")
    print(f"  🟡 Buena: {report['summary']['buena']}")
    print(f"  🟠 Aceptable: {report['summary']['aceptable']}")
    print(f"  🔴 Débil: {report['summary']['debil']}")
    print(f"  ⚫ Muy débil: {report['summary']['muy_debil']}")
    print(f"  ❌ Error: {report['summary']['error']}")
    
    return output_file


def show_devices_table(wifi_data):
    """Muestra los dispositivos en formato tabla"""
    if not wifi_data:
        print("❌ No hay datos para mostrar")
        return
    
    print("\n📡 Dispositivos analizados:")
    print("=" * 100)
    print(f"{'Hostname':<15} {'SSID':<25} {'Señal':<10} {'Calidad':<12} {'Banda':<10} {'Estado':<15}")
    print("=" * 100)
    
    for data in wifi_data:
        hostname = data.get("hostname", "N/A")[:14]
        connection = data.get("connection", {})
        signal = data.get("signal", {})
        network = data.get("network", {})
        
        if "error" in connection:
            ssid = "ERROR"
            strength = "N/A"
            quality = "N/A"
            band = "N/A"
            estado = connection.get("error", "Error")[:14]
        else:
            ssid = connection.get("ssid", "N/A")[:24]
            strength = str(signal.get("strength_percent", "N/A"))
            if strength != "N/A" and not strength.endswith("%"):
                strength += "%"
            quality = signal.get("quality", "N/A")[:11]
            band = network.get("band", "N/A")[:9]
            estado = "OK"
        
        print(f"{hostname:<15} {ssid:<25} {strength:<10} {quality:<12} {band:<10} {estado:<15}")
    
    print("=" * 100)


def main():
    """Función principal"""
    clear_screen()
    print("=" * 60)
    print("📊 GENERADOR DE REPORTES WI-FI")
    print("=" * 60)
    
    # Cargar datos
    print("\n📂 Cargando datos de análisis...")
    wifi_data = load_wifi_data()
    
    if not wifi_data:
        print("\n❌ No se encontraron datos de análisis Wi-Fi")
        print("   Ejecutá primero wifi_analyzer.py")
        print(f"\n   Directorio de reportes: {get_report_dir()}")
        input("\nPresioná ENTER para salir...")
        return
    
    print(f"\n✅ {len(wifi_data)} dispositivos encontrados")
    
    # Mostrar tabla de dispositivos
    show_devices_table(wifi_data)
    
    # Menú de opciones
    print("\n📋 Opciones disponibles:")
    print("1. Generar reporte CSV resumen")
    print("2. Generar reporte de clasificación por calidad")
    print("3. Generar ambos reportes")
    print("4. Salir")
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == "1":
        print("\n📄 Generando reporte CSV...")
        generate_summary_report(wifi_data)
    elif opcion == "2":
        print("\n📊 Clasificando dispositivos...")
        classified = classify_devices(wifi_data)
        generate_classification_report(classified)
    elif opcion == "3":
        print("\n📄 Generando reporte CSV...")
        generate_summary_report(wifi_data)
        print("\n📊 Clasificando dispositivos...")
        classified = classify_devices(wifi_data)
        generate_classification_report(classified)
    elif opcion == "4":
        print("\n👋 ¡Hasta luego!")
        return
    else:
        print("❌ Opción inválida")
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()
