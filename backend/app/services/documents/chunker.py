from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Scholarship, ScholarshipChunk

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class ScholarshipChunker:
    def __init__(self, db: AsyncSession):
        self.db = db
        # 512 characters ~ 100-150 tokens, so let's use 2000 chars for ~512 tokens
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=250,
            length_function=len,
        )
        if SentenceTransformer:
            self.embedder = SentenceTransformer("all-mpnet-base-v2")
        else:
            self.embedder = None

    async def chunk_and_embed_scholarship(self, scholarship: Scholarship):
        if not self.embedder:
            print("SentenceTransformer not available, skipping chunking.")
            return

        # Combine text fields to index
        text_parts = [
            f"Title: {scholarship.title}",
            f"Provider: {scholarship.provider_name}",
            f"Country: {scholarship.country_code}",
        ]
        if scholarship.summary:
            text_parts.append(f"Summary: {scholarship.summary}")
        if scholarship.funding_summary:
            text_parts.append(f"Funding: {scholarship.funding_summary}")
        
        full_text = "\n\n".join(text_parts)
        
        chunks = self.text_splitter.split_text(full_text)
        
        # Optionally, delete old chunks
        # await self.db.execute(delete(ScholarshipChunk).where(ScholarshipChunk.scholarship_id == scholarship.id))
        
        for i, chunk_text in enumerate(chunks):
            embedding = self.embedder.encode(chunk_text).tolist()
            chunk_record = ScholarshipChunk(
                scholarship_id=scholarship.id,
                chunk_index=i,
                content_text=chunk_text,
                embedding=embedding
            )
            self.db.add(chunk_record)
        
        await self.db.flush()
