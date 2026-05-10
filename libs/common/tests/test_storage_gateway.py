"""
Storage Gateway Tests
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from ..gateways.storage import (
    get_storage_gateway,
    LocalStorageProvider,
)


@pytest.fixture
def temp_storage_dir():
    """임시 저장소 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_local_storage_upload_download(temp_storage_dir):
    """로컬 스토리지 업로드/다운로드 테스트"""
    storage = get_storage_gateway(
        provider="local",
        base_path=temp_storage_dir,
    )

    assert isinstance(storage, LocalStorageProvider)
    assert storage.provider_name == "local"

    # 업로드
    content = b"Test content"
    uri = await storage.upload("test/file.txt", content)

    assert uri.startswith("file://")

    # 다운로드
    downloaded = await storage.download("test/file.txt")
    assert downloaded == content


@pytest.mark.asyncio
async def test_local_storage_exists(temp_storage_dir):
    """파일 존재 확인 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    # 존재하지 않음
    exists = await storage.exists("nonexistent.txt")
    assert not exists

    # 업로드 후 존재
    await storage.upload("existing.txt", b"content")
    exists = await storage.exists("existing.txt")
    assert exists


@pytest.mark.asyncio
async def test_local_storage_delete(temp_storage_dir):
    """파일 삭제 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    # 업로드
    await storage.upload("deleteme.txt", b"content")
    assert await storage.exists("deleteme.txt")

    # 삭제
    success = await storage.delete("deleteme.txt")
    assert success
    assert not await storage.exists("deleteme.txt")

    # 존재하지 않는 파일 삭제
    success = await storage.delete("nonexistent.txt")
    assert not success


@pytest.mark.asyncio
async def test_local_storage_list(temp_storage_dir):
    """파일 목록 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    # 여러 파일 업로드
    await storage.upload("dir1/file1.txt", b"content1")
    await storage.upload("dir1/file2.txt", b"content2")
    await storage.upload("dir2/file3.txt", b"content3")

    # 전체 목록
    all_files = await storage.list()
    assert len(all_files) == 3

    # Prefix 필터링
    dir1_files = await storage.list("dir1")
    assert len(dir1_files) >= 2


@pytest.mark.asyncio
async def test_local_storage_metadata(temp_storage_dir):
    """메타데이터 저장 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    metadata = {
        "experiment_id": "exp-001",
        "created_by": "user-123",
    }

    await storage.upload(
        "test/metadata.txt",
        b"content with metadata",
        metadata=metadata,
    )

    # 메타데이터 파일 확인
    meta_path = Path(temp_storage_dir) / "test" / "metadata.txt.meta"
    assert meta_path.exists()

    import json
    stored_meta = json.loads(meta_path.read_text())
    assert stored_meta == metadata


@pytest.mark.asyncio
async def test_local_storage_url(temp_storage_dir):
    """URL 생성 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    await storage.upload("urltest.txt", b"content")
    url = await storage.get_url("urltest.txt")

    assert url.startswith("file://")
    assert "urltest.txt" in url


@pytest.mark.asyncio
async def test_nested_directories(temp_storage_dir):
    """중첩 디렉토리 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    # 깊은 경로에 저장
    deep_path = "a/b/c/d/e/file.txt"
    await storage.upload(deep_path, b"deep content")

    # 다운로드
    content = await storage.download(deep_path)
    assert content == b"deep content"

    # 존재 확인
    assert await storage.exists(deep_path)


@pytest.mark.asyncio
async def test_download_nonexistent_file(temp_storage_dir):
    """존재하지 않는 파일 다운로드 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    with pytest.raises(FileNotFoundError):
        await storage.download("nonexistent.txt")


@pytest.mark.asyncio
async def test_factory_env_var(monkeypatch, temp_storage_dir):
    """환경 변수 기반 Factory 테스트"""
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("STORAGE_BASE_PATH", temp_storage_dir)

    storage = get_storage_gateway()

    assert storage.provider_name == "local"
    assert str(storage.base_path) == temp_storage_dir


def test_factory_s3_missing_bucket():
    """S3 버킷 누락 테스트"""
    with pytest.raises(ValueError, match="bucket_name is required"):
        get_storage_gateway(provider="s3")


@pytest.mark.asyncio
async def test_parallel_uploads(temp_storage_dir):
    """병렬 업로드 테스트"""
    storage = get_storage_gateway(provider="local", base_path=temp_storage_dir)

    tasks = [
        storage.upload(f"parallel/file{i}.txt", f"content{i}".encode())
        for i in range(10)
    ]

    uris = await asyncio.gather(*tasks)

    assert len(uris) == 10
    for uri in uris:
        assert uri.startswith("file://")

    # 모든 파일 존재 확인
    files = await storage.list("parallel")
    assert len(files) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
