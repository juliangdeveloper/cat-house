"""
Test database connectivity for all services.

This script verifies that each service can:
1. Connect to Neon PostgreSQL
2. Execute queries
3. Access their designated tables
"""
import asyncio
import sys
import os
from pathlib import Path

# Add service paths to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "auth-service"))
sys.path.insert(0, str(backend_dir / "catalog-service"))
sys.path.insert(0, str(backend_dir / "installation-service"))
sys.path.insert(0, str(backend_dir / "proxy-service"))

# Change to auth-service directory to load .env
os.chdir(backend_dir / "auth-service")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_service_connection(service_name: str, engine, session_maker):
    """Test database connection for a service."""
    print(f"\n{'='*60}")
    print(f"Testing {service_name}")
    print(f"{'='*60}")
    
    try:
        # Test 1: Basic connection
        print("✓ Creating session...")
        async with session_maker() as session:
            print("✓ Session created successfully")
            
            # Test 2: Execute simple query
            print("✓ Testing simple query...")
            result = await session.execute(text("SELECT 1 as test"))
            row = result.first()
            assert row[0] == 1
            print(f"✓ Simple query successful: {row[0]}")
            
            # Test 3: Check database version
            print("✓ Checking PostgreSQL version...")
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ PostgreSQL version: {version[:50]}...")
            
            # Test 4: List tables
            print("✓ Listing tables...")
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
            
            # Test 5: Service-specific queries
            if service_name == "Auth Service":
                print("✓ Testing users table access...")
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                print(f"✓ Users table: {count} rows")
                
            elif service_name == "Catalog Service":
                print("✓ Testing cats table access...")
                result = await session.execute(text("SELECT COUNT(*) FROM cats"))
                count = result.scalar()
                print(f"✓ Cats table: {count} rows")
                
                print("✓ Testing permissions table access...")
                result = await session.execute(text("SELECT COUNT(*) FROM permissions"))
                count = result.scalar()
                print(f"✓ Permissions table: {count} rows")
                
            elif service_name == "Installation Service":
                print("✓ Testing installations table access...")
                result = await session.execute(text("SELECT COUNT(*) FROM installations"))
                count = result.scalar()
                print(f"✓ Installations table: {count} rows")
                
                print("✓ Testing installation_permissions table access...")
                result = await session.execute(text("SELECT COUNT(*) FROM installation_permissions"))
                count = result.scalar()
                print(f"✓ Installation_permissions table: {count} rows")
            
            elif service_name == "Proxy Service":
                print("✓ Testing read access to all tables...")
                for table in tables:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  - {table}: {count} rows")
        
        print(f"\n✅ {service_name}: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ {service_name}: FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run connectivity tests for all services."""
    print("="*60)
    print("Cat House Backend - Database Connectivity Tests")
    print("="*60)
    print("\nTesting connectivity to Neon PostgreSQL...")
    
    results = {}
    
    # Test Auth Service
    try:
        from app.database import engine as auth_engine, AsyncSessionLocal as auth_session
        results["Auth Service"] = await test_service_connection(
            "Auth Service", auth_engine, auth_session
        )
    except Exception as e:
        print(f"\n❌ Auth Service: Failed to import or connect")
        print(f"Error: {str(e)}")
        results["Auth Service"] = False
    
    # Test Catalog Service
    os.chdir(backend_dir / "catalog-service")
    try:
        from app.database import engine as catalog_engine, AsyncSessionLocal as catalog_session
        results["Catalog Service"] = await test_service_connection(
            "Catalog Service", catalog_engine, catalog_session
        )
    except Exception as e:
        print(f"\n❌ Catalog Service: Failed to import or connect")
        print(f"Error: {str(e)}")
        results["Catalog Service"] = False
    
    # Test Installation Service
    os.chdir(backend_dir / "installation-service")
    try:
        from app.database import engine as install_engine, AsyncSessionLocal as install_session
        results["Installation Service"] = await test_service_connection(
            "Installation Service", install_engine, install_session
        )
    except Exception as e:
        print(f"\n❌ Installation Service: Failed to import or connect")
        print(f"Error: {str(e)}")
        results["Installation Service"] = False
    
    # Test Proxy Service
    os.chdir(backend_dir / "proxy-service")
    try:
        from app.database import engine as proxy_engine, AsyncSessionLocal as proxy_session
        results["Proxy Service"] = await test_service_connection(
            "Proxy Service", proxy_engine, proxy_session
        )
    except Exception as e:
        print(f"\n❌ Proxy Service: Failed to import or connect")
        print(f"Error: {str(e)}")
        results["Proxy Service"] = False
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for service, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{service:30} {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL SERVICES CONNECTED SUCCESSFULLY!")
    else:
        print("⚠️  SOME SERVICES FAILED TO CONNECT")
        print("Check .env files and Neon connection strings")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
