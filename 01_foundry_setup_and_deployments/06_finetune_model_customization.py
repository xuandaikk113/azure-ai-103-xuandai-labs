"""
====================================================================
LAB 01/06 · Fine-tuning (model customization)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI fine-tuning (+ ARM để deploy model đã fine-tune)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION,
               AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AOAI_ACCOUNT_NAME
SDK tiền nhiệm: fine-tune qua REST/portal.
Chạy         : uv run 01_foundry_setup_and_deployments/06_finetune_model_customization.py
Lưu ý        : job fine-tune chạy rất lâu (hàng giờ). File minh hoạ đủ các bước, poll có giới hạn.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import time                     # chờ giữa các lần poll trạng thái job

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── SDK ─────────────────────────────────────────────────────────
from openai import AzureOpenAI   # fine_tuning.jobs nằm trong client AzureOpenAI


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def main() -> None:
    cfg = require_env("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_VERSION")

    client = AzureOpenAI(
        azure_endpoint=cfg["AZURE_OPENAI_ENDPOINT"],
        api_key=cfg["AZURE_OPENAI_API_KEY"],
        api_version=cfg["AZURE_OPENAI_API_VERSION"],
    )

    # 1) Upload file train (JSONL: mỗi dòng 1 ví dụ hội thoại {"messages":[...]})
    #    Đặt file mẫu ở assets/finetune_train.jsonl
    train_path = os.path.join("assets", "finetune_train.jsonl")
    if not os.path.exists(train_path):
        sys.exit(f"[THIẾU DỮ LIỆU] Tạo file train JSONL tại: {train_path}")
    train_file = client.files.create(file=open(train_path, "rb"), purpose="fine-tune")
    print(f"Đã upload train file: {train_file.id}")

    # 2) Tạo fine-tuning job (model gốc hỗ trợ fine-tune, vd gpt-4o-mini)
    job = client.fine_tuning.jobs.create(
        training_file=train_file.id,
        model="gpt-4o-mini-2024-07-18",   # base model cho fine-tune
    )
    print(f"Đã tạo job: {job.id} (status={job.status})")

    # 3) Poll trạng thái (giới hạn vài vòng để minh hoạ — thực tế có thể vài giờ)
    for _ in range(3):
        time.sleep(10)
        job = client.fine_tuning.jobs.retrieve(job.id)
        print(f"  status={job.status}")
        if job.status in ("succeeded", "failed", "cancelled"):
            break

    # 4) Khi 'succeeded', job.fine_tuned_model là tên model mới -> deploy qua ARM
    #    (azure-mgmt-cognitiveservices, giống lab 01/02 nhưng model.name = job.fine_tuned_model)
    print("\nKhi succeeded: deploy job.fine_tuned_model qua azure-mgmt-cognitiveservices (xem lab 01/02).")
    print("Nhớ: fine-tuned model có chi phí HOSTING riêng theo giờ.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
