"""
Utilidades de red para diagnóstico y conectividad
"""
import subprocess
import socket


def ping(hostname, count=2, timeout=3):
    """
    Realiza ping a un host
    
    Args:
        hostname: Nombre o IP del host
        count: Número de pings
        timeout: Timeout en segundos
    
    Returns:
        dict: Resultado con success, latency, packets_lost
    """
    result = {
        "hostname": hostname,
        "success": False,
        "latency_ms": None,
        "packets_sent": count,
        "packets_received": 0,
        "packets_lost": count
    }
    
    try:
        proc = subprocess.run(
            ["ping", "-n", str(count), "-w", str(timeout * 1000), hostname],
            capture_output=True,
            text=True,
            timeout=timeout * count + 5
        )
        
        output = proc.stdout
        
        # Parsear resultado
        if proc.returncode == 0:
            result["success"] = True
            
            # Buscar estadísticas
            for line in output.split('\n'):
                line = line.strip()
                
                # Paquetes: Enviados = 2, Recibidos = 2, Perdidos = 0
                if "Recibidos" in line or "Received" in line:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if len(numbers) >= 3:
                        result["packets_sent"] = int(numbers[0])
                        result["packets_received"] = int(numbers[1])
                        result["packets_lost"] = int(numbers[2])
                
                # Media = 5ms
                if "Media" in line or "Average" in line:
                    import re
                    ms = re.search(r'(\d+)\s*ms', line)
                    if ms:
                        result["latency_ms"] = int(ms.group(1))
        
        return result
        
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def resolve_hostname(hostname):
    """
    Resuelve un hostname a IP
    
    Args:
        hostname: Nombre del host
    
    Returns:
        str: IP o None si no se puede resolver
    """
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.gaierror:
        return None


def test_port(hostname, port, timeout=3):
    """
    Prueba si un puerto está abierto
    
    Args:
        hostname: Nombre o IP del host
        port: Número de puerto
        timeout: Timeout en segundos
    
    Returns:
        bool: True si el puerto está abierto
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def test_winrm_port(hostname):
    """
    Prueba si WinRM está accesible (puerto 5985 HTTP o 5986 HTTPS)
    
    Args:
        hostname: Nombre del host
    
    Returns:
        dict: Resultado con puertos disponibles
    """
    result = {
        "hostname": hostname,
        "http_5985": False,
        "https_5986": False,
        "available": False
    }
    
    result["http_5985"] = test_port(hostname, 5985)
    result["https_5986"] = test_port(hostname, 5986)
    result["available"] = result["http_5985"] or result["https_5986"]
    
    return result


def get_local_ip():
    """
    Obtiene la IP local del equipo
    
    Returns:
        str: IP local o None
    """
    try:
        # Crear socket UDP (no necesita conectar realmente)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def test_internet_connectivity():
    """
    Prueba conectividad a internet
    
    Returns:
        dict: Resultado de las pruebas
    """
    targets = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("www.google.com", "Google Web")
    ]
    
    results = {
        "has_internet": False,
        "tests": []
    }
    
    for target, name in targets:
        ping_result = ping(target, count=1, timeout=3)
        test = {
            "target": target,
            "name": name,
            "success": ping_result["success"],
            "latency_ms": ping_result.get("latency_ms")
        }
        results["tests"].append(test)
        
        if ping_result["success"]:
            results["has_internet"] = True
    
    return results


def diagnose_connection(hostname, verbose=True):
    """
    Realiza diagnóstico completo de conexión a un host
    
    Args:
        hostname: Nombre del host
        verbose: Si True, muestra mensajes
    
    Returns:
        dict: Resultado del diagnóstico
    """
    result = {
        "hostname": hostname,
        "dns_resolved": False,
        "ip": None,
        "ping": False,
        "winrm_ports": False,
        "ready": False,
        "issues": []
    }
    
    # 1. Resolver DNS
    if verbose:
        print(f"🔍 Resolviendo {hostname}...")
    
    ip = resolve_hostname(hostname)
    if ip:
        result["dns_resolved"] = True
        result["ip"] = ip
        if verbose:
            print(f"   ✅ Resuelto a {ip}")
    else:
        result["issues"].append("No se puede resolver el nombre del host")
        if verbose:
            print(f"   ❌ No se puede resolver el nombre")
        return result
    
    # 2. Ping
    if verbose:
        print(f"🔍 Probando ping...")
    
    ping_result = ping(hostname, count=2, timeout=3)
    if ping_result["success"]:
        result["ping"] = True
        latency = ping_result.get("latency_ms", "?")
        if verbose:
            print(f"   ✅ Ping OK ({latency}ms)")
    else:
        result["issues"].append("El host no responde al ping")
        if verbose:
            print(f"   ❌ No responde al ping")
    
    # 3. Puertos WinRM
    if verbose:
        print(f"🔍 Verificando puertos WinRM...")
    
    winrm_result = test_winrm_port(hostname)
    if winrm_result["available"]:
        result["winrm_ports"] = True
        ports = []
        if winrm_result["http_5985"]:
            ports.append("5985 (HTTP)")
        if winrm_result["https_5986"]:
            ports.append("5986 (HTTPS)")
        if verbose:
            print(f"   ✅ Puerto(s) disponible(s): {', '.join(ports)}")
    else:
        result["issues"].append("Puertos WinRM (5985/5986) no accesibles")
        if verbose:
            print(f"   ❌ Puertos WinRM no accesibles")
    
    # Determinar si está listo
    result["ready"] = result["ping"] and result["winrm_ports"]
    
    return result

