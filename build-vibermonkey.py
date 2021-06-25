from pathlib import Path
import urllib.request
import os
import zipfile
import shutil
import subprocess
from textwrap import dedent

thisdir = Path(globals().get("__file__", "./_")).absolute().parent
tmp = thisdir.joinpath("temp")

pypyurl = "https://downloads.python.org/pypy/pypy2.7-v7.3.5-win64.zip"
vipermonkeyurl = "https://github.com/decalage2/ViperMonkey/archive/master.zip"
szipurl = "https://www.7-zip.org/a/7z1900-x64.msi"

pypydir = thisdir.joinpath("build/bin/pypy2.7")
vipermonkeydir = thisdir.joinpath("build/bin/ViperMonkey")
szipdir = thisdir.joinpath("build/bin", "7z")

pypyexe = pypydir.joinpath("pypy.exe")
szipexe = szipdir.joinpath("7z.exe")


def get_filename(url):
    return tmp.joinpath(Path(url).name)


def dl_file(url):
    zip = get_filename(url)
    os.makedirs(zip.parent, exist_ok=True)
    if not zip.is_file():
        urllib.request.urlretrieve(url, zip)


for url in (pypyurl, vipermonkeyurl, szipurl):
    print(f"Downloading {url}")
    dl_file(url)


if not pypydir.joinpath("pypy.exe").is_file():
    with zipfile.ZipFile(get_filename(pypyurl), "r") as zip_ref:
        shutil.rmtree(pypydir, ignore_errors=True)

        zip_ref.extractall(pypydir.parent)
        for i in pypydir.parent.glob("pypy2.7*"):
            shutil.move(i, pypydir)


if not vipermonkeydir.joinpath("requirements.txt").is_file():
    with zipfile.ZipFile(get_filename(vipermonkeyurl), "r") as zip_ref:
        shutil.rmtree(vipermonkeydir, ignore_errors=True)

        zip_ref.extractall(vipermonkeydir.parent)
        for i in pypydir.parent.glob("ViperMonkey*"):
            shutil.move(i, vipermonkeydir)
    

if not szipexe.is_file():
    sztmp = szipdir.joinpath("tmp")
    os.makedirs(sztmp, exist_ok=True)
    subprocess.call(['msiexec', '/a', str(get_filename(szipurl).resolve()), '/qb', f"TARGETDIR={sztmp}"])

    for i in list(sztmp.rglob("7z.exe"))+list(sztmp.rglob("7z.dll")):
        shutil.move(i, szipdir.joinpath(i.name))
    shutil.rmtree(sztmp)

subprocess.call([pypyexe, "-m", "ensurepip"])
subprocess.call([pypyexe, "-m", "pip", "install", "-U", "-r", str(vipermonkeydir.joinpath("requirements.txt")), "--no-warn-script-location"])
subprocess.call([pypyexe, "-m", "pip", "install", "colorlog<5"])

for i in vipermonkeydir.joinpath("vipermonkey").glob("*.py"):
    print(i)
    if i.name in ("api.py", "__init__.py"):
        continue

    irel = i.relative_to(thisdir.joinpath("build"))
    cmdname = thisdir.joinpath("build", i.name[:-3]+".cmd")
    with open(cmdname, "w") as fw:
        fw.write(dedent(f"""
            @call "%~dp0\\bin\\pypy2.7\\pypy.exe" "{irel}" %*
            @exit /b %errorlevel%
            """)
        )

