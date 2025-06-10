
import argparse
import time

from lib.digitalocean import create_droplet
from lib.env import save_ip_to_ansible_inventory

if __name__ == "__main__":

    # parser = argparse.ArgumentParser(description='Create a new droplet and set the new host ip')
    # parser.add_argument('-n', type=str, help='The name of the droplet', required=True)
    # args = parser.parse_args()

    # ip = create_droplet(args.n)
    save_ip_to_ansible_inventory("64.23.234.219")
    
    print("Giving the droplet 30 seconds to be ready...\n")
    time.sleep(30)  # wait for the droplet to be ready