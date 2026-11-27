"""Cho phép `import assistant...` khi chạy pytest từ thư mục repo gốc.

(Package `assistant` nằm trong src/ — thêm src/ vào sys.path.)
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
