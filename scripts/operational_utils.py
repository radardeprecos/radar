import os
import datetime

def run_backup():
    print(f"[{datetime.datetime.now()}] Backup simulado realizado.")
    return True

def send_alert(message, subject="Alerta"):
    print(f"[{datetime.datetime.now()}] ALERTA ENVIADO [{subject}]: {message}")
    return True

def log_event(event):
    os.makedirs('logs', exist_ok=True)
    with open('logs/events.log', 'a') as f:
        f.write(f"[{datetime.datetime.now()}] {event}\n")
