"""
Document Loader (Placeholder)

S3에서 문서 로드 (향후 구현)
"""

from typing import List, Optional
from pathlib import Path

from .schemas import Document


class DocumentLoader:
    """
    문서 로더 (Placeholder)

    향후 구현:
    - S3 rag-source 버킷에서 문서 읽기
    - PDF, DOCX, TXT, Markdown 등 파싱
    - 메타데이터 추출
    - 자동 청킹
    """

    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        local_path: Optional[str] = None,
    ):
        """
        Args:
            s3_bucket: S3 버킷 이름 (예: agent-t-rag-source)
            local_path: 로컬 문서 경로
        """
        self.s3_bucket = s3_bucket
        self.local_path = local_path

    async def load_from_s3(self, prefix: str = "") -> List[Document]:
        """
        S3에서 문서 로드

        Args:
            prefix: S3 prefix (폴더 경로)

        Returns:
            Document 리스트
        """
        raise NotImplementedError(
            "S3 document loading is not yet implemented. "
            "Use load_from_local or manually add documents for now."
        )

    async def load_from_local(self, directory: str) -> List[Document]:
        """
        로컬 디렉토리에서 문서 로드

        Args:
            directory: 로컬 디렉토리 경로

        Returns:
            Document 리스트
        """
        documents = []
        dir_path = Path(directory)

        if not dir_path.exists():
            return documents

        # 텍스트 파일 읽기
        for file_path in dir_path.glob("**/*.txt"):
            try:
                content = file_path.read_text(encoding='utf-8')
                document = Document(
                    document_id=file_path.stem,
                    title=file_path.name,
                    content=content,
                    source=str(file_path),
                    category="local",
                    tags=["local", file_path.parent.name],
                )
                documents.append(document)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")

        return documents

    async def parse_pdf(self, file_path: str) -> Document:
        """
        PDF 파일 파싱 (향후 구현)

        Args:
            file_path: PDF 파일 경로

        Returns:
            Document
        """
        raise NotImplementedError("PDF parsing is not yet implemented.")

    async def parse_docx(self, file_path: str) -> Document:
        """
        DOCX 파일 파싱 (향후 구현)

        Args:
            file_path: DOCX 파일 경로

        Returns:
            Document
        """
        raise NotImplementedError("DOCX parsing is not yet implemented.")
