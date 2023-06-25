from pathlib import Path
from tkinter import filedialog, Tk
from shutil import disk_usage, rmtree
from gettext import gettext as _
from gettext import ngettext as _N
from subprocess import run
from os import path
import sys
from platform import system
import tarfile
import os
import pyzstd
import json
import httpx
from tqdm import tqdm
import vars
import gui
import setup


class Game:
    downloads_data = None
    def __init__(self,name,data_dir,source_url):
        self.name = name
        self.data_dir = data_dir
        self.source_url = source_url
        self.install_dir = setup.sourcemods_path()
        self.latest_ver = -1



    def get_installed_version(self): # need to check it exists locally first.
        local_version_file = open(self.install_dir + '.adastral_ver', 'r')
        local_version = local_version_file.read().rstrip('\n')
        return local_version

    def is_installed(self): ## awful
        try:
            self.get_installed_version()
        except Exception:
            return False
        return True
    def update_version_file(self): # this needs to be updated to cover all games....
        """
        The previous launcher/updater leaves behind a rev.txt file with the old internal revision number.
        To avoid file bloat, we reuse this, but replace it with the game's semantic version number.
        To obtain the game's semantic version number, we do some horrible parsing of the game's version.txt
        file, which is what the game itself uses directly to show the version number on the main menu, etc.
        """
        try:
            old_version_file = open(self.install_dir + self.data_dir + 'version.txt', 'r')
            old_version = old_version_file.readlines()[1]
            before, sep, after = old_version.partition('=')
            if len(after) > 0:
                old_version = after
            old_version = old_version.replace('.', '')
            new_version_file = open(self.install_dir + self.data_dir + '.adastral_ver', 'w')
            # We unconditionally overwrite rev.txt since version.txt is the canonical file.
            new_version_file.write(old_version)
            new_version_file.close()
            old_version_file.close()
            return True
        except FileNotFoundError:
            if gui.message_yes_no(_("We can't read the version of your installation. It could be corrupted. Do you want to reinstall the game?"), False):
                return False
            else:
                gui.message_end(_("We have nothing to do. Goodbye!"), 0)

    def local_version_check(self):
        pass


class Kachemak(Game):
    installled = False
    aria2c_binary = None
    butler_binary = None
    install_path = None
    version_list=None

    def __init__(self, name, data_dir, source_url):
        super().__init__(name, data_dir, source_url)
        self.setup_binaries()

    def get_version_list(self):
        if self.version_list is None:
            try:
                version_remote = httpx.get(self.source_url + 'versions.json')
                self.version_list = json.loads(version_remote.text)
            except httpx.RequestError:
                gui.message_end(
                    _("Could not get version list. If your internet connection is fine, the servers could be having technical issues."),
                    1)
        return self.version_list


    def setup_binaries(self):
        """
        Select paths for required binaries.
        """
        if system() == 'Windows':
            # When we can detect that we're compiled using PyInstaller, we use their
            # suggested method of determining the location of the temporary runtime folder
            # to point to Aria2 and Butler.
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                self.aria2c_binary = path.abspath(path.join(path.dirname(__file__), 'aria2c.exe'))
                self.butler_binary = path.abspath(path.join(path.dirname(__file__), 'butler.exe'))
            else:
                # When running as a script, we just select the Binaries folder directly for Aria2 and Butler.
                self.aria2c_binary = 'Binaries/aria2c.exe'
                self.butler_binary = 'Binaries/butler.exe'
        else:
            # If we're running on Linux...
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                self.aria2c_binary = path.abspath(path.join(path.dirname(__file__), 'aria2c'))
                self.butler_binary = path.abspath(path.join(path.dirname(__file__), 'butler'))
            else:
                self.butler_binary = 'Binaries/butler'
                self.aria2c_binary = 'Binaries/aria2c'

    def download(self,url, size):
            self.free_space_check(size, 'temporary')
            run([self.aria2c_binary, '--max-connection-per-server=16', '-UAdastral-master', '--disable-ipv6=true', '--max-concurrent-downloads=16', '--optimize-concurrent-downloads=true', '--check-certificate=false', '--check-integrity=true', '--auto-file-renaming=false', '--continue=true', '--allow-overwrite=true', '--console-log-level=error', '--summary-interval=0', '--bt-hash-check-seed=false','--allow-piece-length-change=true', '--seed-time=0',
            '-d' + vars.TEMP_PATH, url], check=True)


    def extract(self,filename, endpath, size):
        self.free_space_check(size, 'permanent')

        gui.message(_("Extracting the downloaded archive, please wait patiently."), 1)
        class ZstdTarFile(tarfile.TarFile):
            def __init__(self, name, mode='r', *, level_or_option=None, zstd_dict=None, **kwargs):
                self.zstd_file = pyzstd.ZstdFile(name, mode,
                                        level_or_option=level_or_option,
                                        zstd_dict=zstd_dict)
                try:
                    super().__init__(fileobj=self.zstd_file, mode=mode, **kwargs)
                except:
                    self.zstd_file.close()
                    raise

            def close(self):
                try:
                    super().close()
                finally:
                    self.zstd_file.close()

        # read .tar.zst file (decompression)
        with ZstdTarFile(path.join(vars.TEMP_PATH, filename), mode='r') as tar:
            for member in tqdm(iterable=tar.getmembers(), total=len(tar.getmembers())):
                tar.extract(member=member, path=endpath)

    def butler_verify(self,signature, gamedir, remote):
        run([self.butler_binary, 'verify', signature, gamedir, '--heal=archive,' + remote], check=True)

    def butler_patch(self,url, staging_dir, patchfilename, gamedir):
        if Path(staging_dir).exists() and Path(staging_dir).is_dir():
            rmtree(staging_dir)
        run([self.aria2c_binary, '--max-connection-per-server=16', '-UAdastral-master',
             '--disable-ipv6=true',
             '--allow-piece-length-change=true', '--max-concurrent-downloads=16', '--optimize-concurrent-downloads=true', '--check-certificate=false', '--check-integrity=true', '--auto-file-renaming=false', '--continue=true', '--allow-overwrite=true', '--console-log-level=error', '--summary-interval=0', '--bt-hash-check-seed=false', '--seed-time=0',
        '-d' + vars.TEMP_PATH, url], check=True)
        gui.message(_("Patching your game with the new update, please wait patiently."), 1)
        run([self.butler_binary, 'apply', '--staging-dir=' + staging_dir, path.join(vars.TEMP_PATH, patchfilename), gamedir], check=True)
        if Path(staging_dir).exists() and Path(staging_dir).is_dir():
            rmtree(staging_dir)


    def pretty_size(self,bytes):
        if bytes < 100:
            return _N("%s byte", "%s bytes", bytes) % bytes
        if bytes < 1000000:
            return _("%.2f kB") % (bytes/1000)
        if bytes < 1000000000:
            return _("%.2f MB") % (bytes/1000000)
        if bytes < 1000000000000:
            return _("%.2f GB") % (bytes/1000000000)
        if bytes < 1000000000000000:
            return _("%.2f TB") % (bytes/1000000000000)
        if bytes < 1000000000000000000:
            return _("%.2f PB") % (bytes/1000000000000000)

    def free_space_check(self,size, cat):
        if cat == 'temporary':
            if disk_usage(vars.TEMP_PATH)[2] < size:
                if gui.message_yes_no(_("You don't have enough free space in your computer's default temporary folder for this. A minimum of %s is required. Select alternate temporary folder?") % pretty_size(size), 1):
                    root = Tk()
                    root.withdraw()
                    try:
                        while disk_usage(vars.TEMP_PATH)[2] < size:
                            vars.TEMP_PATH = filedialog.askdirectory()
                            if disk_usage(vars.TEMP_PATH)[2] < size:
                                gui.message(_("Still not enough space at specified path. Retry, and select a different drive if available."))
                    except TypeError:
                        gui.message_end(_("Folder selection prompt closed without choosing any path. Exiting..."), 1)


        if cat == 'permanent':
            if disk_usage(self.install_path)[2] < size and self.installled is False:
                gui.message_end(_("You don't have enough free space for the extraction. A minimum of %s at your chosen extraction site is required.") % pretty_size(size), 1)

    def prepare_symlink(self):
        for s in vars.TO_SYMLINK:
            if path.isfile(self.install_path + s[1]) and not path.islink(self.install_path + s[1]):
                os.remove(self.install_path + s[1])

    def do_symlink(self):
        if system() == "Windows":
            return

        for s in vars.TO_SYMLINK:
            if not path.isfile(self.install_path + self.data_dir + s[1]):
                os.symlink(self.install_path + s[0], self.install_path + self.data_dir + s[1])

    def install(self):
        version_json = self.get_version_list()["versions"]
        last_key = list(version_json.keys())[-1]
        lastver = version_json[last_key]

        self.prepare_symlink()

        gui.message(_("Getting the archive..."), 0)

        self.download(self.source_url + lastver["url"], lastver["presz"])

        if not path.isdir(self.install_path):
            gui.message_end(_("The specified extraction location does not exist."), 1)

        self.extract(lastver["file"], self.install_path, lastver["postsz"])

        self.do_symlink()


    def local_version_check(self):
        version_json = self.get_version_list()["versions"]
        found = False
        for ver in version_json:
            if ver == self.get_installed_version():
                found = True
                break
        return found

    def update(self):
        """
        The simplest part of all of this.
        We already know the user wants to update, can update, and the local version we get the patch from.
        So at this point, it's just downloading, healing, and applying.
        """

        self.prepare_symlink()

        # Prepare some variables
        local_version = self.get_installed_version()

        patch_json = self.get_version_list()["patches"]
        patch_url = patch_json[local_version]["url"]
        patch_file = patch_json[local_version]["file"]
        patch_tempreq = patch_json[local_version]["tempreq"]

        # Filesize check for butler-staging...
        # patch_tempreq is NOT the size of the patch, this is the size of the staging folder when commiting
        # Even though this is literally temporary, we say this is "permanent" since we want to check and use the same drive as the game
        self.free_space_check(patch_tempreq, 'permanent')

        version_json = self.get_version_list()["versions"]
        signature_url = version_json[self.get_installed_version()]["signature"]
        heal_url = version_json[self.get_installed_version()]["heal"]

        # Finally, verify and heal with the information we've gathered.
        self.butler_verify(self.source_url + signature_url, self.install_path + self.data_dir,
                       self.source_url + heal_url)
        self.butler_patch(self.source_url + patch_url, self.install_path + '/butler-staging',
                      patch_file, self.install_path + self.data_dir)

        self.do_symlink()

