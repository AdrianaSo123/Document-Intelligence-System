from bdis.adapters.s3_storage import S3StorageAdapter


def test_storage_adapter_partitions_by_workspace_and_document(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    adapter = S3StorageAdapter()

    uri = adapter.upload_file(
        workspace_id="ws1",
        document_id="doc1",
        file_bytes=b"hello",
        filename="invoice.pdf",
    )

    assert uri.startswith("local://")
    assert "storage/workspaces/ws1/documents/doc1/" in uri
