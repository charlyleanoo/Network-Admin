from netmiko import ConnectHandler
import pandas as pd
import re
from openpyxl import load_workbook

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
    "Solo una LoopBack": {"command": "show ip interface brief | include Loopback", "expected": 1, "remediation": "no interface Loopback1"},
    "Syslog configurado": {"command": "show running-config | include logging host", "expected": "logging host", "remediation": "logging host 192.168.1.84"},
    "NTP configurado": {"command": "show running-config | include ntp server", "expected": "ntp server", "remediation": "ntp server 192.168.1.84"},
    "Redireccion ICMP deshabilitada": {"command": "show running-config | include ip redirects", "expected": "no ip redirects", "remediation": "interface e1/0\nno ip redirects"},
    "IP Source Routing deshabilitado": {"command": "show running-config | include ip source-route", "expected": "no ip source-route", "remediation": "no ip source-route"},
    "Banner de Advertencia": {"command": "show running-config | include banner login", "expected": "banner login", "remediation": "banner login #Acceso autorizado solamente#"},
    "Tiempo de inactividad de la consola": {"command": "show running-config | include exec-timeout", "expected": "exec-timeout", "remediation": "line con 0\nexec-timeout 5 0"},
    "Control de Acceso a la Consola": {"command": "show running-config | include login local", "expected": "login local", "remediation": "line vty 0 4\nlogin local\npassword cisco"}
}

def get_hostname(connection):
    hostname_output = connection.send_command("show version | include uptime")
    hostname_match = re.search(r"(\S+) uptime is", hostname_output)
    return hostname_match.group(1) if hostname_match else "Desconocido"

def execute_audit(connection, hostname, rules):
    audit_results = {}
    for rule, details in rules.items():
        output = connection.send_command(details["command"])
        if isinstance(details["expected"], int):
            count = len(output.strip().split("\n"))  # Contar las líneas devueltas
            compliance = 100 if count == details["expected"] else 0
        else:
            expected_str = str(details["expected"])  # Asegurar que siempre sea una cadena
            if f"no {expected_str}" in output:
                compliance = 0
            elif expected_str in output:
                compliance = 100
            else:
                compliance = 0
        print(f"{rule}: {'Cumple' if compliance == 100 else 'No cumple'}")
        audit_results[rule] = compliance
    return audit_results

def audit_routers(routers, rules):
    initial_audit_results = {rule: {} for rule in rules}  # Resultados antes de la remediación
    final_audit_results = {rule: {} for rule in rules}  # Resultados después de la remediación

    for router in routers:
        try:
            print(f"\n{GREEN}[+]{RESET} Conectando a {router['host']}...")
            net_connect = ConnectHandler(**router)
            net_connect.enable()
            hostname = get_hostname(net_connect)
            print(f"{GREEN}[+]{RESET} Iniciando auditoría en el router: {hostname}")

            # Primera auditoría antes de la remediación
            initial_results = execute_audit(net_connect, hostname, rules)
            for rule, compliance in initial_results.items():
                initial_audit_results[rule][hostname] = compliance  # Guardar resultado inicial

                if compliance == 0:
                    choice = input(f"{AMBAR}[?]{RESET} ¿Aplicar corrección para '{rule}' en {hostname}? (s/n): ")
                    if choice.lower() == 's':
                        net_connect.send_config_set(rules[rule]["remediation"].split("\n"))
                        print(f"{GREEN}[+] Remediación aplicada para {rule} en {hostname}.")

            # Segunda auditoría después de la remediación
            updated_results = execute_audit(net_connect, hostname, rules)
            for rule, compliance in updated_results.items():
                final_audit_results[rule][hostname] = compliance  # Guardar resultado final

            net_connect.disconnect()
        except Exception as e:
            print(f"{RED}[+]{RESET} Error conectando al router {router['host']}: {e}")

    # Convertir a DataFrame
    df_initial = pd.DataFrame(initial_audit_results).T.fillna(0)
    df_initial.loc["Calificación individual"] = df_initial.mean().round(2)
    calificacion_total_initial = df_initial.loc["Calificación individual"].mean().round(2)
    df_initial.loc["Calificación Total"] = [""] * len(df_initial.columns)
    df_initial.at["Calificación Total", "Calificación Total"] = calificacion_total_initial

    df_final = pd.DataFrame(final_audit_results).T.fillna(0)
    df_final.loc["Calificación individual"] = df_final.mean().round(2)
    calificacion_total_final = df_final.loc["Calificación individual"].mean().round(2)
    df_final.loc["Calificación Total"] = [""] * len(df_final.columns)
    df_final.at["Calificación Total", "Calificación Total"] = calificacion_total_final

    # Guardar en Excel en hojas separadas
    excel_filename = "auditoria_comparativa.xlsx"
    with pd.ExcelWriter(excel_filename) as writer:
        df_initial.to_excel(writer, sheet_name="Antes de remediación")
        df_final.to_excel(writer, sheet_name="Después de remediación")

    print(f"\n{AMBAR}[+]{RESET} Auditoría guardada en '{excel_filename}' con dos tablas.")

audit_routers(routers, rules)
