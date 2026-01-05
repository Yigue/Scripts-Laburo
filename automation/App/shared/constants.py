"""
Constantes globales de la aplicación
Centraliza valores hardcoded para facilitar configuración
"""

# ============================================================================
# TIMEOUTS (en segundos)
# ============================================================================
DEFAULT_TIMEOUT = 120
LONG_OPERATION_TIMEOUT = 1800  # 30 minutos (Dell Command, Office, etc)
CONNECTION_TIMEOUT = 30
SHORT_TIMEOUT = 10

# ============================================================================
# LÍMITES DE EJECUCIÓN
# ============================================================================
MAX_PARALLEL_HOSTS = 10
MAX_SESSIONS_PER_HOST = 3
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # segundos
RETRY_BACKOFF = 2  # multiplicador

# ============================================================================
# PATHS DE RECURSOS
# ============================================================================
TEMP_DIR = "C:\\TEMP"
TOOLS_NETWORK_PATH = r"\\pc101338\c$\Tools"

# Instaladores
DELL_COMMAND_INSTALLER = "Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
NOSLEEP_EXE = "NoSleep.exe"
OFFICE_SETUP = "setup.exe"
OFFICE_CONFIG = "config.xml"

# ============================================================================
# CACHE TTL (en segundos)
# ============================================================================
CACHE_TTL_SOFTWARE_LIST = 300  # 5 minutos
CACHE_TTL_SYSTEM_INFO = 600    # 10 minutos
CACHE_TTL_SERVICES = 120       # 2 minutos
CACHE_TTL_PROCESS_LIST = 60    # 1 minuto
CACHE_TTL_EVENT_LOGS = 60      # 1 minuto

# ============================================================================
# PATTERNS DE VALIDACIÓN
# ============================================================================
HOSTNAME_PATTERN = r'^[A-Z]{2}\d{6}$'  # Ej: NB001234, PC005678
IP_PATTERN = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
MAC_PATTERN = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'

# ============================================================================
# KEYS DE ACTIVACIÓN WINDOWS
# ============================================================================
WINDOWS_ACTIVATION_KEYS = [
    "P9BHN-HYVGH-DVK3V-JHPJ6-HFR9M",
    "3BRT8-N267D-TXT8G-W2F7F-JHW4K",
    "22JFY-NPQ9G-RQ6P2-9PYM7-2R6FT"
]

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
LOG_RETENTION_DAYS = 30

# ============================================================================
# PORTS
# ============================================================================
WINRM_HTTP_PORT = 5985
WINRM_HTTPS_PORT = 5986
SMB_PORT = 445
RDP_PORT = 3389

# ============================================================================
# COLORES PARA CLI (colorama)
# ============================================================================
COLOR_SUCCESS = "green"
COLOR_ERROR = "red"
COLOR_WARNING = "yellow"
COLOR_INFO = "cyan"
COLOR_HIGHLIGHT = "magenta"

# ============================================================================
# LÍMITES DE TAMAÑO DE ARCHIVO
# ============================================================================
MAX_FILE_LINES = 250  # Máximo recomendado de líneas por archivo
IDEAL_FILE_LINES = 150  # Ideal de líneas por archivo

