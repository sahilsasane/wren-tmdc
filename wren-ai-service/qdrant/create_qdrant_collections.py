import asyncio
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Force create all Qdrant collections."""
    logger.info("🚀 Creating Qdrant collections...")

    # Connect to Qdrant
    client = QdrantClient(url="http://localhost:6333")

    # Collection configurations
    collections = [
        "Document",
        "table_descriptions",
        "view_questions",
        "sql_pairs",
        "instructions",
        "project_meta",
    ]

    # Embedding dimension from config (text-embedding-3-large)
    embedding_dim = 3072

    try:
        for collection_name in collections:
            try:
                # Check if collection exists
                existing_collections = client.get_collections()
                collection_exists = any(
                    col.name == collection_name
                    for col in existing_collections.collections
                )

                if collection_exists:
                    logger.info(f"✅ Collection '{collection_name}' already exists")
                else:
                    # Create collection
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=embedding_dim, distance=Distance.COSINE
                        ),
                    )
                    logger.info(f"✅ Created collection '{collection_name}'")

                    # Create payload index for project_id
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="project_id",
                        field_schema="keyword",
                    )
                    logger.info(f"✅ Created project_id index for '{collection_name}'")

            except Exception as e:
                logger.error(f"❌ Failed to create collection '{collection_name}': {e}")

        logger.info("🎉 Qdrant collections creation complete!")

        # List all collections
        collections_info = client.get_collections()
        logger.info("📋 Current collections:")
        for col in collections_info.collections:
            logger.info(f"   - {col.name}")

    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running on http://localhost:6333")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
