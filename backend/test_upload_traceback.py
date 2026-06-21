import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.services.document_service import DocumentService
from app.services.storage_service import get_storage_backend
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async with AsyncSession(engine) as db:
        storage = get_storage_backend()
        svc = DocumentService(db, storage)
        
        # We need a mock UploadFile
        from fastapi import UploadFile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Hello world")
            tmp_name = f.name
            
        with open(tmp_name, "rb") as f:
            upload_file = UploadFile(filename="test.txt", file=f)
            
            # Use real section and uploader
            section_id = uuid.UUID('00000000-0000-0000-0002-000000000001')
            uploader_id = uuid.UUID('00000000-0000-0000-0001-000000000001')
            
            try:
                await svc.upload(
                    section_id=section_id,
                    title="Direct Test",
                    description="",
                    version_label=None,
                    file=upload_file,
                    uploader_id=uploader_id,
                    ip="127.0.0.1"
                )
                print("Upload success")
            except Exception as e:
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
