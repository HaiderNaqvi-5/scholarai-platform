import asyncio
import os
import sys
import uuid
from sqlalchemy import select
from sentence_transformers import SentenceTransformer

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import async_session_factory
from app.models import Scholarship, RecordState
from app.services.recommendations.hybrid_retriever import OpenSearchHybridRetriever

async def bulk_index():
    print("Starting bulk indexing of scholarships to OpenSearch...")
    retriever = OpenSearchHybridRetriever()
    await retriever.create_index_if_not_exists()
    
    print("Loading embedder model...")
    embedder = SentenceTransformer('all-mpnet-base-v2')
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(Scholarship).where(Scholarship.record_state == RecordState.PUBLISHED)
        )
        scholarships = result.scalars().all()
        
        print(f"Found {len(scholarships)} published scholarships to index.")
        
        for i, scholarship in enumerate(scholarships):
            # Generate embedding
            text_to_embed = f"{scholarship.title} {scholarship.summary or ''} {scholarship.provider_name or ''}"
            embedding = embedder.encode(text_to_embed).tolist()
            
            # Index
            await retriever.index_scholarship(scholarship, embedding)
            
            if (i + 1) % 10 == 0:
                print(f"Indexed {i + 1}/{len(scholarships)}...")
                
    print("Bulk indexing complete.")

if __name__ == "__main__":
    asyncio.run(bulk_index())
