# features.py
class AlwaysOpenFeatures:
    """Características para modo estación permanente"""
    
    @staticmethod
    def auto_refresh_inventory():
        """Refrescar inventario automáticamente cada X minutos"""
        # Usar threading.Timer o schedule
        pass
    
    @staticmethod  
    def notification_system():
        """Sistema de notificaciones en terminal"""
        # Usar rich.notifications o crear propio
        pass
    
    @staticmethod
    def session_persistence():
        """Guardar estado de sesión"""
        # Guardar favoritos, hosts frecuentes, etc.
        pass
    
    @staticmethod
    def hotkey_support():
        """Soporte para atajos de teclado globales"""
        # Usar keyboard library (con sudo si necesario)
        pass
    
    @staticmethod
    def background_monitoring():
        """Monitoreo en segundo plano"""
        # Verificar estado de servicios/hosts
        pass