#!/usr/bin/env python3
"""
GCS Image Uploader — bkk2025-public
=====================================
事前に一度だけ実行するセットアップスクリプト。

    pip install google-cloud-storage
    python3 upload_to_gcs.py

やること:
  1. GCS バケット bkk2025-public-images を作成（存在すればスキップ）
  2. allUsers に閲覧権限を付与（公開バケット化）
  3. images/ フォルダの全 JPEG を gs://bkk2025-public-images/images/ にアップロード
  4. metadata.csv もアップロード（任意）

完了後の公開URL例:
  https://storage.googleapis.com/bkk2025-public-images/images/IMG_2835.jpeg
"""

import os
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 設定
# ──────────────────────────────────────────────────────────────────────────────
KEY_FILE    = Path(__file__).parent.parent / "ocr-th-486203-7f6e7c45dedb.json"
PROJECT_ID  = "ocr-th-486203"
BUCKET_NAME = "bkk2025-public-images"
LOCATION    = "asia-east1"   # 東アジア (台湾) — 近い方が速い
IMAGES_DIR  = Path(__file__).parent / "images"
CSV_FILE    = Path(__file__).parent / "metadata.csv"
# ──────────────────────────────────────────────────────────────────────────────


def main():
    try:
        from google.cloud import storage
    except ImportError:
        print("❌  google-cloud-storage が必要です:")
        print("    pip install google-cloud-storage")
        sys.exit(1)

    print(f"🔑  サービスアカウント: {KEY_FILE}")
    print(f"📦  バケット: gs://{BUCKET_NAME}\n")

    client = storage.Client.from_service_account_json(str(KEY_FILE), project=PROJECT_ID)

    # ── 1. バケット作成 ────────────────────────────────────────────────────────
    try:
        bucket = client.get_bucket(BUCKET_NAME)
        print(f"✅  バケット既存: gs://{BUCKET_NAME}")
    except Exception:
        print(f"🆕  バケットを作成中: gs://{BUCKET_NAME} ({LOCATION})")
        bucket = client.create_bucket(BUCKET_NAME, location=LOCATION)
        print(f"✅  バケット作成完了")

    # ── 2. 公開アクセス (allUsers objectViewer) ────────────────────────────────
    try:
        # uniformBucketLevelAccess が有効な場合は IAM ポリシーで設定
        policy = bucket.get_iam_policy(requested_policy_version=3)
        members = set()
        for b in policy.bindings:
            if b["role"] == "roles/storage.objectViewer":
                members = b.get("members", set())
                break
        if "allUsers" not in members:
            policy.bindings.append({
                "role": "roles/storage.objectViewer",
                "members": {"allUsers"},
            })
            bucket.set_iam_policy(policy)
            print("✅  公開アクセス設定完了 (allUsers objectViewer)")
        else:
            print("✅  公開アクセス設定済み")
    except Exception as e:
        print(f"⚠️   公開アクセス設定失敗（手動でコンソールから設定してください）: {e}")

    # ── 3. 画像アップロード ────────────────────────────────────────────────────
    image_files = sorted(IMAGES_DIR.glob("*.jpeg")) + sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.png"))
    print(f"\n📤  {len(image_files)} 枚の画像をアップロード中...")

    for i, img_path in enumerate(image_files, 1):
        dest = f"images/{img_path.name}"
        blob = bucket.blob(dest)
        blob.upload_from_filename(str(img_path), content_type="image/jpeg")
        print(f"  [{i:2d}/{len(image_files)}] {img_path.name}")

    print(f"✅  画像アップロード完了")

    # ── 4. metadata.csv アップロード（任意） ───────────────────────────────────
    if CSV_FILE.exists():
        blob = bucket.blob("metadata.csv")
        blob.upload_from_filename(str(CSV_FILE), content_type="text/csv")
        print(f"✅  metadata.csv アップロード完了")

    # ── 完了メッセージ ─────────────────────────────────────────────────────────
    base_url = f"https://storage.googleapis.com/{BUCKET_NAME}"
    print(f"""
╔══════════════════════════════════════════════════════╗
║  アップロード完了！                                  ║
╠══════════════════════════════════════════════════════╣
║  ベースURL:                                          ║
║  {base_url:<52}║
║                                                      ║
║  画像URL例:                                          ║
║  {base_url}/images/IMG_2835.jpeg
╚══════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
