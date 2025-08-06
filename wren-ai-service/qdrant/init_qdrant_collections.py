import asyncio
import logging

from src.config import settings
from src.providers import generate_components

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize all Qdrant collections."""
    logger.info("🚀 Initializing Qdrant collections...")

    try:
        # Generate all components which will create the collections
        _ = generate_components(settings.components)
        logger.info("✅ Successfully generated all pipeline components")

        # List the collections that should now exist
        collections = [
            "Document",
            "table_descriptions",
            "view_questions",
            "sql_pairs",
            "instructions",
            "project_meta",
        ]

        logger.info("📋 Collections that should now exist:")
        for collection in collections:
            logger.info(f"   - {collection}")

        logger.info("🎉 Qdrant collections initialization complete!")

    except Exception as e:
        logger.error(f"❌ Failed to initialize collections: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
