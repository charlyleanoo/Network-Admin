from netmiko import ConnectHandler
import pandas as pd
import re  # Importante para usar `re.search`

AMBAR = "\033[93m"
GREEN = "\033[92m"
RED = "\033[31m"
BLUE = "\033[94m"
RESET = "\033[0m"

routers = [
    {"device_type": "cisco_ios", "host": "192.168.1.102", "username": "cisco", "password": "cisco", "secret": "cisco"},
    {"device_type": "cisco_ios", "host": "10.0.3.1", "username": "cisco", "password": "cisco", "secret": "cisco"},
    {"device_type": "cisco_ios", "host": "10.0.3.6", "username": "cisco", "password": "cisco", "secret": "cisco"},
]

rules = {
    "HTTPS habilitado": {
        "command": "show running-config | include ip http secure-server",
        "expected": "ip http secure-server",
    },
    "Telnet deshabilitado": {
        "command": "show running-config | include transport input",
        "expected": "transport input ssh",
    },
    "Solo una LoopBack": {
        "command": "show ip interface brief | include Loopback",
        "expected": 1,
    },
    "Syslog configurado": {
        "command": "show running-config | include logging host",
        "expected": "logging host",
    },
    "NTP configurado": {
        "command": "show running-config | include ntp server",
        "expected": "ntp server",
    },
    "Redireccion ICMP deshabilitada": {
        "command": "show running-config | include ip redirects",
        "expected": "no ip redirects",
    },
    "Seguridad en puertos Habilitados": {
        "command": "show running-config | include switchport port-security",
        "expected": "switchport port-security",
    }
}

def get_hostname(connection):
    """Obtiene el hostname del router usando 'show version'"""
    hostname_output = connection.send_command("show version | include uptime")
    hostname_match = re.search(r"(\S+) uptime is", hostname_output)
    return hostname_match.group(1) if hostname_match else "Desconocido"

def audit_routers(routers, rules):
    audit_results = []

    for router in routers:
        try:
            print(f"\n{GREEN}[+]{RESET} Conectando a {router['host']}...")
            net_connect = ConnectHandler(**router)
            net_connect.enable()

            hostname = get_hostname(net_connect)
            print(f"{GREEN}[+]{RESET} Iniciando auditoría en el router: {hostname}")

            for rule, details in rules.items():
                output = net_connect.send_command(details["command"])

                # Verificación para loopback
                if "LoopBack" in rule:
                    count = output.count("Loopback")
                    compliance = 100 if count == details["expected"] else 0
                else:
                    compliance = 100 if details["expected"] in output else 0

                print(f"{BLUE}- {RESET}{rule}: {compliance}")
                audit_results.append([hostname, rule, details["command"], output, compliance])
            
            net_connect.disconnect()

        except Exception as e:
            print(f"{RED}[+]{RESET} Error conectando al router {router['host']}: {e}")

    # Guardar en Excel
    if audit_results:
        df = pd.DataFrame(audit_results, columns=["Hostname", "Regla", "Comando", "Salida", "Estado"])
        excel_filename = "auditoria_routers.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"\n{AMBAR}[+]{RESET} Auditoría guardada en '{excel_filename}'")

audit_routers(routers, rules)
