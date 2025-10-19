# Project Structure Analysis & Recommendations

## Current Structure Analysis

```
mcp/
├── src/kubric_mcp/           # Main application code
│   ├── server.py             # FastMCP server
│   ├── tools.py              # MCP tools interface
│   ├── config.py             # Configuration (empty)
│   └── video/
│       └── ingestion/
│           ├── tools.py      # Video extraction tools
│           └── video_processor.py
├── notebook/                  # Jupyter notebooks
│   └── data/                 # Local data storage (should be removed)
│       ├── videos/
│       ├── audio/
│       ├── frames/
│       ├── clips/
│       └── transcripts/
├── docker/                   # Docker configurations
│   ├── postgres/
│   └── minio/
└── [scripts: postgres.sh, minio.sh]
```

## Recommended Folder Structure

```
mcp/
├── src/kubric_mcp/
│   │
│   ├── __init__.py
│   ├── server.py                    # FastMCP server entry point
│   ├── config.py                    # Application configuration
│   │
│   ├── core/                        # Core business logic
│   │   ├── __init__.py
│   │   ├── video_processor.py      # Main video processing orchestrator
│   │   ├── embedding_generator.py  # Generate embeddings for text/video
│   │   └── search_engine.py        # Search functionality
│   │
│   ├── storage/                     # Storage layer (abstraction)
│   │   ├── __init__.py
│   │   ├── postgres.py             # PostgreSQL connection & queries
│   │   ├── vector_store.py         # pgvector operations (semantic search)
│   │   ├── minio_client.py         # MinIO operations (S3-like)
│   │   └── models.py               # Database models/schemas
│   │
│   ├── video/                       # Video-specific operations
│   │   ├── __init__.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── uploader.py         # Upload videos to MinIO
│   │   │   ├── extractor.py        # Extract clips, frames, audio
│   │   │   ├── transcriber.py      # Speech-to-text
│   │   │   └── metadata.py         # Extract video metadata
│   │   │
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   ├── frame_extractor.py  # Extract keyframes
│   │   │   ├── audio_processor.py  # Audio extraction/processing
│   │   │   ├── scene_detector.py   # Scene detection
│   │   │   └── thumbnail_generator.py
│   │   │
│   │   └── analysis/
│   │       ├── __init__.py
│   │       ├── object_detector.py  # Object detection in frames
│   │       ├── text_extractor.py   # OCR from video frames
│   │       └── emotion_analyzer.py # Sentiment/emotion analysis
│   │
│   ├── embeddings/                  # Embedding operations
│   │   ├── __init__.py
│   │   ├── text_embeddings.py      # Text embedding generation
│   │   ├── visual_embeddings.py    # Frame/image embeddings
│   │   └── multimodal_embeddings.py # Combined embeddings
│   │
│   ├── api/                         # API/MCP tools interface
│   │   ├── __init__.py
│   │   ├── tools.py                # MCP tool definitions
│   │   ├── handlers.py             # Request handlers
│   │   └── schemas.py              # API request/response schemas
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── logger.py               # Logging configuration
│       ├── validators.py           # Input validation
│       └── helpers.py              # Common helper functions
│
├── docker/                          # Docker configurations
│   ├── postgres/
│   │   ├── init.sql                # DB initialization
│   │   ├── migrations/             # Database migrations
│   │   │   ├── 001_initial.sql
│   │   │   ├── 002_add_embeddings.sql
│   │   │   └── 003_add_indexes.sql
│   │   ├── test_connection.py
│   │   └── README.md
│   │
│   └── minio/
│       ├── init.sh
│       ├── policies/               # Bucket policies
│       │   └── public_read.json
│       ├── test_connection.py
│       └── README.md
│
├── scripts/                         # Management scripts
│   ├── postgres.sh
│   ├── minio.sh
│   ├── setup.sh                    # Initialize entire stack
│   ├── seed_data.sh                # Seed test data
│   └── migrate.sh                  # Run database migrations
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── unit/
│   │   ├── test_storage.py
│   │   ├── test_video_processing.py
│   │   └── test_embeddings.py
│   ├── integration/
│   │   ├── test_postgres.py
│   │   ├── test_minio.py
│   │   └── test_video_pipeline.py
│   └── e2e/
│       └── test_full_workflow.py
│
├── notebooks/                       # Jupyter notebooks (experiments)
│   ├── 01_video_exploration.ipynb
│   ├── 02_embedding_experiments.ipynb
│   └── 03_search_testing.ipynb
│
├── alembic/                         # Database migrations (if using Alembic)
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── docs/                            # Documentation
│   ├── architecture.md
│   ├── api.md
│   ├── setup.md
│   └── deployment.md
│
├── .env                            # Environment variables
├── .env.example                    # Example environment file
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── docker-compose.db.yml
├── docker-compose.minio.yml
├── docker-compose.yml              # Combined services
└── README.md
```

## Key Design Principles

### 1. Storage Layer Strategy

#### PostgreSQL (with pgvector)

Store in PostgreSQL:
- Video metadata (title, duration, size, format, upload_date)
- Transcript text (full text search)
- Text embeddings (pgvector for semantic search)
- Scene/segment metadata (timestamps, descriptions)
- Processing status and job metadata
- User queries and search history
- Relationships between videos, clips, and frames

#### MinIO (S3-compatible)

Store in MinIO:
- Original video files (bucket: `videos/`)
- Extracted video clips (bucket: `clips/`)
- Keyframes/thumbnails (bucket: `thumbnails/`)
- Audio files (bucket: `audio/`)
- Processed artifacts (bucket: `processed/`)
- Temporary files (bucket: `temp/`)

### 2. Data Flow Architecture

```
Video Upload → MinIO (videos/)
     ↓
Metadata Extraction → PostgreSQL (video_metadata table)
     ↓
Frame Extraction → MinIO (thumbnails/)
     ↓
Audio Extraction → MinIO (audio/)
     ↓
Transcription → PostgreSQL (transcripts table)
     ↓
Embedding Generation → PostgreSQL (embeddings table with pgvector)
     ↓
Indexing Complete → Ready for Search
```

### 3. Database Schema Structure

```sql
-- PostgreSQL Tables Structure

-- Videos table (metadata only)
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    title TEXT,
    description TEXT,
    duration FLOAT,
    file_size BIGINT,
    format VARCHAR(50),
    minio_bucket VARCHAR(100),  -- Reference to MinIO
    minio_key VARCHAR(500),     -- Object path in MinIO
    upload_date TIMESTAMPTZ,
    processing_status VARCHAR(50),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- Segments/Scenes (for temporal search)
CREATE TABLE video_segments (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    start_time FLOAT,
    end_time FLOAT,
    transcript_text TEXT,
    minio_thumbnail_key VARCHAR(500),  -- Thumbnail in MinIO
    created_at TIMESTAMPTZ
);

-- Embeddings (pgvector)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    segment_id UUID REFERENCES video_segments(id),
    content_text TEXT,
    embedding vector(1536),  -- OpenAI embedding dimension
    embedding_type VARCHAR(50),  -- 'text', 'visual', 'multimodal'
    created_at TIMESTAMPTZ
);

-- Create indexes
CREATE INDEX idx_embeddings_video ON embeddings(video_id);
CREATE INDEX idx_embeddings_segment ON embeddings(segment_id);
CREATE INDEX idx_embeddings_vector ON embeddings
    USING ivfflat (embedding vector_cosine_ops);
```

### 4. Module Responsibilities

#### `storage/postgres.py`
- Database connection management
- CRUD operations for metadata
- Transaction management

#### `storage/vector_store.py`
- pgvector operations (similarity search)
- Embedding storage and retrieval
- Batch operations for embeddings

#### `storage/minio_client.py`
- File upload/download operations
- Presigned URL generation
- Bucket management
- File streaming

#### `core/video_processor.py`
- Orchestrates entire video pipeline
- Coordinates storage, processing, and embedding
- Manages processing state

#### `video/ingestion/uploader.py`
- Upload videos to MinIO
- Generate metadata
- Create database records

#### `embeddings/text_embeddings.py`
- Generate embeddings from transcripts
- Store in pgvector
- Batch processing

### 5. Configuration Structure

**`config.py`:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_VIDEOS: str = "videos"
    MINIO_BUCKET_THUMBNAILS: str = "thumbnails"

    # Processing
    MAX_VIDEO_SIZE_MB: int = 1000
    FRAME_EXTRACTION_FPS: float = 1.0

    # AI Models
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
```

### 6. Best Practices

#### ✅ DO:

- Store large binary data (videos, images) in MinIO
- Store structured metadata and relationships in PostgreSQL
- Store embeddings in pgvector for semantic search
- Use MinIO presigned URLs for temporary access
- Keep database records with MinIO references (bucket + key)
- Use database transactions for consistency
- Implement connection pooling for both PostgreSQL and MinIO
- Add indexes on frequently queried fields
- Use UUIDs for distributed system compatibility

#### ❌ DON'T:

- Store video files in PostgreSQL (use MinIO)
- Store embeddings as JSON in regular columns (use pgvector)
- Keep local file copies in `notebook/data/` (delete this)
- Mix business logic with storage logic
- Hardcode credentials (use environment variables)
- Store temporary files permanently

### 7. Why This Structure?

1. **Separation of Concerns**: Storage, processing, and business logic are separated
2. **Scalability**: Each layer can scale independently
3. **Testability**: Easy to mock storage layers for testing
4. **Maintainability**: Clear responsibilities for each module
5. **Performance**: Right tool for right job (MinIO for files, pgvector for search)
6. **Data Consistency**: PostgreSQL ensures ACID properties for metadata

### 8. Example Usage Flow

```python
# src/kubric_mcp/api/tools.py
from kubric_mcp.core.video_processor import VideoProcessor
from kubric_mcp.storage.minio_client import MinIOClient
from kubric_mcp.storage.postgres import PostgresDB

@mcp.tool()
def upload_and_process_video(video_path: str) -> str:
    processor = VideoProcessor()
    video_id = processor.process(video_path)
    return f"Video processed: {video_id}"

# src/kubric_mcp/core/video_processor.py
class VideoProcessor:
    def __init__(self):
        self.minio = MinIOClient()
        self.db = PostgresDB()

    def process(self, video_path: str) -> str:
        # 1. Upload to MinIO
        minio_key = self.minio.upload_video(video_path)

        # 2. Store metadata in PostgreSQL
        video_id = self.db.create_video_record(
            minio_bucket="videos",
            minio_key=minio_key
        )

        # 3. Extract and process
        # ... (transcription, embedding, etc.)

        return video_id
```

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Set up storage layer (`storage/` module)
   - `postgres.py` - Database connection
   - `minio_client.py` - MinIO client
   - `models.py` - Database schema
2. Create database migrations
3. Test storage layer independently

### Phase 2: Core Processing (Week 2)
1. Implement `core/video_processor.py`
2. Build `video/ingestion/` modules
3. Integrate with storage layer

### Phase 3: Embeddings & Search (Week 3)
1. Set up `embeddings/` module
2. Implement `storage/vector_store.py`
3. Build search functionality

### Phase 4: API & Tools (Week 4)
1. Create `api/tools.py` with MCP tools
2. Add validation and error handling
3. Write integration tests

### Phase 5: Advanced Features (Week 5+)
1. Scene detection and analysis
2. Object detection
3. Multimodal embeddings
4. Advanced search features

## Migration from Current Structure

### Step 1: Create new structure
```bash
mkdir -p src/kubric_mcp/{core,storage,embeddings,api,utils}
mkdir -p src/kubric_mcp/video/{ingestion,processing,analysis}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docker/postgres/migrations
mkdir -p scripts
```

### Step 2: Move existing files
```bash
# Keep current video/ingestion but refactor
# Move server.py logic to api/tools.py
# Split tools.py into core/video_processor.py and api/tools.py
```

### Step 3: Remove local data directory
```bash
# Delete notebook/data/ - use MinIO instead
rm -rf notebook/data/
```

### Step 4: Implement storage layer first
- Start with `storage/postgres.py`
- Then `storage/minio_client.py`
- Then `storage/models.py`

### Step 5: Refactor existing code
- Move video processing logic to appropriate modules
- Update imports
- Add proper error handling

## Summary

This structure provides:
- **Clear separation** between storage (MinIO/PostgreSQL) and business logic
- **Scalability** through modular design
- **Testability** with isolated components
- **Maintainability** with clear responsibilities
- **Performance** by using the right tool for each job

The key is to store **files in MinIO** and **metadata/embeddings in PostgreSQL**, with a clean abstraction layer that makes it easy to swap implementations if needed.
