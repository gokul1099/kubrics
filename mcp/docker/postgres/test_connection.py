#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script
Tests connection to PostgreSQL and verifies pgvector extension
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test PostgreSQL connection and pgvector extension"""

    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        print("❌ Error: psycopg2 not installed")
        print("Install it with: pip install psycopg2-binary")
        return False

    # Get connection details from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'kubric_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }

    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    print(f"\n📋 Connection Details:")
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")
    print()

    try:
        # Connect to PostgreSQL
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connection successful!")

        # Test 1: Check PostgreSQL version
        print("\n📊 PostgreSQL Version:")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   {version.split(',')[0]}")

        # Test 2: Check pgvector extension
        print("\n🔍 Checking pgvector extension:")
        cursor.execute("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'vector';
        """)
        result = cursor.fetchone()

        if result:
            print(f"   ✅ pgvector {result[1]} is installed and enabled")
        else:
            print("   ❌ pgvector extension not found")
            return False

        # Test 3: Check embeddings table
        print("\n📁 Checking embeddings table:")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'embeddings'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM embeddings;")
            count = cursor.fetchone()[0]
            print(f"   ✅ Embeddings table exists with {count} records")
        else:
            print("   ⚠️  Embeddings table not found")

        # Test 4: Test vector operations
        print("\n🧪 Testing vector operations:")
        try:
            cursor.execute("""
                SELECT '[1,2,3]'::vector(3) <-> '[4,5,6]'::vector(3) as distance;
            """)
            distance = cursor.fetchone()[0]
            print(f"   ✅ Vector operations working (test distance: {distance:.4f})")
        except Exception as e:
            print(f"   ❌ Vector operation failed: {e}")
            return False

        # Test 5: List all tables
        print("\n📚 Available tables:")
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = cursor.fetchall()
        if tables:
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("   (no tables found)")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ All tests passed! PostgreSQL with pgvector is ready to use.")
        print("=" * 60)

        return True

    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL container is running: ./postgres.sh status")
        print("2. Check if the container is healthy: docker ps")
        print("3. View logs: ./postgres.sh logs")
        print("4. Verify .env file has correct credentials")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
