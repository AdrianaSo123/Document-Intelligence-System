# Sprint 9: S3 Blob Storage & Interactors

**Goal:** Provide secure, permanent storage for raw PDF bytestreams before ingestion. Establish a LocalStack/MinIO emulator to simulate AWS interactions without bleeding AWS credentials into the repository.

## 🎯 Deliverables

1. **Infrastructure Mocking (`docker-compose.yml`):** 
   - Inject a `minio/minio` service to emulate Amazon S3 endpoints.
   - Pre-provision an `invoices` bucket upon startup.

2. **Clean Architecture Dependencies:**
   - Define `IFileStorage` Port in `ports/file_storage.py`.
   - Implement `S3StorageAdapter` using `boto3`.

3. **Use Case Modification:**
   - Upgrade `process_document.py` to accept the `IFileStorage` port.
   - Save the raw bytes and retrieve a generated `s3_uri`.
   - Save the `s3_uri` into the `DocumentInsight` database table.

## ✅ Definition of Done
- Every PDF uploaded physically persists as a file object in the MinIO bucket.
- The PostgreSQL database securely registers the `s3_uri` alongside the extracted JSON data.
