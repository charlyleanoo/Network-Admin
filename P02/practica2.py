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
 

 