from netmiko import ConnectHandler
import re
from datetime import datetime

# Lista de routers
routers = [
    {"device_type": "cisco_ios_ssh", "host": "192.168.1.102", "username": "cisco", "password": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.1", "username": "cisco", "password": "cisco"},
    {"device_type": "cisco_ios_ssh", "host": "10.0.3.6", "username": "cisco", "password": "cisco"},
]

def extract_ips_interfaces_and_status(output):
    """ Extrae interfaces, IPs y estado de la salida del comando """
    # Patrón actualizado para capturar correctamente la salida de 'show ip interface brief'
    pattern = r"(\S+)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+\w+\s+\w+\s+(up|down|administratively down)"
    matches = re.finditer(pattern, output, re.MULTILINE)
    return [(match.group(1), match.group(2), match.group(3)) for match in matches]

def generate_html(network_data):
    """Genera el contenido HTML con los datos de red"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Información de Red</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                color: #333;
                text-align: center;
            }}
            .device-section {{
                background-color: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
            }}
            .status-up {{
                color: green;
                font-weight: bold;
            }}
            .status-down {{
                color: red;
                font-weight: bold;
            }}
            .timestamp {{
                text-align: center;
                color: #666;
                margin-top: 20px;
            }}
            .debug-info {{
                color: #666;
                font-size: 0.8em;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Información de Dispositivos de Red</h1>
    """
    
    # Agregar sección para cada dispositivo
    for device_data in network_data:
        html_content += f"""
            <div class="device-section">
                <h2>Dispositivo: {device_data['hostname']}</h2>
                <p>Dirección IP de gestión: {device_data['management_ip']}</p>
                <table>
                    <thead>
                        <tr>
                            <th>Interfaz</th>
                            <th>Dirección IP</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Agregar información de depuración
        html_content += f"""
                <tr><td colspan="3" class="debug-info">
                    Número de interfaces encontradas: {len(device_data['interfaces'])}
                </td></tr>
        """
        
        for interface in device_data['interfaces']:
            status_class = "status-up" if "up" in interface['status'].lower() else "status-down"
            html_content += f"""
                        <tr>
                            <td>{interface['name']}</td>
                            <td>{interface['ip']}</td>
                            <td class="{status_class}">{interface['status']}</td>
                        </tr>
            """
            
        html_content += """
                    </tbody>
                </table>
            </div>
        """
    
    # Agregar timestamp y cerrar HTML
    html_content += f"""
            <p class="timestamp">Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    network_data = []
    
    for router in routers:
        try:
            connection = ConnectHandler(**router)
            print(f"\n[+] Conectando a -> {router['host']}\n")
            
            # Obtener hostname
            hostname_output = connection.send_command("show version | include uptime")
            hostname_match = re.search(r"(\S+) uptime is", hostname_output)
            hostname = hostname_match.group(1) if hostname_match else "Desconocido"
            
            # Obtener interfaces
            output = connection.send_command("show ip interface brief")
            print(f"\n[DEBUG] Salida del comando para {hostname}:\n{output}\n")  # Debug output
            
            interfaces_data = extract_ips_interfaces_and_status(output)
            print(f"[DEBUG] Interfaces encontradas: {len(interfaces_data)}")  # Debug output
            
            # Preparar datos del dispositivo
            device_data = {
                'hostname': hostname,
                'management_ip': router['host'],
                'interfaces': []
            }
            
            for interface, ip, status in interfaces_data:
                # Normalizar estado
                if "administratively down" in status.lower():
                    status = "Administratively Down"
                elif "down" in status.lower():
                    status = "Down"
                elif "up" in status.lower():
                    status = "Up"
                
                device_data['interfaces'].append({
                    'name': interface,
                    'ip': ip,
                    'status': status
                })
                print(f"[DEBUG] Agregada interfaz: {interface} - {ip} - {status}")  # Debug output
            
            network_data.append(device_data)
            connection.disconnect()
            
        except Exception as e:
            print(f"Error al conectar con {router['host']}: {str(e)}")
    
    # Generar y guardar HTML
    html_content = generate_html(network_data)
    with open('network_info.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n[+] Archivo HTML generado como 'network_info.html'")

if __name__ == "__main__":
    main()