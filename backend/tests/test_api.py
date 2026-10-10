"""
backend/tests/test_api.py — Integration tests for all ZipForge REST API endpoints.
"""

from __future__ import annotations

import io
from starlette.testclient import TestClient
from PIL import Image

import main

client = TestClient(main.app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["app"] == "ZipForge"


def test_api_algorithms():
    res = client.get("/api/algorithms")
    assert res.status_code == 200
    data = res.json()
    assert "algorithms" in data
    algo_ids = [a["id"] for a in data["algorithms"]]
    assert "AUTO" in algo_ids
    assert "HUFFMAN" in algo_ids
    assert "LZW" in algo_ids
    assert "RLE" in algo_ids
    assert "STORE" in algo_ids


def test_api_compress_single_file_and_download():
    content = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50
    files = [("files", ("sample.txt", io.BytesIO(content), "text/plain"))]
    data = {
        "level": "RECOMMENDED",
        "archive_name": "test_bundle",
        "use_target_size": "false",
    }
    res = client.post("/api/compress", data=data, files=files)
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["total_input"] == len(content)
    assert json_data["total_compressed"] > 0
    assert json_data["is_single_file"] is True
    assert "job_id" in json_data
    job_id = json_data["job_id"]

    # Test downloading the zip archive
    dl_zip = client.get(f"/api/download/archive/{job_id}")
    assert dl_zip.status_code == 200
    assert len(dl_zip.content) == json_data["total_compressed"]

    # Test downloading the single file directly
    dl_file = client.get(f"/api/download/file/{job_id}/0")
    assert dl_file.status_code == 200
    assert len(dl_file.content) > 0


def test_api_compress_multi_file():
    f1 = b"AAAAABBBBBCCCCCDDDDD" * 40
    f2 = b"Hello ZipForge compression engine!" * 30
    files = [
        ("files", ("repeated.txt", io.BytesIO(f1), "text/plain")),
        ("files", ("greeting.txt", io.BytesIO(f2), "text/plain")),
    ]
    res = client.post("/api/compress", data={"level": "EXTREME"}, files=files)
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert len(json_data["files"]) == 2
    assert json_data["is_single_file"] is False


def test_api_decompress_preview_and_extract():
    # First compress some data into a zip
    content = b"Decompression verification test payload" * 20
    files = [("files", ("doc.txt", io.BytesIO(content), "text/plain"))]
    res_c = client.post("/api/compress", data={"archive_name": "to_extract"}, files=files)
    job_id = res_c.json()["job_id"]
    zip_bytes = client.get(f"/api/download/archive/{job_id}").content

    # Preview
    preview_res = client.post(
        "/api/decompress/preview",
        files={"archive": ("to_extract.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert preview_res.status_code == 200
    prev_data = preview_res.json()
    assert prev_data["success"] is True
    assert prev_data["entry_count"] >= 1

    # Extract
    extract_res = client.post(
        "/api/decompress/extract",
        files={"archive": ("to_extract.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert extract_res.status_code == 200
    ext_data = extract_res.json()
    assert ext_data["success"] is True
    assert len(ext_data["files"]) >= 1

    # Download extracted entry
    ext_job_id = ext_data["job_id"]
    dl_ext = client.get(f"/api/download/extracted/{ext_job_id}/0")
    assert dl_ext.status_code == 200
    assert dl_ext.content == content


def test_api_image_optimize_profile():
    img = Image.new("RGB", (64, 64), color=(255, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    raw_img = buf.getvalue()

    res = client.post(
        "/api/image/optimize",
        data={"mode": "profile", "profile_name": "RECOMMENDED", "output_format": "JPEG"},
        files={"file": ("photo.jpg", io.BytesIO(raw_img), "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["final_size"] > 0
    assert "optimized_preview" in data
    assert data["output_format"] == "JPEG"

    # Download optimized image
    dl = client.get(f"/api/download/image/{data['job_id']}")
    assert dl.status_code == 200
    assert len(dl.content) == data["final_size"]


def test_api_benchmark():
    content = b"Benchmark testing payload with mixed repetitive text ABCD " * 50
    res = client.post(
        "/api/benchmark",
        files={"file": ("bench.txt", io.BytesIO(content), "text/plain")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["results"]) == 4
    algos = [r["algorithm"] for r in data["results"]]
    assert "HUFFMAN" in algos
    assert "LZW" in algos
    assert "RLE" in algos
    assert "STORE" in algos


def test_api_inspect():
    content = b"Inspection testing payload" * 15
    files = [("files", ("file.txt", io.BytesIO(content), "text/plain"))]
    res_c = client.post("/api/compress", files=files)
    job_id = res_c.json()["job_id"]
    zip_bytes = client.get(f"/api/download/archive/{job_id}").content

    res = client.post(
        "/api/inspect",
        files={"archive": ("archive.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["entry_count"] >= 1
