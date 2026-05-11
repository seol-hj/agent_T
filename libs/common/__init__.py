"""
Common Libraries

공통 라이브러리 패키지
"""

import os
from typing import Optional

from .gateways.storage import StorageGateway, LocalStorageGateway, S3StorageGateway
from .gateways.llm import LLMGateway, BedrockLLMGateway, MockLLMProvider
from .models.llm_response import LLMResponse, LLMUsageMetadata
# from .rag import Retriever, InMemoryRetriever, VectorRetriever  # TODO: RAG 모듈 구현 후 활성화


def get_storage_gateway() -> StorageGateway:
    """
    Storage Gateway 팩토리 함수

    환경 변수 STORAGE_PROVIDER로 선택:
    - local: LocalStorageGateway
    - s3: S3StorageGateway
    """
    provider = os.getenv("STORAGE_PROVIDER", "local")

    if provider == "s3":
        bucket_name = os.getenv("STORAGE_BASE_PATH", "agent-t-storage")
        region = os.getenv("AWS_REGION", "ap-northeast-2")
        return S3StorageGateway(bucket_name=bucket_name, region=region)
    else:
        base_path = os.getenv("STORAGE_BASE_PATH", "/tmp/storage")
        return LocalStorageGateway(base_path=base_path)


def get_llm_gateway() -> LLMGateway:
    """
    LLM Gateway 팩토리 함수

    환경 변수 LLM_PROVIDER로 선택:
    - mock: MockLLMProvider (테스트용)
    - bedrock: BedrockLLMGateway
    """
    provider = os.getenv("LLM_PROVIDER", "bedrock")

    if provider == "mock":
        model_id = os.getenv("LLM_MODEL_ID", "mock-model-v1")
        return MockLLMProvider(model_id=model_id)
    elif provider == "bedrock":
        region = os.getenv("AWS_REGION", "us-east-1")
        model_id = os.getenv("LLM_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
        return BedrockLLMGateway(region=region, model_id=model_id)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_rag_retriever() -> Retriever:
    """
    RAG Retriever 팩토리 함수

    환경 변수 RAG_RETRIEVER로 선택:
    - in_memory: InMemoryRetriever (기본)
    - vector: VectorRetriever (향후)
    - bedrock_kb: BedrockKnowledgeBaseRetriever (향후)
    """
    retriever_type = os.getenv("RAG_RETRIEVER", "in_memory")

    if retriever_type == "in_memory":
        chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "500"))
        chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
        return InMemoryRetriever(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif retriever_type == "vector":
        return VectorRetriever()
    else:
        raise ValueError(f"Unsupported RAG retriever: {retriever_type}")


__all__ = [
    "StorageGateway",
    "LocalStorageGateway",
    "S3StorageGateway",
    "LLMGateway",
    "BedrockLLMGateway",
    "MockLLMProvider",
    "LLMResponse",
    "LLMUsageMetadata",
    "Retriever",
    "InMemoryRetriever",
    "VectorRetriever",
    "get_storage_gateway",
    "get_llm_gateway",
    "get_rag_retriever",
]
