"""
Módulo para calibrar impresoras Zebra vía WiFi
Corresponde a la opción 10 del menú
"""
import socket


def calibrar_zebra(ip: str, port: int = 9100):
    """
    Envía comando de calibración a impresora Zebra
    
    Args:
        ip: Dirección IP de la impresora
        port: Puerto RAW (default 9100)
    
    Returns:
        bool: True si el comando se envió correctamente
    """
    # Comando ZPL de calibración
    zpl_command = "~JC\r\n"
    
    try:
        # Conectar por TCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)
        client.connect((ip, port))
        
        # Enviar comando
        client.sendall(zpl_command.encode())
        
        # Cerrar conexión
        client.close()
        
        return True
        
    except socket.timeout:
        print(f"❌ Timeout conectando a {ip}:{port}")
        return False
    except ConnectionRefusedError:
        print(f"❌ Conexión rechazada por {ip}:{port}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def ejecutar(executor=None, hostname: str = None):
    """
    Ejecuta la calibración de impresora Zebra
    
    Args:
        executor: No usado, incluido por compatibilidad con el menú
        hostname: No usado, se pide la IP directamente
    """
    print("\n🖨️ Calibración de Impresora Zebra")
    print()
    
    ip = input("Dirección IP de la impresora Zebra: ").strip()
    if not ip:
        print("❌ Debe ingresar una IP")
        input("\nPresioná ENTER para continuar...")
        return
    
    # Validar formato IP básico
    parts = ip.split('.')
    if len(parts) != 4:
        print("❌ Formato de IP inválido")
        input("\nPresioná ENTER para continuar...")
        return
    
    print(f"\n📡 Enviando comando de calibración a {ip}...")
    
    if calibrar_zebra(ip):
        print(f"✅ Calibración enviada correctamente a {ip}")
        print("   La impresora debería comenzar a calibrar los medios")
    else:
        print(f"❌ No se pudo enviar el comando de calibración")
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🖨️ CALIBRAR ZEBRA WIFI")
    print("=" * 60)
    
    ejecutar()


if __name__ == "__main__":
    main()

