import shutil
import dockerfactory.packages
import dockerfactory.images
import subprocess
import os
from glob import glob

def build_base_image():
    tmp_path = "/tmp/dockerfactory-baseimage"

    print(":: Generating base image")
    subprocess.check_output(["rm", "-rf", tmp_path])

    print("   -> Generating rootfs")
    subprocess.check_output(["cdebootstrap", "jessie", tmp_path, "http://ftp.fr.debian.org/debian"], stderr=subprocess.STDOUT)

    if not os.path.exists(os.path.join(tmp_path, "etc/dpkg/dpkg.cfg.d")):
        os.mkdir(os.path.join(tmp_path, "etc/dpkg/dpkg.cfg.d"))
    with open(os.path.join(tmp_path, "etc/dpkg/dpkg.cfg.d/01_exclude_stuff"), "w") as dpkg_config:
        dpkg_config.write("path-exclude=/usr/share/man/*\n")
        dpkg_config.write("path-exclude=/usr/share/doc/*\n")
        dpkg_config.write("path-exclude=/usr/share/info/*\n")

        dpkg_config.write("path-exclude=/usr/share/locale/*\n")
        dpkg_config.write("path-include=/usr/share/locale/en\n")
        dpkg_config.write("path-include=/usr/share/locale/en_US\n")
        dpkg_config.write("path-include=/usr/share/locale/de\n")

        dpkg_config.write("path-exclude=/usr/share/i18n/locales/*\n")
        dpkg_config.write("path-include=/usr/share/i18n/locales/en_US\n")
        dpkg_config.write("path-include=/usr/share/i18n/locales/de_DE\n")
        dpkg_config.write("path-include=/usr/share/i18n/locales/de_DE@euro\n")

    open(os.path.join(tmp_path, "etc/apt/apt.conf.d/02no-recommends"), "w").write('APT::Install-Recommends "0" ; APT::Install-Suggests "0" ;')

    open(os.path.join(tmp_path, "usr/sbin/policy-rc.d"), "w").write("#!/bin/bash\nexit 101")
    os.chmod(os.path.join(tmp_path, "usr/sbin/policy-rc.d"), 0o755)

    print("   -> Applying additional updates")
    with open(os.path.join(tmp_path, "etc/apt/sources.list"), "w") as sources_list:
        sources_list.write("deb http://ftp.fr.debian.org/debian/ jessie main\n")
        sources_list.write("deb http://ftp.fr.debian.org/debian/ jessie-updates main\n")
        sources_list.write("deb http://security.debian.org/ jessie/updates main\n")
    subprocess.check_output(["chroot", tmp_path, "/bin/bash", "-c", "apt-get -qq update; apt-get -yqq dist-upgrade; apt-get -yqq install supervisor rsync git openssh-client build-essential htop psmisc; rm -rf /run/*"], stderr=subprocess.STDOUT)

    dockerfactory.images.image_fs_cleanup(tmp_path)

    print("   -> Creating docker image")
    tar_cmd = subprocess.Popen(["tar", "c", "-C", tmp_path, "-c", "."], stdout=subprocess.PIPE)
    new_image = subprocess.check_output(["docker", "import", "-"], stdin=tar_cmd.stdout).strip()

    print("   -> Tagging image")
    dockerfactory.images.tag_image(new_image, 'debian')

    print("   -> Pushing image")
    dockerfactory.images.push_image('debian')

    print("   -> Done!")
    return new_image

