#!/usr/bin/env

import subprocess
import lzma, gzip, bz2
import urllib.request
import apt

def parse_packages_file(packages_file_content, packages = {}, state = None):
    package = None
    version = None
    status = None

    for line in packages_file_content.split(b"\n"):
        line = line.strip()

        if line.startswith(b'Package: '):
            package = line.split(None,1)[1]

        elif line.startswith(b'Version: '):
            version = line.split(None,1)[1]

        elif line.startswith(b'Status: '):
            status = line.split(None,1)[1]

        elif line == b'' and package and version and (not state or status):
            if state and (not status or not state in status):
                continue

            if package in packages:
                if apt.apt_pkg.version_compare(packages[package], version) < 0:
                    packages[package] = version
            else:
                packages[package] = version

            package = None
            version = None
            status = None

    return packages

def get_repo_pkg_versions():
    packages_file_urls = [
            "http://ftp.fr.debian.org/debian/dists/jessie/main/binary-amd64/Packages.xz",
            "http://ftp.fr.debian.org/debian/dists/jessie-updates/main/binary-amd64/Packages.bz2",
            "http://security.debian.org/dists/jessie/updates/main/binary-amd64/Packages.bz2",
    ]

    packages = {}

    for packages_file_url in packages_file_urls:
        packages_file_compressed = urllib.request.urlopen(packages_file_url)

        if packages_file_url.endswith('.xz'):
            packages_file = lzma.open(packages_file_compressed)
            packages_file_content = packages_file.read()
        elif packages_file_url.endswith('.gz'):
            packages_file_content = gzip.decompress(packages_file_compressed.read())
        elif packages_file_url.endswith('.bz2'):
            packages_file_content = bz2.decompress(packages_file_compressed.read())
        else:
            print("unknown compression format for packages file")
            sys.exit(1)

        parse_packages_file(packages_file_content, packages)

    return packages

def get_pkg_versions(image):
    if type(image) == bytes:
        image = image.decode('ascii')

    packages_file_content = open("/var/lib/docker/btrfs/subvolumes/%s/var/lib/dpkg/status" % image, "rb").read()
    packages = parse_packages_file(packages_file_content, state=b'installed')

    return packages

def check_for_updates(packages, repo_packages):
    updates = []

    for package in packages:
        if not packages[package] == repo_packages[package]:
            updates.append((package, packages[package], repo_packages[package]))

    return updates

def contains_all_packages(installed_packages, required_packages):
    for package in required_packages:
        if not type(package) == bytes:
            package = package.encode('ascii')

        if not package in installed_packages:
            return False

    return True
