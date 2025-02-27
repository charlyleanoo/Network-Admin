import os
import difflib
import datetime
import shutil
from netmiko import ConnectHandler
import subprocess

# Configuración de los dispositivos (añadir más si es necesario)
routers = [
    {"device_type": "cisco_ios_ssh", "host": "192.168.1.102", "username": "cisco", "password": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.1", "username": "cisco", "password": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.6", "username": "cisco", "password": "cisco"},
]

# Ruta del repositorio donde se guardarán los backups
REPO_PATH = "/Users/Erika/Documents/admin_redes/Network-Admin"
os.makedirs(REPO_PATH, exist_ok=True)

# Función para obtener la configuración del router
def get_config(device):
    try:
        connection = ConnectHandler(**device)
        config = connection.send_command("show running-config")
        connection.disconnect()
        return config
    except Exception as e:
        print(f"❌ Error conectando a {device['host']}: {e}")
        return None

# Función para guardar y comparar backups
def save_backup(device, config):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    device_folder = os.path.join(REPO_PATH, device["host"])  # Usa la IP en lugar del nombre
    os.makedirs(device_folder, exist_ok=True)
    
    new_backup_file = os.path.join(device_folder, f"backup_{timestamp}.txt")
    latest_backup_file = os.path.join(device_folder, "latest_backup.txt")

    # Guardar nuevo backup
    with open(new_backup_file, "w") as file:
        file.write(config)

    # Si ya existe un backup anterior, compararlo
    if os.path.exists(latest_backup_file):
        with open(latest_backup_file, "r") as old_file:
            old_config = old_file.readlines()
        with open(new_backup_file, "r") as new_file:
            new_config = new_file.readlines()
        
        # Si hay diferencias, reemplazar el archivo
        if old_config != new_config:
            print(f"🔄 Cambios detectados en {device['host']}. Actualizando backup...")
            shutil.copy(new_backup_file, latest_backup_file)
            return True  # Se detectaron cambios
        else:
            print(f"✅ No hay cambios en {device['host']}. Conservando backup anterior.")
            os.remove(new_backup_file)  # Eliminar el archivo nuevo innecesario
            return False
    else:
        print(f"📌 No había backups previos para {device['host']}. Creando uno nuevo...")
        shutil.copy(new_backup_file, latest_backup_file)
        return True

# Función para subir cambios a GitHub
def push_to_github():
    os.chdir(REPO_PATH)
    subprocess.run(["git", "add", "."], check=True)
    commit_message = f"Backup actualizado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)

# 🔹 **Ejecutar el script**
if __name__ == "__main__":
    changes_detected = False

    for router in routers:
        print(f"🔌 Conectando a {router['host']}...")
        config = get_config(router)
        if config:
            if save_backup(router, config):
                changes_detected = True

    # Subir cambios a GitHub si hubo modificaciones
    if changes_detected:
        print("🚀 Subiendo cambios a GitHub...")
        push_to_github()
        print("✅ Backups actualizados en GitHub.")
    else:
        print("🔍 No hubo cambios, no se subió nada a GitHub.")
