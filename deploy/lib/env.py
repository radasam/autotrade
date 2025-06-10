import os

NEW_HOST_IP_ENV_VAR = "NEW_HOST_IP"

def save_ip_to_ansible_inventory(ip: str, inventory_path: str = './deploy/ansible', overwrite: bool = True):
    # create the inventory file if it does not exist
    try:
        with open(f"{inventory_path}/hosts", "x") as f:
            pass  # File created
    except FileExistsError:
        pass

    with open(f"{inventory_path}/hosts", "w" if overwrite else "a") as f:
        f.write(f"[vms]\n")
        f.write(f"{ip}\n")
    
