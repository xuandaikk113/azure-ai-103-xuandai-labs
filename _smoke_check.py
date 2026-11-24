"""
Smoke-check: nghiệm thu nhanh bộ lab mà KHÔNG gọi Azure (không tốn tiền, không cần mạng).
- Biên dịch (py_compile) mọi file NN_*.py trong các thư mục lab -> bắt lỗi cú pháp.
- Đối chiếu key trong .env.example với .env -> liệt kê biến còn thiếu.

Chạy       : uv run _smoke_check.py
Self-test  : uv run _smoke_check.py --self-test
"""
import py_compile
import sys
from pathlib import Path

# Windows: console mặc định dùng cp1252, không in được tiếng Việt -> ép stdout sang UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent


def find_lab_files() -> list:
    """Các thư mục lab bắt đầu bằng 2 chữ số; trong đó lấy file NN_*.py."""
    return sorted(
        p
        for d in ROOT.glob("[0-9][0-9]_*")
        if d.is_dir()
        for p in d.glob("[0-9][0-9]_*.py")
    )


def check_compile(files: list) -> list:
    """Trả về danh sách (file, lỗi) cho những file không biên dịch được."""
    errors = []
    for f in files:
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append((f, str(e)))
    return errors


def parse_env_keys(path: Path) -> list:
    """Lấy danh sách KEY (trước dấu =) từ file .env, bỏ qua comment và dòng trống."""
    if not path.exists():
        return []
    keys = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.append(line.split("=", 1)[0].strip())
    return keys


def check_env() -> list:
    """Những key có trong .env.example nhưng chưa có trong .env."""
    example = parse_env_keys(ROOT / ".env.example")
    actual = set(parse_env_keys(ROOT / ".env"))
    return [k for k in example if k not in actual]


def main() -> int:
    files = find_lab_files()
    print(f"Tìm thấy {len(files)} file lab.")

    errors = check_compile(files)
    if errors:
        print(f"\n[CÚ PHÁP] {len(errors)} file lỗi:")
        for f, e in errors:
            print(f"  - {f.relative_to(ROOT)}: {e}")
    else:
        print("[CÚ PHÁP] Tất cả file biên dịch OK.")

    missing = check_env()
    if missing:
        print(f"\n[.env] Thiếu {len(missing)} biến (so với .env.example): " + ", ".join(missing))
    else:
        print("[.env] Đủ biến, hoặc chưa tạo .env.")

    return 1 if errors else 0


def _self_test() -> None:
    """Kiểm tra parse_env_keys đọc đúng key và bỏ comment/dòng trống."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False, encoding="utf-8") as tf:
        tf.write("# comment\nFOO=bar\n\nBAZ=1\n")
        name = tf.name
    try:
        assert parse_env_keys(Path(name)) == ["FOO", "BAZ"]
    finally:
        os.unlink(name)
    print("self-test OK")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _self_test()
    else:
        sys.exit(main())
