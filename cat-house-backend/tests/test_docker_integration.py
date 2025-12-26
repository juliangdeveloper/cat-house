"""Integration tests for Docker Compose multi-service setup."""
import subprocess
import time
import pytest
import httpx


SERVICES = [
    {"name": "auth-service", "port": 8005, "url": "http://localhost:8005/api/v1/health"},
    {"name": "catalog-service", "port": 8002, "url": "http://localhost:8002/api/v1/health"},
    {"name": "installation-service", "port": 8003, "url": "http://localhost:8003/api/v1/health"},
    {"name": "proxy-service", "port": 8004, "url": "http://localhost:8004/api/v1/health"},
]


@pytest.fixture(scope="module")
def docker_services():
    """Start Docker Compose services and tear them down after tests."""
    # Start services
    subprocess.run(
        ["docker-compose", "up", "-d", "--build"],
        check=True,
        capture_output=True
    )
    
    # Wait for services to be ready
    time.sleep(10)
    
    yield
    
    # Cleanup
    subprocess.run(
        ["docker-compose", "down", "-v"],
        check=True,
        capture_output=True
    )


def test_all_services_start(docker_services):
    """Test that all services start successfully with docker-compose."""
    result = subprocess.run(
        ["docker-compose", "ps", "--services", "--filter", "status=running"],
        capture_output=True,
        text=True,
        check=True
    )
    
    running_services = result.stdout.strip().split("\n")
    
    # Check that core services are running
    expected_services = ["auth-service", "catalog-service", "installation-service", "proxy-service"]
    for service in expected_services:
        assert service in running_services, f"{service} is not running"


def test_all_health_endpoints_respond(docker_services):
    """Test that all service health endpoints are accessible and respond correctly."""
    with httpx.Client(timeout=10.0) as client:
        for service in SERVICES:
            response = client.get(service["url"])
            
            assert response.status_code == 200, f"{service['name']} health check failed"
            data = response.json()
            assert data["status"] == "healthy", f"{service['name']} is not healthy"
            assert "service" in data, f"{service['name']} missing service name in response"


def test_services_on_correct_ports(docker_services):
    """Test that services are accessible on their assigned ports."""
    with httpx.Client(timeout=10.0) as client:
        for service in SERVICES:
            try:
                response = client.get(service["url"])
                assert response.status_code == 200, f"{service['name']} not accessible on port {service['port']}"
            except httpx.ConnectError:
                pytest.fail(f"{service['name']} is not listening on port {service['port']}")


def test_database_container_running(docker_services):
    """Test that the PostgreSQL database container is running."""
    result = subprocess.run(
        ["docker-compose", "ps", "--services", "--filter", "status=running"],
        capture_output=True,
        text=True,
        check=True
    )
    
    running_services = result.stdout.strip().split("\n")
    assert "db" in running_services, "PostgreSQL database container is not running"


def test_service_networking(docker_services):
    """Test that services can communicate via Docker network."""
    # Check that services are on the same network
    result = subprocess.run(
        ["docker", "network", "inspect", "cat-house-backend_cathouse-network"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Docker network 'cathouse-network' does not exist"
