import os
import time

from digitalocean import Droplet, Manager

digitalocean_token = os.getenv("DIGITALOCEAN_TOKEN")
digitalocean_region = os.getenv("DIGITALOCEAN_REGION", "sfo3")
digitalocean_image = os.getenv("DIGITALOCEAN_IMAGE", "debian-12-x64")
digitalocean_size = os.getenv("DIGITALOCEAN_SIZE", "s-1vcpu-1gb-35gb-intel")

def create_droplet(name, **kwargs) -> str:

    manager = Manager(token=digitalocean_token)
    keys = manager.get_all_sshkeys()
    keys = [key.id for key in keys]

    region = kwargs.get("region", digitalocean_region)
    size = kwargs.get("size", digitalocean_size)
    image = kwargs.get("image", digitalocean_image)


    droplet = Droplet(
        token=digitalocean_token,
        name=name,
        region=region,
        size=size,
        image=image,
        ssh_keys=keys,
    )

    droplet.create()

    while droplet.status != "active":
        droplet.load()
        print(f"Creating droplet {name} status: {droplet.status}")
        time.sleep(5)

    print(f"Droplet {name} created with ip: {droplet.ip_address}")

    return droplet.ip_address