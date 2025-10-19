# MinIO Object Storage Setup

This directory contains the MinIO setup for S3-compatible object storage for videos, embeddings, and other files.

## Quick Start

### 1. Start MinIO

```bash
./minio.sh start
```

This will:
- Start MinIO server in Docker
- Initialize default buckets (videos, embeddings, thumbnails)
- Start the MinIO Console web interface

### 2. Access MinIO Console

```bash
./minio.sh console
```

Or manually visit: http://localhost:9001

**Default Credentials:**
- Username: `minioadmin`
- Password: `minioadmin`

### 3. Verify Connection

```bash
./minio.sh test
```

## Configuration

All configuration is in the `.env` file at the project root:

```env
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=localhost:9000
MINIO_API_URL=http://localhost:9000
MINIO_CONSOLE_URL=http://localhost:9001
MINIO_BUCKET=videos
MINIO_USE_SSL=false
```

## Management Commands

The `minio.sh` script provides easy management:

```bash
# Start MinIO
./minio.sh start

# Stop MinIO
./minio.sh stop

# Restart MinIO
./minio.sh restart

# View logs (follow mode)
./minio.sh logs

# Check status
./minio.sh status

# Open MinIO Console in browser
./minio.sh console

# Create a new bucket
./minio.sh bucket <bucket-name>

# List all buckets
./minio.sh list

# Upload a file
./minio.sh upload <bucket-name> <file-path>

# Get server information
./minio.sh info

# Test connection with Python
./minio.sh test

# Remove container and all data (WARNING: destructive)
./minio.sh clean
```

## Default Buckets

Three buckets are automatically created on first start:

1. **videos** - Store video files
2. **embeddings** - Store embedding data
3. **thumbnails** - Store video thumbnails

## Using MinIO with Python

### Install Required Package

```bash
pip install minio
# or
poetry add minio
```

### Connection Example

```python
import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

# Initialize MinIO client
client = Minio(
    os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
    access_key=os.getenv('MINIO_ROOT_USER', 'minioadmin'),
    secret_key=os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
    secure=False  # Set to True if using HTTPS
)

# List all buckets
buckets = client.list_buckets()
for bucket in buckets:
    print(bucket.name)
```

### Upload a File

```python
# Upload a file
client.fput_object(
    "videos",
    "my-video.mp4",
    "/path/to/my-video.mp4",
    content_type="video/mp4"
)
print("File uploaded successfully!")
```

### Upload from Memory

```python
from io import BytesIO

# Upload data from memory
data = b"Hello, MinIO!"
client.put_object(
    "videos",
    "test.txt",
    BytesIO(data),
    length=len(data),
    content_type="text/plain"
)
```

### Download a File

```python
# Download a file
client.fget_object(
    "videos",
    "my-video.mp4",
    "/path/to/download/my-video.mp4"
)
```

### Download to Memory

```python
# Download to memory
response = client.get_object("videos", "test.txt")
data = response.read()
response.close()
response.release_conn()
print(data)
```

### List Objects in a Bucket

```python
# List all objects in a bucket
objects = client.list_objects("videos", recursive=True)
for obj in objects:
    print(f"{obj.object_name} - {obj.size} bytes")
```

### Delete an Object

```python
# Delete an object
client.remove_object("videos", "my-video.mp4")
```

### Get Object Metadata

```python
# Get object information
stat = client.stat_object("videos", "my-video.mp4")
print(f"Size: {stat.size}")
print(f"Content-Type: {stat.content_type}")
print(f"Last Modified: {stat.last_modified}")
```

### Generate Presigned URL

```python
from datetime import timedelta

# Generate a presigned URL (valid for 7 days)
url = client.presigned_get_object(
    "videos",
    "my-video.mp4",
    expires=timedelta(days=7)
)
print(f"Download URL: {url}")
```

### Check if Bucket Exists

```python
# Check if a bucket exists
if client.bucket_exists("videos"):
    print("Bucket exists!")
else:
    print("Bucket does not exist")
```

### Create a Bucket

```python
# Create a new bucket
client.make_bucket("my-bucket")
```

## Using MinIO with CLI (mc)

MinIO Client (mc) is available inside the container:

```bash
# Access the container
docker exec -it kubric-minio sh

# Inside container, mc is already configured
mc ls local/
mc cp /data/videos/video.mp4 /tmp/
```

## Use Cases

### Video Processing Pipeline

```python
from minio import Minio
import os

client = Minio(
    os.getenv('MINIO_ENDPOINT'),
    access_key=os.getenv('MINIO_ROOT_USER'),
    secret_key=os.getenv('MINIO_ROOT_PASSWORD'),
    secure=False
)

# 1. Upload video
client.fput_object("videos", "input.mp4", "/path/to/input.mp4")

# 2. Process video (your processing logic here)
# process_video()

# 3. Upload processed video
client.fput_object("videos", "output.mp4", "/path/to/output.mp4")

# 4. Upload thumbnail
client.fput_object("thumbnails", "thumb.jpg", "/path/to/thumb.jpg")
```

### Embedding Storage

```python
import json
import pickle
from io import BytesIO

# Store embeddings as pickle
embeddings_data = {"text": "Hello", "vector": [0.1, 0.2, 0.3]}
pickle_data = pickle.dumps(embeddings_data)

client.put_object(
    "embeddings",
    "doc_123.pkl",
    BytesIO(pickle_data),
    length=len(pickle_data),
    content_type="application/octet-stream"
)

# Store metadata as JSON
metadata = {"id": "doc_123", "source": "upload"}
json_data = json.dumps(metadata).encode()

client.put_object(
    "embeddings",
    "doc_123.json",
    BytesIO(json_data),
    length=len(json_data),
    content_type="application/json"
)
```

## Troubleshooting

### Container won't start

```bash
# Check if ports are already in use
lsof -i :9000
lsof -i :9001

# View detailed logs
./minio.sh logs

# Clean and restart
./minio.sh clean
./minio.sh start
```

### Connection refused

1. Ensure the container is running: `./minio.sh status`
2. Wait for health check to pass (30 seconds on first start)
3. Check credentials in `.env` file
4. Test connection: `./minio.sh test`

### Bucket not found

```bash
# List all buckets
./minio.sh list

# Create missing bucket
./minio.sh bucket <bucket-name>
```

### Permission denied

Check that the MinIO user has proper permissions:

```bash
# View server info
./minio.sh info

# Check bucket policies
docker exec kubric-minio mc admin policy list local
```

### Reset everything

```bash
# This will delete all data and start fresh
./minio.sh clean
./minio.sh start
```

## Docker Details

- **Image**: minio/minio:latest
- **Container Name**: kubric-minio
- **API Port**: 9000
- **Console Port**: 9001
- **Network**: kubric-network
- **Volume**: minio_data (persistent storage)
- **Health Check**: Runs every 30 seconds

## Security Notes

**WARNING**: The default credentials (minioadmin/minioadmin) are for development only.

For production:
1. Change credentials in `.env`
2. Enable SSL/TLS (set `MINIO_USE_SSL=true`)
3. Use strong passwords
4. Configure proper bucket policies
5. Enable versioning for important buckets
6. Regular backups
7. Use IAM policies for fine-grained access control

## Accessing from External Services

To access MinIO from outside Docker (e.g., from your Python application):

```python
# Use localhost for local development
client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)

# For Docker container-to-container communication
client = Minio(
    'kubric-minio:9000',  # Use container name
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)
```

## Web Console Features

Access at http://localhost:9001:

- Browse buckets and objects
- Upload/download files via drag-and-drop
- Create and manage buckets
- Set bucket policies
- View object metadata
- Generate presigned URLs
- Monitor server performance
- Manage users and access keys

## Integration with Other Services

### With PostgreSQL (for metadata)

```python
import psycopg2
from minio import Minio

# Store file in MinIO
client.fput_object("videos", "video.mp4", "/path/to/video.mp4")

# Store metadata in PostgreSQL
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO videos (filename, minio_bucket, minio_key, size) VALUES (%s, %s, %s, %s)",
    ("video.mp4", "videos", "video.mp4", 1024000)
)
conn.commit()
```

## References

- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [MinIO Python Client](https://min.io/docs/minio/linux/developers/python/API.html)
- [Amazon S3 Compatibility](https://docs.min.io/docs/minio-server-configuration-guide.html)
