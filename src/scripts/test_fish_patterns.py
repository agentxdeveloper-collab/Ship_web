import os, sys, importlib.util
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))  # points to src
RC_PATH = os.path.join(SRC_ROOT, 'services', 'reservation_checker.py')

def _load_rc():
    if SRC_ROOT not in sys.path:
        sys.path.insert(0, SRC_ROOT)
    try:
        from services.reservation_checker import check_single_boat  # type: ignore
        return check_single_boat
    except Exception:
        spec = importlib.util.spec_from_file_location('reservation_checker', RC_PATH)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return getattr(mod, 'check_single_boat')

check_single_boat = _load_rc()

TESTS = [
    ("https://teammansu.kr/index.php?mid=bk", 2025, 11, 22),
    ("http://www.kumkangho.co.kr/index.php?mid=bk", 2025, 11, 22),
    ("http://seasidefishing.kr/index.php?mid=bk", 2025, 11, 22),
]

if __name__ == "__main__":
    for base, y, m, d in TESTS:
        print("==== TEST:", base)
        res = check_single_boat(base, y, m, d, debug_enabled=True)
        entries = res.get("entries", [])
        print("entries:", len(entries), "error:", res.get("error"), "used_url:", res.get("used_url") or res.get("source_url"))
        # show first 5 entries fish info
        for e in entries[:5]:
            print({
                "ship_name": e.get("ship_name"),
                "fish": e.get("fish"),
                "status": e.get("status"),
                "available": e.get("available"),
            })
        print()
