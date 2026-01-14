import subprocess
import threading
import uuid
import time
import os
from datetime import datetime

class Job:
    def __init__(self, playbook, target_host, extra_vars=None):
        self.id = str(uuid.uuid4())[:8]
        self.playbook = playbook
        self.target_host = target_host
        self.extra_vars = extra_vars or {}
        self.status = "PENDING"
        self.start_time = None
        self.end_time = None
        self.process = None
        self.output = []
        self.error = None

    def to_dict(self):
        return {
            "id": self.id,
            "playbook": os.path.basename(self.playbook),
            "target": self.target_host,
            "status": self.status,
            "start_time": self.start_time.strftime("%H:%M:%S") if self.start_time else "-",
            "duration": self._get_duration()
        }

    def _get_duration(self):
        if not self.start_time: return "-"
        end = self.end_time or datetime.now()
        return str(end - self.start_time).split(".")[0]

class BackgroundEngine:
    def __init__(self):
        self.jobs = {}
        self._lock = threading.Lock()

    def launch_playbook(self, playbook_path, target_host, extra_vars=None):
        job = Job(playbook_path, target_host, extra_vars)
        with self._lock:
            self.jobs[job.id] = job
        
        thread = threading.Thread(target=self._execute, args=(job,))
        thread.daemon = True
        thread.start()
        return job.id

    def _execute(self, job):
        job.status = "RUNNING"
        job.start_time = datetime.now()
        
        cmd = [
            "ansible-playbook", 
            job.playbook,
            "-i", "inventory/hosts.ini", # Ajustar según tu estructura
            "-e", f"target_host={job.target_host}"
        ]
        
        for k, v in job.extra_vars.items():
            cmd.extend(["-e", f"{k}={v}"])

        try:
            # Usamos subprocess para tener control total del PID y la salida
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

    def cancel_job(self, job_id):
        with self._lock:
            job = self.jobs.get(job_id)
            if job and job.status == "RUNNING" and job.process:
                job.process.terminate()
                job.status = "CANCELLED"
                job.end_time = datetime.now()
                return True
        return False

    def get_all_jobs(self):
        with self._lock:
            return [job.to_dict() for job in self.jobs.values()]

    def get_job_output(self, job_id):
        with self._lock:
            job = self.jobs.get(job_id)
            return job.output if job else []
