import asyncio
from datetime import datetime
from src.agents.controller import AsyncRCAController, LogEntry

async def test_controller():
    print("Initializing Controller...")
    controller = AsyncRCAController()
    
    # Start controller in background task
    print("Starting Controller...")
    asyncio.create_task(controller.start())
    
    # Give it a moment to initialize loops
    await asyncio.sleep(1)
    
    # Submit a log
    log = LogEntry(
        timestamp=datetime.now(),
        service="payment-db",
        level="ERROR",
        latency=250.0,
        message="Connection timeout acquiring lock",
        metadata={"error_count": 1}
    )
    
    print("Submitting log...")
    await controller.submit_log(log)
    
    # Wait for ingestion details
    print("Waiting for ingestion...")
    for _ in range(10):
        if controller.stats['processed'] > 0:
            print(f"Success! Stats: {controller.stats}")
            break
        await asyncio.sleep(0.5)
        
    if controller.stats['processed'] == 0:
        print("Failed to process log in time.")
        exit(1)
        
    print("Stopping Controller...")
    controller.stop()
    await asyncio.sleep(1) # Allow tasks to exit
    print("Controller Smoke Test Passed.")

if __name__ == "__main__":
    asyncio.run(test_controller())
