import customtkinter as ctk
import socket
from tkinter import messagebox, simpledialog
import subprocess
import ctypes
import sys
import tempfile
import os
import wmi
from datetime import datetime


# ============ FUNCIONES ============
def ejecutar_como_admin():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        script = sys.executable
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", script, params, None, 1
        )
        sys.exit()

# ---- Obligatorio para pedir elevación ----
ejecutar_como_admin()

def check_user_AD():
    try:
        hostname = simpledialog.askstring("Buscar BitLocker", "Ingrese el nombre del equipo (hostname):")
        if not hostname:
            return

        ps_script = f'''
$computer = Get-ADComputer -Identity "{hostname}" -Properties DistinguishedName -ErrorAction Stop

$recoveryObjects = Get-ADObject -SearchBase $computer.DistinguishedName `
    -Filter 'objectClass -eq "msFVE-RecoveryInformation"' `
    -Properties 'msFVE-RecoveryPassword', 'WhenCreated'

if ($recoveryObjects.Count -eq 0) {{
    Write-Output "No se encontraron claves para {hostname}."
}} else {{
    foreach ($item in $recoveryObjects) {{
        Write-Output "Fecha: $($item.WhenCreated)"
        Write-Output "Clave: $($item.'msFVE-RecoveryPassword')"
        Write-Output "----"
    }}
}}
'''

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as f:
            f.write(ps_script)
            ps1_path = f.name

        resultado = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps1_path],
            capture_output=True, text=True
        )
        os.remove(ps1_path)

        salida = resultado.stdout.strip()

        ventana_resultado = ctk.CTkToplevel()
        ventana_resultado.title(f"Claves BitLocker: {hostname}")
        ventana_resultado.geometry("600x300")

        text_box = ctk.CTkTextbox(ventana_resultado, wrap="word")
        text_box.pack(expand=True, fill='both', padx=10, pady=10)
        text_box.insert("1.0", salida if salida else "No se encontraron claves.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")

def resolver_nombre_equipo(ip):
    try:
        host = socket.gethostbyaddr(ip)[0]
        return f"{ip} → {host}"
    except socket.herror:
        return f"No se pudo resolver el nombre para {ip} (gethostbyaddr)"


def resolver_ip_equipo(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return f"{hostname} → {ip}"
    except socket.gaierror:
        return f"No se pudo resolver la IP para {hostname}"


def buscar_nombre_o_ip():
    # Crear ventana de selección
    opcion = simpledialog.askstring(
        "Modo de búsqueda",
        "Escriba 'IP' para ingresar una IP o 'HOST' para ingresar un hostname:"
    )
    if not opcion:
        return

    opcion = opcion.strip().lower()
    if opcion == "ip":
        ip = simpledialog.askstring("Ingresar IP", "Ingrese la dirección IP:")
        if not ip:
            return
        resultado = resolver_nombre_equipo(ip)

    elif opcion == "host":
        hostname = simpledialog.askstring("Ingresar Hostname", "Ingrese el nombre del equipo:")
        if not hostname:
            return
        resultado = resolver_ip_equipo(hostname)

    else:
        messagebox.showerror("Error", "Opción inválida. Escriba 'ip' o 'host'.")
        return
    

    # ============ FUNCIONES NUEVAS ============

def chequeo_usuario_bloqueado():
    try:
        username = simpledialog.askstring("Chequeo de usuario", "Ingrese el nombre de usuario:")
        if not username:
            return

        # Script PowerShell para verificar si está bloqueado en AD
        ps_script = f'''
try {{
    $user = Get-ADUser -Identity "{username}" -Properties LockedOut
    if ($user.LockedOut -eq $true) {{
        Write-Output "El usuario {username} está BLOQUEADO."
    }} else {{
        Write-Output "El usuario {username} NO está bloqueado."
    }}
}} catch {{
    Write-Output "No se encontró el usuario {username} en Active Directory."
}}
'''

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as f:
            f.write(ps_script)
            ps1_path = f.name

        resultado = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps1_path],
            capture_output=True, text=True
        )
        os.remove(ps1_path)

        salida = resultado.stdout.strip()

        messagebox.showinfo("Resultado", salida if salida else "No se obtuvo resultado.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")



# ================== CREDENCIALES REMOTAS ==================
# Poné aquí tus credenciales del dominio (o locales del equipo remoto)

# 🔑 credenciales de dominio
USUARIO = "andreani.com.ar\\venom"
PASSWORD = "Covid2019..__"

# ================== HELPERS ==================
BATTERY_STATUS = {
    1: "Desconocido",
    2: "Cargando",
    3: "Descargando",
    4: "No cargando",
    5: "Completamente cargada",
    6: "Baja",
    7: "Críticamente baja",
    8: "En carga",
    9: "En carga y alta",
    10: "En carga y baja",
    11: "En carga y críticamente baja",
    12: "Sin batería",
    13: "No detectada"
}

def parse_wmi_date(wmi_dt):
    # Win32_BIOS.ReleaseDate suele venir como '20220701000000.000000+000'
    if not wmi_dt:
        return "N/D"
    try:
        base = wmi_dt.split('.')[0]  # yyyyMMddHHmmss
        dt = datetime.strptime(base, "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(wmi_dt)

def get_info_wmi(host="localhost", user=None, password=None):
    try:
        if host.lower() in ("", "localhost", "127.0.0.1"):
            conn = wmi.WMI()
        else:
            conn = wmi.WMI(computer=host, user=user, password=password)

        info = []

        # -------- Sistema Operativo --------
        for so in conn.Win32_OperatingSystem():
            info.append(f"Sistema Operativo: {so.Caption} {so.Version} ({so.OSArchitecture})")
            info.append(f"Build: {so.BuildNumber}")
            info.append(f"Último booteo: {so.LastBootUpTime}")

        # -------- Equipo / Hardware --------
        for sys in conn.Win32_ComputerSystem():
            info.append(f"Hostname: {sys.Name}")
            info.append(f"Fabricante/Modelo: {sys.Manufacturer} {sys.Model}")
            try:
                ram_gb = round(int(sys.TotalPhysicalMemory) / (1024**3), 2)
            except Exception:
                ram_gb = "N/D"
            info.append(f"Memoria RAM: {ram_gb} GB")

        for cpu in conn.Win32_Processor():
            info.append(f"Procesador: {cpu.Name} | Núcleos: {cpu.NumberOfCores} | Hilos: {cpu.NumberOfLogicalProcessors}")

        # -------- BIOS --------
        for bios in conn.Win32_BIOS():
            info.append(f"BIOS Fabricante: {bios.Manufacturer}")
            info.append(f"BIOS Versión: {bios.SMBIOSBIOSVersion}")
            info.append(f"BIOS Serial: {bios.SerialNumber}")
            info.append(f"BIOS Release: {parse_wmi_date(bios.ReleaseDate)}")

        # -------- Batería (si es notebook) --------
                # -------- Batería (si es notebook) --------
        bats = conn.Win32_Battery()
        if bats:
            for b in bats:
                estado = BATTERY_STATUS.get(b.BatteryStatus, str(b.BatteryStatus))
                info.append(f"Batería Estado: {estado}")

                if b.EstimatedChargeRemaining is not None:
                    info.append(f"Batería Carga: {b.EstimatedChargeRemaining}%")

                if b.EstimatedRunTime is not None and b.EstimatedRunTime > 0:
                    # Definimos un máximo de referencia, ej: 240 min = 4 horas
                    MAX_MINUTOS = 240  
                    porcentaje_tiempo = min(100, round((b.EstimatedRunTime / MAX_MINUTOS) * 100, 1))
                    info.append(f"Batería Tiempo restante: {b.EstimatedRunTime} min (~{porcentaje_tiempo}%)")
        else:
            info.append("Batería: No se detecta batería")


        # -------- Red (todas las NIC con IP) --------
        nics = conn.Win32_NetworkAdapterConfiguration(IPEnabled=True)
        if nics:
            for idx, nic in enumerate(nics, start=1):
                ip = nic.IPAddress[0] if nic.IPAddress else "N/D"
                gw = nic.DefaultIPGateway[0] if nic.DefaultIPGateway else "N/D"
                dns = ", ".join(nic.DNSServerSearchOrder) if nic.DNSServerSearchOrder else "N/D"
                info.append(f"NIC {idx}: {nic.Description}")
                info.append(f"    IP: {ip}")
                info.append(f"    MAC: {nic.MACAddress}")
                info.append(f"    Gateway: {gw}")
                info.append(f"    DNS: {dns}")
        else:
            info.append("Red: No hay NICs con IP habilitada")

        return "\n".join(info)

    except Exception as e:
        return f"❌ Error obteniendo información de '{host}': {e}"

# ================== UI ==================
def mostrar_info_sistema_dialog():
    try:
        dialog = ctk.CTkInputDialog(
            text="Ingrese el hostname (vacío = este equipo):",
            title="Consultar equipo por WMI"
        )
        host = dialog.get_input()
        host = host.strip() if host else "localhost"

        # Si es remoto, usamos credenciales guardadas
        if host.lower() in ("localhost", "127.0.0.1", ""):
            salida = get_info_wmi("localhost")
        else:
            salida = get_info_wmi(host, user=USUARIO, password=PASSWORD)

        # Ventana de resultado
        win = ctk.CTkToplevel()
        win.title(f"Información del sistema - {host}")
        win.geometry("820x560")

        # Caja de texto con scroll
        text_box = ctk.CTkTextbox(win, wrap="word")
        text_box.pack(expand=True, fill="both", padx=12, pady=12)
        text_box.insert("1.0", salida)
        text_box.configure(state="disabled")  # solo lectura

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el diálogo: {e}")



def salir():
    root.destroy()

# ============ INTERFAZ ============

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Soporte Windows 11 (Avanzado)")
root.geometry("450x400")
root.resizable(False, False)

label = ctk.CTkLabel(root, text="Seleccioná una tarea de mantenimiento", font=ctk.CTkFont(size=16, weight="bold"))
label.pack(pady=20)

btn2 = ctk.CTkButton(root, text="Recuperación de clave BL", width=300, command=check_user_AD)
btn2.pack(pady=10)

btn3 = ctk.CTkButton(root, text="Resolver nombre por IP/HOST", width=300, command=buscar_nombre_o_ip)
btn3.pack(pady=10)

btn3 = ctk.CTkButton(root, text="chequeo de user bloqueado  ", width=300, command=chequeo_usuario_bloqueado)
btn3.pack(pady=10)

btn3 = ctk.CTkButton(root, text="info de sistema", width=300, command=mostrar_info_sistema_dialog)
btn3.pack(pady=10)



btn_exit = ctk.CTkButton(root, text="Salir", width=300, command=salir)
btn_exit.pack(pady=20)

root.mainloop()



