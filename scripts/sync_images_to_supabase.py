"""Upload changed RESCENE photos to Supabase Storage and register new member photos."""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


MEMBERS = {
    "리브": ("LIV", "liv_images"),
    "메이": ("MEI", "mei_images"),
    "미나미": ("MINAMI", "minami_images"),
    "원이": ("WONI", "woni_images"),
    "제나": ("JENA", "jena_images"),
}


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required GitHub secret: {name}")
    return value.rstrip("/")


def request(url: str, method: str, headers: dict[str, str], body: bytes | None = None) -> bytes:
    request_object = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request_object) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed ({error.code}): {detail}") from error


def upload_file(supabase_url: str, service_key: str, bucket: str, file_path: Path) -> str:
    storage_path = file_path.as_posix()
    encoded_path = urllib.parse.quote(storage_path, safe="/")
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    request(
        f"{supabase_url}/storage/v1/object/{urllib.parse.quote(bucket, safe='')}/{encoded_path}",
        "POST",
        {
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        file_path.read_bytes(),
    )
    return f"{supabase_url}/storage/v1/object/public/{urllib.parse.quote(bucket, safe='')}/{encoded_path}"


def photo_already_registered(supabase_url: str, service_key: str, table: str, image_url: str) -> bool:
    params = urllib.parse.urlencode({"select": "id", "image_url": f"cs.{json.dumps([image_url])}"})
    result = request(
        f"{supabase_url}/rest/v1/{table}?{params}",
        "GET",
        {"Authorization": f"Bearer {service_key}", "apikey": service_key},
    )
    return bool(json.loads(result))


def register_photo(supabase_url: str, service_key: str, member_name: str, table: str, image_url: str) -> None:
    if photo_already_registered(supabase_url, service_key, table, image_url):
        print(f"Already registered: {image_url}")
        return

    request(
        f"{supabase_url}/rest/v1/{table}",
        "POST",
        {
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json.dumps({"member_name": member_name, "image_url": [image_url]}).encode("utf-8"),
    )
    print(f"Registered {member_name}: {image_url}")


def main() -> None:
    if len(sys.argv) != 2:
        raise RuntimeError("Usage: sync_images_to_supabase.py <changed-images.txt>")

    supabase_url = required_env("SUPABASE_URL")
    service_key = required_env("SUPABASE_SERVICE_ROLE_KEY")
    bucket = required_env("SUPABASE_STORAGE_BUCKET")

    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        status, relative_name = line.split("\t", maxsplit=1)
        file_path = Path(relative_name)
        if not file_path.is_file():
            continue

        image_url = upload_file(supabase_url, service_key, bucket, file_path)
        folder = file_path.parts[1] if len(file_path.parts) > 1 else ""
        member = MEMBERS.get(folder)

        if status == "A" and member:
            member_name, table = member
            register_photo(supabase_url, service_key, member_name, table, image_url)
        elif not member:
            print(f"Uploaded without database registration: {relative_name}")


if __name__ == "__main__":
    main()
