from netmiko import ConnectHandler
import pandas as pd
import re
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment, Font

# Definir colores para la terminal
AMBAR = "\033[93m"
GREEN = "\033[92m"
RED = "\033[31m"
RESET = "\033[0m"

# Lista de routers
routers = [
    {"device_type": "cisco_ios", "host": "192.168.1.102", "username": "cisco", "password": "cisco", "secret": "cisco"},
    {"device_type": "cisco_ios", "host": "10.0.3.1", "username": "cisco", "password": "cisco", "secret": "cisco"},
    {"device_type": "cisco_ios", "host": "10.0.3.6", "username": "cisco", "password": "cisco", "secret": "cisco"},
]

# Reglas con sus comandos y remediaciones
rules = {
    "HTTPS habilitado": {"command": "show running-config | include ip http secure-server", "expected": "ip http secure-server", "remediation": "ip http secure-server"},
    "Telnet deshabilitado": {"command": "show running-config | include transport input", "expected": "transport input ssh", "remediation": "line vty 0 4\ntransport input ssh"},
    "Solo una LoopBack": {"command": "show ip interface brief | include Loopback", "expected": 1, "remediation": "interface Loopback1\nshutdown"},
    "Syslog configurado": {"command": "show running-config | include logging host", "expected": "logging host", "remediation": "logging host 192.168.1.1"},
    "NTP configurado": {"command": "show running-config | include ntp server", "expected": "ntp server", "remediation": "ntp server 192.168.1.1"},
    "Redireccion ICMP deshabilitada": {"command": "show running-config | include ip redirects", "expected": "no ip redirects", "remediation": "no ip redirects"},
    "Deshabilitar puertos no usados": {"command": "show interfaces status | include notconnect", "expected": "", "remediation": "interface range [puertos] \n shutdown"},
    "Banner de Advertencia": {"command": "show running-config | include banner login", "expected": "banner login", "remediation": "banner login #Acceso autorizado solamente#"},
    "Tiempo de inactividad de la consola": {"command": "show running-config | include exec-timeout", "expected": "exec-timeout", "remediation": "line con 0\nexec-timeout 5 0"},
    "Control de Acceso a la Consola": {"command": "show running-config | include login local", "expected": "login local", "remediation": "line vty 0 4\nlogin local"}
}

def get_hostname(connection):
    hostname_output = connection.send_command("show version | include uptime")
    hostname_match = re.search(r"(\S+) uptime is", hostname_output)
    return hostname_match.group(1) if hostname_match else "Desconocido"

def audit_routers(routers, rules):
    audit_results = {rule: {} for rule in rules}

    for router in routers:
        try:
            print(f"\n{GREEN}[+]{RESET} Conectando a {router['host']}...")
            net_connect = ConnectHandler(**router)
            net_connect.enable()
            hostname = get_hostname(net_connect)
            print(f"{GREEN}[+]{RESET} Iniciando auditoría en el router: {hostname}")

            for rule, details in rules.items():
                output = net_connect.send_command(details["command"])
                compliance = 100 if details["expected"] in output else 0
                print(f"{rule}: {'Cumple' if compliance == 100 else 'No cumple'}")
                audit_results[rule][hostname] = compliance

                if compliance == 0:
                    choice = input(f"{AMBAR}[?]{RESET} ¿Aplicar corrección para '{rule}' en {hostname}? (s/n): ")
                    if choice.lower() == 's':
                        if rule == "Deshabilitar puertos no usados":
                            interfaces = output.split("\n")
                            for interface in interfaces:
                                if interface:
                                    int_name = interface.split()[0]
                                    remediation_cmd = f"interface {int_name}\nshutdown"
                                    net_connect.send_config_set(remediation_cmd.split("\n"))
                        else:
                            net_connect.send_config_set(details["remediation"].split("\n"))
                        print(f"{GREEN}[+]{RESET} Remediación aplicada para {rule} en {hostname}.")

            net_connect.disconnect()
        except Exception as e:
            print(f"{RED}[+]{RESET} Error conectando al router {router['host']}: {e}")

audit_routers(routers, rules)
