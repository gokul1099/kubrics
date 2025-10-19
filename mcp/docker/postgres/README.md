# PostgreSQL with pgvector Setup

This directory contains the PostgreSQL setup with pgvector extension for vector similarity search.

## Quick Start

### 1. Start PostgreSQL

```bash
./postgres.sh start
```

This will:
- Start PostgreSQL 17 with pgvector extension in Docker
- Initialize the database with vector support
- Create a sample embeddings table
- Set up indexes for vector similarity search

### 2. Verify Connection

```bash
./postgres.sh test
```

Or manually with psql:

```bash
./postgres.sh shell
```

## Configuration

All configuration is in the `.env` file at the project root:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=kubric_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kubric_db
```

## Management Commands

The `postgres.sh` script provides easy management:

```bash
# Start PostgreSQL
./postgres.sh start

# Stop PostgreSQL
./postgres.sh stop

# Restart PostgreSQL
./postgres.sh restart

# View logs (follow mode)
./postgres.sh logs

# Check status
./postgres.sh status

# Connect to PostgreSQL shell
./postgres.sh shell

# Test connection with Python
./postgres.sh test

# Remove container and all data (WARNING: destructive)
./postgres.sh clean
```

## Database Schema

### Embeddings Table

The initialization script creates an `embeddings` table:

```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- Adjust dimension based on your model
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Vector Index

An IVFFlat index is created for fast similarity search:

```sql
CREATE INDEX embeddings_embedding_idx ON embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Using pgvector

### Insert Vectors

```python
import psycopg2
from psycopg2.extras import Json

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="kubric_db",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()

# Insert a vector
embedding = [0.1, 0.2, 0.3, ...]  # Your embedding vector
cursor.execute(
    "INSERT INTO embeddings (content, embedding, metadata) VALUES (%s, %s, %s)",
    ("Sample text", embedding, Json({"source": "test"}))
)

conn.commit()
```

### Similarity Search

```python
# Find similar vectors (cosine distance)
query_vector = [0.1, 0.2, 0.3, ...]  # Your query vector

cursor.execute("""
    SELECT id, content, embedding <-> %s::vector as distance
    FROM embeddings
    ORDER BY embedding <-> %s::vector
    LIMIT 10
""", (query_vector, query_vector))

results = cursor.fetchall()
for id, content, distance in results:
    print(f"{id}: {content} (distance: {distance})")
```

### Distance Operators

pgvector supports three distance operators:

- `<->` - Cosine distance (most common for embeddings)
- `<#>` - Negative inner product
- `<=>` - Euclidean distance (L2)

## Python Integration

### Install Required Package

```bash
pip install psycopg2-binary
# or
poetry add psycopg2-binary
```

### Connection Example

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# Your database operations here
cursor.execute("SELECT version();")
print(cursor.fetchone())

cursor.close()
conn.close()
```

## Troubleshooting

### Container won't start

```bash
# Check if port 5432 is already in use
lsof -i :5432

# View detailed logs
./postgres.sh logs

# Clean and restart
./postgres.sh clean
./postgres.sh start
```

### Connection refused

1. Ensure the container is running: `./postgres.sh status`
2. Wait for health check to pass (30 seconds on first start)
3. Check credentials in `.env` file
4. Test connection: `./postgres.sh test`

### pgvector not working

```bash
# Connect to shell and verify
./postgres.sh shell

# Then in psql:
\dx                        # List installed extensions
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

### Reset everything

```bash
# This will delete all data and start fresh
./postgres.sh clean
./postgres.sh start
```

## Files

- `init.sql` - Database initialization script (runs on first start)
- `test_connection.py` - Python script to test connection and pgvector
- `README.md` - This file

## Docker Details

- **Image**: pgvector/pgvector:pg17
- **Container Name**: postgres-pgvector
- **Network**: kubric-network
- **Volume**: postgres_data (persistent storage)
- **Health Check**: Runs every 10 seconds

## Security Notes

**WARNING**: The default credentials (postgres/postgres) are for development only.

For production:
1. Change the password in `.env`
2. Use environment variables or secrets management
3. Restrict network access
4. Enable SSL/TLS
5. Regular backups

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
