import tkinter as tk
from tkinter import scrolledtext
import queue
import threading

class OutputWindow:
    """
    Ventana GUI de Tkinter para mostrar el progreso de una operación.
    """
    def __init__(self, hostname, operation_label):
        self.hostname = hostname
        self.operation_label = operation_label
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        
        # Iniciar la interfaz en el hilo principal
        self.root = None
        self.text_area = None
        self.status_label = None
        self.close_button = None
        
    def _setup_ui(self):
        self.root = tk.Tk()
        self.root.title(f"Operación: {self.operation_label} - {self.hostname}")
        self.root.geometry("800x500")
        self.root.configure(bg="#1e1e1e")
        
        # Estilo de colores oscuros
        bg_color = "#1e1e1e"
        fg_color = "#d4d4d4"
        accent_color = "#007acc"
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2d2d2d", height=40)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(
            header_frame, 
            text=f"🌐 Equipo: {self.hostname} | 🛠️ Operación: {self.operation_label}",
            bg="#2d2d2d", 
            fg="#ffffff",
            font=("Consolas", 10, "bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Text Area para Logs
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg=bg_color,
            fg=fg_color,
            insertbackground="white",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.configure(state='disabled')
        
        # Footer con estado y controles
        footer_frame = tk.Frame(self.root, bg="#2d2d2d", height=40)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            footer_frame,
            text="⏳ Ejecutando...",
            bg="#2d2d2d",
            fg=accent_color,
            font=("Consolas", 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Botón Detener (inicialmente habilitado)
        self.stop_button = tk.Button(
            footer_frame,
            text="🛑 Detener",
            command=self._on_stop_clicked,
            bg="#d11a2a",
            fg="white",
            state=tk.NORMAL,
            font=("Consolas", 9, "bold"),
            padx=15
        )
        self.stop_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.close_button = tk.Button(
            footer_frame,
            text="Cerrar",
            command=self.root.destroy,
            bg="#3e3e3e",
            fg="white",
            state=tk.DISABLED,
            font=("Consolas", 9),
            padx=20
        )
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Iniciar loop de chequeo de cola
        self.root.after(100, self._process_queue)
        
    def log(self, message):
        """Envía un mensaje a la cola para ser mostrado en la UI"""
        self.queue.put(message)
        
    def set_finished(self, success=True, reason=None):
        """Marca la operación como finalizada"""
        if reason == "CANCELLED":
            status = "🛑 Cancelado"
            color = "#ffcc00"
        else:
            status = "✅ Finalizado" if success else "❌ Fallido"
            color = "#4ec9b0" if success else "#f44747"
            
        self.queue.put(("FINISH", status, color))

    def _on_stop_clicked(self):
        """Manejador del botón detener"""
        self.stop_button.config(state=tk.DISABLED, text="⏳ Deteniendo...")
        self._stop_event.set()
        self.log("\n[!] Solicitando cancelación remota...")

    def is_stopped(self):
        """Verifica si se ha solicitado parar"""
        return self._stop_event.is_set()

    def _process_queue(self):
        """Procesa los mensajes de la cola y los inserta en el widget de texto"""
        try:
            while True:
                data = self.queue.get_nowait()
                if isinstance(data, tuple) and data[0] == "FINISH":
                    _, status, color = data
                    self.status_label.config(text=status, fg=color)
                    self.close_button.config(state=tk.NORMAL, bg="#0e639c")
                    self.stop_button.config(state=tk.DISABLED)
                else:
                    self.text_area.configure(state='normal')
                    self.text_area.insert(tk.END, str(data) + "\n")
                    self.text_area.see(tk.END)
                    self.text_area.configure(state='disabled')
        except queue.Empty:
            pass
        
        self.root.after(100, self._process_queue)

    def run(self):
        """Ejecuta el loop principal de Tkinter"""
        self._setup_ui()
        self.root.mainloop()
