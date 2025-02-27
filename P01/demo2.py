from netmiko import ConnectHandler
# Define the device parameters
print("*** Creating network Object...")
device = {
'device_type': 'cisco_ios_telnet',
'ip': '192.168.5.47',
'username': 'cisco',
'password': 'cisco',
'port': 23, # Telnet port
}
# Connect to the device
print("*** Connecting to device")
net_connect = ConnectHandler(**device)
# Send a command to the device
print("*** Sending config commands:")
commands = ['interface eth1/0',
'description AdminRedes',
'bandwidth 100']
output = net_connect.send_config_set(commands)
# Print the output
print(output)
print("*** Disconnecting ")
# Disconnect from the device
net_connect.disconnect()
