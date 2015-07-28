import subprocess
import os
import stat
import shutil
from glob import glob

def tag_image(image, tag):
    if type(image) == bytes:
        image = image.decode("ascii")

    if type(tag) == bytes:
        tag = tag.decode("ascii")

    subprocess.check_output(["docker", "tag", "-f", image, "registry.kurz.pw:443/%s" % tag])

def push_image(image):
    if type(image) == bytes:
        image = image.decode("ascii")

    subprocess.check_output(["docker", "push", "registry.kurz.pw:443/%s" % image])

def commit_container(container):
    new_image = subprocess.check_output(["docker", "commit", container]).strip()
    subprocess.check_output(["docker", "rm", container])

    return new_image

def image_fs_cleanup(path):
    for remove in ['usr/share/doc', 'usr/share/man', 'usr/share/info', 'usr/share/zoneinfo', 'var/cache/apt', 'var/lib/apt/lists']:
        if os.path.exists("%s/%s" % (path, remove)):
            shutil.rmtree("%s/%s" % (path, remove))

    for locale in glob("%s/usr/share/locale/*" % path):
        if not os.path.basename(locale) in ['en', 'en_US', 'de']:
            shutil.rmtree(locale)

    for locale in glob("%s/usr/share/i18n/locales/*" % path):
        if not os.path.basename(locale) in ['en', 'en_US', 'de']:
            shutil.rmtree(locale)

def install_packages(image, packages):
    temp_container = subprocess.check_output(["docker", "create", "--entrypoint=/start.sh", image]).strip()

    installer_file = "/var/lib/docker/btrfs/subvolumes/%s/start.sh" % (temp_container.decode('ascii'))
    with open(installer_file, "w") as installer:
        os.chmod(installer_file, 0o755)
        installer.write("#!/bin/bash\n")
        installer.write("set -e\n")
        installer.write("apt-get -qq update\n")
        installer.write("apt-get -yqq install %s\n" % ' '.join(list(x.decode('ascii') if type(x) == bytes else x for x in packages)))
        installer.write("rm /start.sh\n")
        installer.write("exit 0\n")

    subprocess.check_output(["docker", "start", "-a", temp_container], stderr=subprocess.STDOUT)
    image_fs_cleanup("/var/lib/docker/btrfs/subvolumes/%s" % temp_container.decode('ascii'))

    return commit_container(temp_container)

def add_files(image, files):
    temp_container = subprocess.check_output(["docker", "create", "--entrypoint=/start.sh", image]).strip()
    base_path = "/var/lib/docker/btrfs/subvolumes/%s" % (temp_container.decode('ascii'))

    for path in files:
        src = path['src']
        dst = os.path.join(base_path, path['dst'])
        dstdir = os.path.dirname(dst)

        if not os.path.exists(dstdir):
            os.makedirs(dstdir)

        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    return commit_container(temp_container)

def exists(image):
    return get_image_date(image) > 0

def get_image_date(image):
    if type(image) == bytes:
        image = image.decode('ascii')

    if len(image) == 64 and os.path.exists("/var/lib/docker/btrfs/subvolumes/%s" % image):
        return int(os.path.getmtime("/var/lib/docker/btrfs/subvolumes/%s" % image))
    else:
        try:
            image = subprocess.check_output(["docker", "inspect", "-f", "{{ .Id }}", image], stderr=subprocess.DEVNULL).strip()
            return get_image_date(image)
        except:
            return 0

