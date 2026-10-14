"""Inspect a cyclophaser wheel and sdist for criterion (c) of release 2.1.3.

    python -I inspect_dists.py <wheel_direct> <sdist> <wheel_from_sdist>

Prints the wheel's Requires-Dist / Requires-Python and whether LICENSE is in it,
every sdist entry under tests/, and compares the package files (cyclophaser/...)
of the direct wheel and of the wheel built from the sdist by SHA256 of content.
Read-only on its inputs.
"""
import hashlib
import sys
import tarfile
import zipfile


def wheel_files(path):
    with zipfile.ZipFile(path) as z:
        return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}


def metadata(path):
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
        return z.read(name).decode()


def main():
    whl, sdist, whl2 = sys.argv[1:4]
    meta = metadata(whl).splitlines()
    print("== wheel:", whl)
    for ln in meta:
        if ln.startswith(("Name:", "Version:", "Requires-Python:", "Requires-Dist:",
                          "Provides-Extra:", "License-File:")):
            print("  ", ln)
    files = wheel_files(whl)
    print("   files:", sorted(files))
    print("   LICENSE present:", any(n.endswith("/LICENSE") or n == "LICENSE" for n in files))

    with tarfile.open(sdist) as t:
        names = t.getnames()
    root = names[0].split("/")[0]
    tests = [n for n in names if n.startswith(f"{root}/tests/") or n == f"{root}/tests"]
    print("== sdist:", sdist, "entries:", len(names))
    for n in sorted(names):
        print("   ", n)
    print("   entries under tests/:", len(tests), tests)

    files2 = wheel_files(whl2)
    pk1 = {n: h for n, h in files.items() if n.startswith("cyclophaser/")}
    pk2 = {n: h for n, h in files2.items() if n.startswith("cyclophaser/")}
    print("== package files, direct wheel vs wheel from sdist")
    for n in sorted(set(pk1) | set(pk2)):
        print("   ", n, pk1.get(n), pk2.get(n), "SAME" if pk1.get(n) == pk2.get(n) else "DIFF")
    print("   identical by content:", pk1 == pk2, f"({len(pk1)} files)")
    print("   METADATA identical:", metadata(whl) == metadata(whl2))


if __name__ == "__main__":
    main()
