"""
Progress Indicators - Barras de progreso y status display mejoradas
"""
import sys
import time
from typing import Optional
from colorama import Fore, Style, init
from .colors import Colors, ConsoleStyle

init(autoreset=True)
style = ConsoleStyle()


class ProgressBar:
    """Barra de progreso ASCII para operaciones largas"""
    
    def __init__(self, total: int, prefix: str = "", length: int = 50):
        """
        Inicializa la barra de progreso
        
        Args:
            total: Número total de items
            prefix: Prefijo a mostrar
            length: Longitud de la barra en caracteres
        """
        self.total = total
        self.prefix = prefix
        self.length = length
        self.current = 0
        self.start_time = time.time()
    
    def update(self, current: Optional[int] = None, suffix: str = ""):
        """
        Actualiza la barra de progreso con mejor formato visual
        
        Args:
            current: Valor actual (si None, incrementa en 1)
            suffix: Sufijo a mostrar
        """
        if current is not None:
            self.current = current
        else:
            self.current += 1
        
        percent = 100 * (self.current / float(self.total))
        filled_length = int(self.length * self.current // self.total)
        
        # Barra con colores según progreso
        if percent < 33:
            bar_color = Colors.RED
        elif percent < 66:
            bar_color = Colors.YELLOW
        else:
            bar_color = Colors.GREEN
        
        # Usar caracteres ASCII para mejor compatibilidad
        filled_char = "#" if percent >= 100 else "="
        empty_char = "-"
        filled_bar = f"{bar_color}{Style.BRIGHT}{filled_char}{Colors.RESET}" * filled_length
        empty_bar = f"{Colors.DIM}{empty_char}{Colors.RESET}" * (self.length - filled_length)
        bar = filled_bar + empty_bar
        
        # Calcular tiempo
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = self._format_time(eta)
            elapsed_str = self._format_time(elapsed)
            time_info = f"{Colors.CYAN}[*]{Colors.RESET} {elapsed_str} {Colors.DIM}|{Colors.RESET} {Colors.YELLOW}ETA: {eta_str}{Colors.RESET}"
        else:
            time_info = ""
        
        # Imprimir barra con mejor formato
        prefix_formatted = f"{Colors.CYAN}{self.prefix}{Colors.RESET}" if self.prefix else ""
        percent_formatted = f"{Colors.BOLD}{bar_color}{percent:.1f}%{Colors.RESET}"
        suffix_formatted = f"{Colors.WHITE}{suffix}{Colors.RESET}" if suffix else ""
        
        print(f'\r{prefix_formatted} [{bar}] {percent_formatted} {suffix_formatted} {time_info}', end='', flush=True)
        
        if self.current >= self.total:
            print()  # Nueva línea al finalizar
    
    def _format_time(self, seconds: float) -> str:
        """Formatea segundos a MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    
    def finish(self):
        """Finaliza la barra de progreso"""
        self.update(self.total)


class SpinnerProgress:
    """Spinner animado para operaciones sin progreso conocido"""
    
    # Spinner compatible con Windows usando caracteres ASCII
    SPINNERS = ['|', '/', '-', '\\', '|', '/', '-', '\\']
    
    def __init__(self, message: str = "Procesando"):
        """
        Inicializa el spinner
        
        Args:
            message: Mensaje a mostrar
        """
        self.message = message
        self.index = 0
        self.running = False
    
    def spin(self):
        """Muestra el siguiente frame del spinner"""
        if self.running:
            spinner = self.SPINNERS[self.index % len(self.SPINNERS)]
            print(f'\r{spinner} {self.message}...', end='', flush=True)
            self.index += 1
    
    def start(self):
        """Inicia el spinner"""
        self.running = True
        self.spin()
    
    def stop(self, final_message: str = "Completado"):
        """
        Detiene el spinner con mensaje formateado
        
        Args:
            final_message: Mensaje final a mostrar
        """
        self.running = False
        print(f'\r{style.success(final_message)}' + ' ' * 30)


class BatchProgressDisplay:
    """Display de progreso para operaciones batch"""
    
    def __init__(self, hosts: list):
        """
        Inicializa el display
        
        Args:
            hosts: Lista de hostnames
        """
        self.hosts = hosts
        self.status = {host: "⏸ Pendiente" for host in hosts}
        self.start_time = time.time()
    
    def update_host(self, hostname: str, status: str, icon: str = "⏳"):
        """
        Actualiza estado de un host con mejor formato
        
        Args:
            hostname: Nombre del host
            status: Estado actual
            icon: Icono a mostrar
        """
        # Aplicar colores según el estado
        if "[OK]" in icon or "Completado" in status:
            status_formatted = f"{Colors.GREEN}[OK] {status}{Colors.RESET}"
        elif "[X]" in icon or "Fallido" in status:
            status_formatted = f"{Colors.RED}[X] {status}{Colors.RESET}"
        elif "[*]" in icon or "En progreso" in status:
            status_formatted = f"{Colors.YELLOW}[*] {status}{Colors.RESET}"
        else:
            status_formatted = f"{Colors.CYAN}{icon} {status}{Colors.RESET}"
        
        self.status[hostname] = status_formatted
        self.refresh()
    
    def mark_complete(self, hostname: str, success: bool = True):
        """Marca un host como completado con mejor formato"""
        if success:
            self.update_host(hostname, "Completado", "[OK]")
        else:
            self.update_host(hostname, "Fallido", "[X]")
    
    def mark_in_progress(self, hostname: str):
        """Marca un host como en progreso"""
        self.update_host(hostname, "En progreso", "⏳")
    
    def refresh(self):
        """Refresca el display con mejor formato visual"""
        # Limpiar pantalla (opcional)
        # print('\033[2J\033[H')  # ANSI clear screen
        
        print(f"\n{Colors.CYAN}{'=' * 72}{Colors.RESET}")
        print(f"{Colors.CYAN}|{Colors.RESET}  {Colors.BOLD}{Colors.MAGENTA}[*] PROGRESO DE EJECUCION EN LOTE{Colors.RESET}                                    {Colors.CYAN}|{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 72}{Colors.RESET}\n")
        
        completed = sum(1 for s in self.status.values() if "[OK]" in s or "[X]" in s)
        total = len(self.hosts)
        progress_percent = (completed / total * 100) if total > 0 else 0
        
        # Mostrar cada host con mejor formato
        for hostname, status in self.status.items():
            print(f"   {Colors.BOLD}{Colors.WHITE}{hostname:25}{Colors.RESET} {status}")
        
        print(f"\n{Colors.CYAN}{'-' * 72}{Colors.RESET}")
        
        # Estadísticas
        if progress_percent < 33:
            progress_color = Colors.RED
        elif progress_percent < 66:
            progress_color = Colors.YELLOW
        else:
            progress_color = Colors.GREEN
        
        print(f"   {Colors.BOLD}Progreso:{Colors.RESET} {progress_color}{completed}/{total}{Colors.RESET} completados {Colors.DIM}({progress_percent:.1f}%){Colors.RESET}")
        
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed//60)}m {int(elapsed%60)}s"
        print(f"   {Colors.BOLD}Tiempo transcurrido:{Colors.RESET} {Colors.CYAN}{elapsed_str}{Colors.RESET}")
        
        print(f"{Colors.CYAN}{'=' * 72}{Colors.RESET}\n")

