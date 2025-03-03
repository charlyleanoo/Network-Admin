import os
import re
import difflib
import datetime
import shutil
import schedule
import time
from netmiko import ConnectHandler
import subprocess

AMBAR = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Ruta donde se guardarán los backups
REPO_PATH = "/Users/Erika/Documents/admin_redes/Network-Admin/P02/BackUps"
os.makedirs(REPO_PATH, exist_ok=True)

# Configuración de los dispositivos
routers = [
    {"device_type": "cisco_ios_ssh", "host": "192.168.1.102", "username": "cisco", "password": "cisco", "secret": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.1", "username": "cisco", "password": "cisco", "secret": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.6", "username": "cisco", "password": "cisco", "secret": "cisco"},
]

# Función para obtener el nombre del router (hostname)
def get_hostname(connection):
    hostname_output = connection.send_command("show version | include uptime")
    hostname_match = re.search(r"(\S+) uptime is", hostname_output)
    return hostname_match.group(1) if hostname_match else "Desconocido"

# Función para obtener la configuración del router
def get_config(device):
    try:
        connection = ConnectHandler(**device)
        connection.enable()

        # Obtener el hostname antes de ejecutar show running-config
        hostname = get_hostname(connection)

        # Obtener la configuración del router
        config = connection.send_command("show running-config")
        connection.disconnect()
        return hostname, config  # Devuelve el nombre y la configuración
    except Exception as e:
        print(f"❌ Error conectando a {device['host']}: {e}")
        return None, None

# Función para guardar y comparar backups
def save_backup(device, hostname, config):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Guardar el backup dentro de una carpeta con el nombre del router
    device_folder = os.path.join(REPO_PATH, hostname)
    os.makedirs(device_folder, exist_ok=True)

    new_backup_file = os.path.join(device_folder, f"backup_{timestamp}.txt")
    latest_backup_file = os.path.join(device_folder, "latest_backup.txt")

    with open(new_backup_file, "w") as file:
        file.write(config)

    if os.path.exists(latest_backup_file):
        with open(latest_backup_file, "r") as old_file:
            old_config = old_file.readlines()
        with open(new_backup_file, "r") as new_file:
            new_config = new_file.readlines()

        if old_config != new_config:
            print(f"🔄 Cambios detectados en {hostname} ({device['host']}). Actualizando backup...")
            shutil.copy(new_backup_file, latest_backup_file)
            return True
        else:
            print(f"{AMBAR}->{RESET} No hay cambios en {hostname} ({device['host']}). Conservando backup anterior.")
            os.remove(new_backup_file)
            return False
    else:
        print(f"📌 No había backups previos para {hostname} ({device['host']}). Creando uno nuevo...")
        shutil.copy(new_backup_file, latest_backup_file)
        return True

# Función para subir cambios a GitHub
def push_to_github():
    os.chdir(REPO_PATH)
    
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("❌ Git no está instalado o no está configurado en el sistema.")
        return

    subprocess.run(["git", "add", "."], check=True)
    commit_message = f"Backup actualizado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)

# Función para ejecutar respaldos periódicamente
def backup_job():
    print("🔄 Ejecutando respaldo de configuración...")
    changes_detected = False

    for router in routers:
        print(f"{GREEN}[+]{RESET} Conectando a {router['host']}...")

        hostname, config = get_config(router)
        if hostname and config:
            if save_backup(router, hostname, config):
                changes_detected = True

    if changes_detected:
        print("🚀 Subiendo cambios a GitHub...")
        push_to_github()
        print("✅ Backups actualizados en GitHub.")
    else:
        print("🔍 No hubo cambios, no se subió nada a GitHub.")

# Programar la ejecución del respaldo cada 5 segundos
schedule.every(5).seconds.do(backup_job)

if __name__ == "__main__":
    print("📢 Iniciando el servicio de respaldo automático cada 5 segundos...")
    while True:
        schedule.run_pending()
        time.sleep(1)
