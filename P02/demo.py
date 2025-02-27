from netmiko import ConnectHandler
import re

AMBAR = "\033[93m"
BLUE = "\033[94m"
GREEN = "\033[92m"
RESET = "\033[0m"
 
routers = [
    {"device_type": "cisco_ios_ssh", "host": "192.168.1.102", "username": "cisco", "password": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.1", "username": "cisco", "password": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.6", "username": "cisco", "password": "cisco"},
]
 
def extract_ips_interfaces_and_status(output):
     """ Extrae interfaces, IPs y estado de la salida del comando """
     pattern = re.findall(r"(\S+)\s+([\d.]+)\s+\S+\s+\S+\s+(\S+\s*\S*)", output)
     return pattern
 
for router in routers:
     connection = ConnectHandler(**router)
     print(f"\n{GREEN}[+]{RESET} Conectando a -> {BLUE}{router['host']}{RESET}\n")
     # Obtener el hostname del dispositivo desde `show version | include uptime`
     hostname_output = connection.send_command("show version | include uptime")
     hostname_match = re.search(r"(\S+) uptime is", hostname_output)
     hostname = hostname_match.group(1) if hostname_match else "Desconocido"
     print(f"{GREEN}[+]{RESET} Hostname del dispositivo: {AMBAR}{hostname}{RESET}\n")
     # Obtener las interfaces con sus IPs y estado
     output = connection.send_command("show ip interface brief")
     interfaces_ips_and_status = extract_ips_interfaces_and_status(output)
     print(f"\nDirecciones IP y estado de las interfaces en {hostname}:\n")
     for interface, ip, status in interfaces_ips_and_status:
         # Normalizar el estado
         if "administratively down" in status:
             status = "Administratively Down"
         elif "down" in status:
             status = "Down"
         elif "up" in status:
             status = "Up"
         print(f"Interfaz: {interface} -> IP: {BLUE}{ip}{RESET} -> Estado: {status}")

print("\n")
connection.disconnect()
