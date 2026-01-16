#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TestConection.py - Diagnóstico de conectividad WinRM
=====================================================
Herramienta para diagnosticar problemas de conexión WinRM desde WSL.

Verifica:
1. Resolución DNS del hostname
2. Conectividad al puerto 5985 (WinRM HTTP)
3. Conectividad al puerto 5986 (WinRM HTTPS)
4. Gateway de WSL (tu máquina Windows host)
"""

import subprocess
import socket
import sys


def get_wsl_gateway():
    """Obtiene la IP del gateway de WSL (tu Windows host)."""
    try:
        result = subprocess.check_output(
            "ip route show | grep default | awk '{print $3}'",
            shell=True
        ).decode().strip()
        return result
    except Exception:
        return None


def resolve_hostname(hostname):
    """
    Intenta resolver el hostname a una IP.
    Retorna una tupla (ip, method) o (None, error).
    """
    # Primero intentar con getaddrinfo (respeta /etc/hosts y DNS)
    try:
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            ip = result[0][4][0]
            # Verificar que no sea localhost
            if ip.startswith("127.") or ip == "::1":
                return None, f"Resuelve a localhost ({ip}) - DNS mal configurado"
            return ip, "DNS"
    except socket.gaierror:
        pass
    
    # Intentar con getent hosts
    try:
        result = subprocess.check_output(
            f"getent hosts {hostname}",
            shell=True, stderr=subprocess.DEVNULL
        ).decode().strip()
        if result:
            ip = result.split()[0]
            if ip == "::1" or ip.startswith("127."):
                return None, f"getent resuelve a localhost ({ip})"
            return ip, "getent"
    except Exception:
        pass
    
    return None, "No se pudo resolver el hostname"


def test_port(host, port, timeout=3):
    """Prueba si un puerto está abierto."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False


def print_section(title):
    """Imprime un separador de sección."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_connection(hostname):
    """Ejecuta diagnóstico completo de conectividad."""
    print_section(f"DIAGNÓSTICO DE CONECTIVIDAD: {hostname}")
    
    results = {
        "dns_ok": False,
        "gateway_ok": False,
        "port_5985_ok": False,
        "resolved_ip": None
    }
    
    # 1. Gateway de WSL
    print_section("1. Gateway de WSL (Tu Windows Host)")
    gateway = get_wsl_gateway()
    if gateway:
        print(f"  ✅ Gateway detectado: {gateway}")
        results["gateway_ok"] = True
        
        # Probar puerto 5985 en gateway
        if test_port(gateway, 5985):
            print(f"  ✅ Puerto 5985 ABIERTO en gateway ({gateway})")
        else:
            print(f"  ❌ Puerto 5985 CERRADO en gateway ({gateway})")
    else:
        print("  ❌ No se pudo detectar el gateway")
    
    # 2. Resolución DNS
    print_section("2. Resolución DNS")
    resolved_ip, method = resolve_hostname(hostname)
    
    if resolved_ip:
        print(f"  ✅ {hostname} → {resolved_ip} (vía {method})")
        results["dns_ok"] = True
        results["resolved_ip"] = resolved_ip
    else:
        print(f"  ❌ {method}")
        print(f"  💡 Posible solución: Usar IP directamente en lugar de hostname")
    
    # 3. Test de puertos WinRM
    print_section("3. Test de Puertos WinRM")
    
    # Probar en IP resuelta si existe
    if resolved_ip:
        print(f"\n  Probando {resolved_ip}:")
        if test_port(resolved_ip, 5985):
            print(f"    ✅ Puerto 5985 (HTTP) ABIERTO")
            results["port_5985_ok"] = True
        else:
            print(f"    ❌ Puerto 5985 (HTTP) CERRADO")
        
        if test_port(resolved_ip, 5986):
            print(f"    ✅ Puerto 5986 (HTTPS) ABIERTO")
        else:
            print(f"    ⚠️  Puerto 5986 (HTTPS) CERRADO (normal si no usas HTTPS)")
    
    # Probar en gateway como fallback
    if gateway and gateway != resolved_ip:
        print(f"\n  Probando gateway ({gateway}) como fallback:")
        if test_port(gateway, 5985):
            print(f"    ✅ Puerto 5985 (HTTP) ABIERTO en gateway")
            if not results["port_5985_ok"]:
                print(f"    💡 TIP: Podrías usar {gateway} como tu target si el hostname falla")
        else:
            print(f"    ❌ Puerto 5985 (HTTP) CERRADO en gateway")
    
    # 4. Resumen y recomendaciones
    print_section("4. RESUMEN Y RECOMENDACIONES")
    
    all_ok = results["dns_ok"] and results["port_5985_ok"]
    
    if all_ok:
        print("  ✅ Todo parece correcto. WinRM debería funcionar.")
        print(f"\n  IP a usar: {resolved_ip}")
    else:
        print("  ❌ Se detectaron problemas:\n")
        
        if not results["dns_ok"]:
            print("  🔧 PROBLEMA DE DNS:")
            print(f"     El hostname '{hostname}' no resuelve correctamente.")
            print("     SOLUCIONES:")
            print(f"     1. Usar la IP directamente en lugar de '{hostname}'")
            print("     2. Agregar entrada en /etc/hosts de WSL:")
            print(f"        echo '<IP_DEL_EQUIPO> {hostname}' | sudo tee -a /etc/hosts")
            print("     3. Verificar configuración DNS corporativo")
            if gateway:
                print(f"\n     💡 Si el target es tu máquina Windows host, la IP es: {gateway}")
        
        if not results["port_5985_ok"] and results["dns_ok"]:
            print("\n  🔧 PROBLEMA DE FIREWALL/WINRM:")
            print(f"     El puerto 5985 no está accesible en {resolved_ip}")
            print("     EJECUTAR EN POWERSHELL (ADMIN) DEL EQUIPO REMOTO:")
            print("     1. Enable-PSRemoting -Force")
            print("     2. Set-NetConnectionProfile -NetworkCategory Private")
            print("     3. winrm quickconfig")
            print("     4. Set-Item WSMan:\\localhost\\Service\\AllowUnencrypted -Value $true")
    
    print("\n" + "="*60)
    return results


def main():
    """Punto de entrada principal."""
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
    else:
        hostname = input("Ingrese el hostname o IP para probar: ").strip()
    
    if not hostname:
        print("Error: Debe ingresar un hostname")
        sys.exit(1)
    
    results = test_connection(hostname)
    
    # Código de salida según resultado
    if results["dns_ok"] and results["port_5985_ok"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()