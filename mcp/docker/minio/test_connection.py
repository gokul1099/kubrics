#!/usr/bin/env python3
"""
MinIO Connection Test Script
Tests connection to MinIO and verifies bucket access
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test MinIO connection and bucket operations"""

    try:
        from minio import Minio
        from minio.error import S3Error
    except ImportError:
        print("❌ Error: minio not installed")
        print("Install it with: pip install minio")
        return False

    # Get connection details from environment
    endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
    secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
    use_ssl = os.getenv('MINIO_USE_SSL', 'false').lower() == 'true'

    print("=" * 60)
    print("MinIO Connection Test")
    print("=" * 60)
    print(f"\n📋 Connection Details:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Access Key: {access_key}")
    print(f"   Use SSL: {use_ssl}")
    print()

    try:
        # Connect to MinIO
        print("🔌 Connecting to MinIO...")
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=use_ssl
        )
        print("✅ Connection successful!")

        # Test 1: List all buckets
        print("\n📦 Listing all buckets:")
        buckets = client.list_buckets()
        if buckets:
            for bucket in buckets:
                print(f"   - {bucket.name} (created: {bucket.creation_date})")
        else:
            print("   (no buckets found)")

        # Test 2: Check default buckets
        print("\n🔍 Checking default buckets:")
        default_buckets = ['videos', 'embeddings', 'thumbnails']
        for bucket_name in default_buckets:
            exists = client.bucket_exists(bucket_name)
            if exists:
                print(f"   ✅ {bucket_name} exists")

                # Count objects in bucket
                try:
                    objects = list(client.list_objects(bucket_name))
                    print(f"      └─ {len(objects)} objects")
                except Exception as e:
                    print(f"      └─ Could not count objects: {e}")
            else:
                print(f"   ❌ {bucket_name} not found")

        # Test 3: Test bucket operations (create test bucket)
        print("\n🧪 Testing bucket operations:")
        test_bucket = "test-bucket"

        try:
            if not client.bucket_exists(test_bucket):
                client.make_bucket(test_bucket)
                print(f"   ✅ Created test bucket: {test_bucket}")
            else:
                print(f"   ℹ️  Test bucket already exists: {test_bucket}")

            # Test 4: Test object operations (upload test file)
            print("\n📤 Testing object operations:")
            test_content = b"Hello from Kubric! This is a test file."
            test_object = "test-file.txt"

            from io import BytesIO

            client.put_object(
                test_bucket,
                test_object,
                BytesIO(test_content),
                length=len(test_content),
                content_type='text/plain'
            )
            print(f"   ✅ Uploaded test file: {test_object}")

            # Test 5: Download and verify
            print("\n📥 Testing download:")
            response = client.get_object(test_bucket, test_object)
            downloaded_content = response.read()
            response.close()
            response.release_conn()

            if downloaded_content == test_content:
                print(f"   ✅ Downloaded and verified test file")
            else:
                print(f"   ❌ Content mismatch")
                return False

            # Test 6: Get object metadata
            print("\n📊 Testing metadata:")
            stat = client.stat_object(test_bucket, test_object)
            print(f"   - Size: {stat.size} bytes")
            print(f"   - Content-Type: {stat.content_type}")
            print(f"   - ETag: {stat.etag}")
            print(f"   - Last Modified: {stat.last_modified}")

            # Cleanup test objects
            print("\n🧹 Cleaning up test objects...")
            client.remove_object(test_bucket, test_object)
            print(f"   ✅ Removed test file")

        except S3Error as e:
            print(f"   ❌ S3 Error: {e}")
            return False

        # Test 7: Server information
        print("\n🖥️  MinIO Server Status:")
        print(f"   ✅ Server is healthy and responding")
        print(f"   API Endpoint: http://{endpoint}")
        print(f"   Console: {os.getenv('MINIO_CONSOLE_URL', 'http://localhost:9001')}")

        print("\n" + "=" * 60)
        print("✅ All tests passed! MinIO is ready to use.")
        print("=" * 60)
        print("\nNext steps:")
        print("  - Access MinIO Console: ./minio.sh console")
        print("  - Create a bucket: ./minio.sh bucket <bucket-name>")
        print("  - Upload a file: ./minio.sh upload <bucket> <file>")
        print("  - List buckets: ./minio.sh list")

        return True

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MinIO container is running: ./minio.sh status")
        print("2. Check if the container is healthy: docker ps")
        print("3. View logs: ./minio.sh logs")
        print("4. Verify .env file has correct credentials")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
