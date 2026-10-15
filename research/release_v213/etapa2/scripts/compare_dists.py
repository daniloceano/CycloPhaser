"""Compare a local build of cyclophaser with the files published on an index.

    python -I compare_dists.py <local_dir> <index_dir>

Each directory holds one wheel and one sdist of the same version. Prints, for
every member of the wheel and of the sdist (sdist members keyed without their
top-level folder), whether the content is the same (SHA256), and the verdicts
the release criterion reads: package files cyclophaser/* identical, Requires-
Dist / Requires-Python identical, entries under tests/ in the sdist. Read-only.
"""
import hashlib
import sys
import tarfile
import zipfile
from pathlib import Path


def wheel_members(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def sdist_members(path):
    out = {}
    with tarfile.open(path) as t:
        for m in t.getmembers():
            if m.isfile():
                out[m.name.split("/", 1)[1]] = t.extractfile(m).read()
    return out


def meta_lines(blob, keys=("Requires-Dist:", "Requires-Python:", "Version:")):
    return [ln for ln in blob.decode().splitlines() if ln.startswith(keys)]


def compare(kind, a, b):
    print(f"== {kind}: {len(a)} local members, {len(b)} index members")
    for n in sorted(set(a) | set(b)):
        ha = hashlib.sha256(a[n]).hexdigest()[:16] if n in a else None
        hb = hashlib.sha256(b[n]).hexdigest()[:16] if n in b else None
        print(f"   {'SAME' if ha == hb else 'DIFF'}  {n}  {ha}  {hb}")
    pkg = sorted(n for n in set(a) | set(b) if n.startswith("cyclophaser/"))
    same = all(n in a and n in b and a[n] == b[n] for n in pkg)
    print(f"   package files cyclophaser/* identical: {same} ({len(pkg)} files)")
    return same


def main():
    local, index = Path(sys.argv[1]), Path(sys.argv[2])
    wl, wi = next(local.glob("*.whl")), next(index.glob("*.whl"))
    sl, si = next(local.glob("*.tar.gz")), next(index.glob("*.tar.gz"))
    a, b = wheel_members(wl), wheel_members(wi)
    w_ok = compare("wheel", a, b)
    ma = meta_lines(a[next(n for n in a if n.endswith("dist-info/METADATA"))])
    mb = meta_lines(b[next(n for n in b if n.endswith("dist-info/METADATA"))])
    print("   METADATA local:", ma)
    print("   METADATA index:", mb)
    print("   Requires-Dist/Requires-Python/Version identical:", ma == mb)
    sa, sb = sdist_members(sl), sdist_members(si)
    s_ok = compare("sdist", sa, sb)
    for n in ("setup.py", "MANIFEST.in", "README.md", "LICENSE"):
        print(f"   sdist {n} identical: {sa.get(n) == sb.get(n) and n in sa}")
    print("   sdist entries under tests/ (index):", [n for n in sb if n.startswith("tests/")])
    print("VERDICT wheel_pkg", w_ok, "sdist_pkg", s_ok, "metadata", ma == mb)


if __name__ == "__main__":
    main()
