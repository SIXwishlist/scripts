"""Installs arkOS over the top of an existing Arch Linux or ALARM system."""
from __future__ import print_function

import os
import subprocess
import shutil
import sys
import time
import textwrap
try:
    # Python 3
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from urllib import urlopen
try:
    # Python 3
    termSize = shutil.get_terminal_size((80, 20))
except NameError:
    # Python 2
    termSize = (80, 20)


class bcolors:
    """ANSI terminal styling."""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def askPermission():
    """Ask the user if they are sure they want to proceed."""
    print(bcolors.BOLD + bcolors.OKBLUE + "=== arkOS ===" + bcolors.ENDC)
    print("Arch-to-arkOS Conversion Script")
    print()
    msg = ("Using this script will convert your Arch Linux installation"
           " to a fully-functional arkOS server. It will irreversibly alter"
           " the software configurations on your machine. You should make no"
           " assumptions about your ability to manually configure your server"
           " after this script has successfully completed, except by using"
           " the tools and methods included in arkOS.")
    for x in textwrap.wrap(bcolors.WARNING + msg + bcolors.ENDC, termSize[0]):
        print(x)
    print()
    print("If you do NOT want this to occur, press Ctrl+C now.")
    try:
        for i in range(10, 0, -1):
            sys.stdout.write("\rInstalling in {0}...".format(i))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.exit(1)


def install():
    """Install arkOS."""
    print("Installing new packages...")
    subprocess.call(["pacman-key", "--init"])
    code = subprocess.call(["pacman-key", "-r", "0585F850"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to retrieve package signing key. Please retry." +
            bcolors.ENDC)
        sys.exit(1)
    code = subprocess.call(["pacman-key", "--lsign", "0585F850"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to install and trust package signing key. Please retry." +
            bcolors.ENDC)
        sys.exit(1)

    # Install key
    code = subprocess.call(["pacman", "-Su", "--noconfirm"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to update system packages. Please retry." +
            bcolors.ENDC)
        sys.exit(1)

    # Install new mirrorlist
    code = subprocess.call(["pacman", "-Q", "arkos-mirrorlist"])
    if code != 0:
        m = "https://pkg.arkos.io/resources/arkos-mirrorlist-latest.pkg.tar.xz"
        data = urlopen(m)
        with open("/tmp/arkos-mirrorlist.pkg.tar.xz", "wb") as f:
            f.write(data.read())
        install_cmd = ["pacman", "-U", "/tmp/arkos-mirrorlist.pkg.tar.xz",
                       "--noconfirm", "--needed"]
        code = subprocess.call(install_cmd)
        if code != 0:
            print(
                bcolors.FAIL +
                "Failed to install arkOS mirrorlist. Please retry." +
                bcolors.ENDC)
            sys.exit(1)

    isRepoInstalled = False
    with open("/etc/pacman.conf", "r") as f:
        if "[arkos]" in f.read():
            isRepoInstalled = True
    if not isRepoInstalled:
        with open("/etc/pacman.conf", "a") as f:
            f.write("\n[arkos]\nInclude = /etc/pacman.d/arkos-mirrorlist")
    subprocess.call(["pacman", "-Sy"])

    # Install new requirements
    required = ["arkos-core", "arkos-kraken", "arkos-genesis",
                "python-pip", "python2-pip"]
    code = subprocess.call(["pacman", "-Su", "--noconfirm"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to update system packages. Please retry." +
            bcolors.ENDC)
        sys.exit(1)
    subprocess.call(["pacman-db-upgrade"])
    install_cmd = ["pacman", "-Sy"] + required + ["--noconfirm", "--needed"]
    code = subprocess.call(install_cmd)
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to install new requirements. Please retry." +
            bcolors.ENDC)
        sys.exit(1)
    subprocess.call(["pacman-key", "--populate", "arkos"])

    # Configure system
    code = subprocess.call(["arkosctl", "init", "ldap"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to configure system. Please retry "
            "`sudo arkosctl init ldap`." + bcolors.ENDC)
    code = subprocess.call(["arkosctl", "init", "nslcd"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to configure system. Please retry "
            "`sudo arkosctl init nslcd`." + bcolors.ENDC)
    code = subprocess.call(["arkosctl", "init", "nginx"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to configure system. Please retry "
            "`sudo arkosctl init nginx`." + bcolors.ENDC)
    code = subprocess.call(["arkosctl", "init", "redis"])
    if code != 0:
        print(
            bcolors.FAIL +
            "Failed to configure system. Please retry "
            "`sudo arkosctl init redis`." + bcolors.ENDC)


if __name__ == '__main__':
    if os.geteuid() != 0:
        print(
            bcolors.FAIL +
            "You must run this script as root, or prefixed with `sudo`." +
            bcolors.ENDC)
        sys.exit(1)
    askPermission()
    try:
        install()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print("Installation cancelled.")
        sys.stdout.write("\n")
        sys.exit(1)
    subprocess.call(["systemctl", "enable", "avahi-daemon", "ntpd", "cronie",
                     "krakend"])
    print()
    print(bcolors.OKGREEN + "Installation completed successfully. "
          "Please restart your computer." + bcolors.ENDC)
