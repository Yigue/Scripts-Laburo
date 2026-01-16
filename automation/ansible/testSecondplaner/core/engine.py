"""
Motor de ejecución en segundo plano para playbooks de Ansible
"""
import subprocess
import threading
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, List, Any


class Job:
    """Representa un trabajo/job de ejecución de playbook"""
    
    def __init__(self, playbook: str, target_host: str, extra_vars: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())[:8]
        self.playbook = playbook
        self.target_host = target_host
        self.extra_vars = extra_vars or {}
        self.status = "PENDING"
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.process: Optional[subprocess.Popen] = None
        self.output: List[str] = []
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convertir job a diccionario para visualización"""
        return {
            "id": self.id,
            "playbook": os.path.basename(self.playbook),
            "target": self.target_host,
            "status": self.status,
            "start_time": self.start_time.strftime("%H:%M:%S") if self.start_time else "-",
            "duration": self._get_duration()
        }

    def _get_duration(self) -> str:
        """Calcular duración del job"""
        if not self.start_time:
            return "-"
        end = self.end_time or datetime.now()
        return str(end - self.start_time).split(".")[0]


class BackgroundEngine:
    """Motor de ejecución de playbooks en segundo plano"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def launch_playbook(self, playbook_path: str, target_host: str, extra_vars: Optional[Dict[str, Any]] = None) -> str:
        """
        Lanzar un playbook en segundo plano
        
        Args:
            playbook_path: Ruta al playbook de Ansible
            target_host: Host objetivo
            extra_vars: Variables adicionales para Ansible
            
        Returns:
            ID del job creado
        """
        job = Job(playbook_path, target_host, extra_vars)
        with self._lock:
            self.jobs[job.id] = job
        
        thread = threading.Thread(target=self._execute, args=(job,))
        thread.daemon = True
        thread.start()
        return job.id

    def _execute(self, job: Job) -> None:
        """Ejecutar el job en un hilo separado"""
        job.status = "RUNNING"
        job.start_time = datetime.now()
        
        cmd = [
            "ansible-playbook", 
            job.playbook,
            "-i", "inventory/hosts.ini",
            "-e", f"target_host={job.target_host}"
        ]
        
        # Agregar check mode si está activo
        if job.extra_vars and job.extra_vars.get("check_mode"):
            cmd.append("--check")
        
        # Agregar verbosity si está configurado
        verbosity = job.extra_vars.get("verbosity", 0) if job.extra_vars else 0
        if verbosity > 0:
            cmd.append("-" + "v" * min(verbosity, 4))
        
        # Agregar extra vars (excluyendo los flags internos)
        for k, v in job.extra_vars.items():
            if k not in ("check_mode", "verbosity"):
                cmd.extend(["-e", f"{k}={v}"])

        try:
            job.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            for line in job.process.stdout:
                job.output.append(line.strip())
            
            job.process.wait()
            
            if job.process.returncode == 0:
                job.status = "SUCCESS"
            else:
                job.status = "FAILED"
                job.error = f"Return code: {job.process.returncode}"

        except Exception as e:
            job.status = "FAILED"
            job.error = str(e)
        finally:
            job.end_time = datetime.now()

    def cancel_job(self, job_id: str) -> bool:
        """Cancelar un job en ejecución"""
        with self._lock:
            job = self.jobs.get(job_id)
            if job and job.status == "RUNNING" and job.process:
                job.process.terminate()
                job.status = "CANCELLED"
                job.end_time = datetime.now()
                return True
        return False

    def get_all_jobs(self) -> List[Dict[str, str]]:
        """Obtener todos los jobs"""
        with self._lock:
            return [job.to_dict() for job in self.jobs.values()]

    def get_job_output(self, job_id: str) -> List[str]:
        """Obtener salida de un job"""
        with self._lock:
            job = self.jobs.get(job_id)
            return job.output if job else []
