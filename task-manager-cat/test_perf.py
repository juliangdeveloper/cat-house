import asyncio
import asyncpg
import time
import random
from datetime import datetime, timedelta

async def test_performance():
    # Connect to database
    conn = await asyncpg.connect("postgresql://taskuser:taskpass@postgres:5432/taskmanager_dev")
    
    # Create test user
    user_id = "test-perf-1000-tasks"
    
    # Clean up existing data
    await conn.execute("DELETE FROM tasks WHERE user_id = $1", user_id)
    
    # Insert 1000 tasks
    print("Inserting 1000 tasks...")
    statuses = ["pending", "in_progress", "completed"]
    for i in range(1000):
        status = random.choice(statuses)
        due_date = None
        if random.random() > 0.5:
            days_offset = random.randint(-10, 10)
            due_date = datetime.now() + timedelta(days=days_offset)
        
        await conn.execute("""
            INSERT INTO tasks (user_id, title, status, due_date)
            VALUES ($1, $2, $3, $4)
        """, user_id, f"Task {i+1}", status, due_date)
    
    print("1000 tasks inserted. Testing statistics calculation...")
    
    # Import stats service
    import sys
    sys.path.insert(0, "/app")
    from app.services.stats_service import get_task_statistics
    
    # Measure performance
    start = time.time()
    stats = await get_task_statistics(user_id, conn)
    end = time.time()
    
    elapsed_ms = (end - start) * 1000
    
    print(f"\nStatistics calculated in {elapsed_ms:.2f}ms")
    print(f"Results: {stats}")
    
    # Cleanup
    await conn.execute("DELETE FROM tasks WHERE user_id = $1", user_id)
    await conn.close()
    
    print(f"\nPerformance target: < 200ms")
    print(f"Actual: {elapsed_ms:.2f}ms")
    if elapsed_ms < 200:
        print(" Performance target met!")
    else:
        print(" Performance target not met")

asyncio.run(test_performance())
