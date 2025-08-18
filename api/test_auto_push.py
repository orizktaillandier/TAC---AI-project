import asyncio
import httpx

async def test_auto_push(ticket_id="319204000300044224"):
    """Test auto-push functionality with a specific ticket."""
    print(f"=== TESTING AUTO-PUSH WITH TICKET {ticket_id} ===")
    
    url = "http://localhost:8090/api/v1/classify"
    payload = {
        "ticket_id": ticket_id,
        "auto_push": True
    }
    
    print(f"Sending request to {url} with auto_push=True")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Classification: {result.get('classification')}")
                print(f"Pushed: {result.get('pushed')}")
                print(f"Push result: {result.get('push_result')}")
                return result
            else:
                print(f"Error: {response.text}")
                return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

async def test_multiple_tickets():
    """Test a batch of tickets to verify reliability."""
    # Replace with actual ticket IDs from your system
    test_tickets = [
        "319204000300044224",  # Your test case
        # Add more ticket IDs here
    ]
    
    results = []
    for ticket_id in test_tickets:
        result = await test_auto_push(ticket_id)
        results.append(result)
        print("=" * 50)
    
    # Print summary
    print("\\n=== TEST SUMMARY ===")
    for i, result in enumerate(results):
        if result:
            classification = result.get('classification', {})
            print(f"Ticket {i+1}: {test_tickets[i]}")
            print(f"  Dealer: {classification.get('dealer_name')} (ID: {classification.get('dealer_id')})")
            print(f"  Rep: {classification.get('rep')}")
            print(f"  Success: {'Yes' if result.get('pushed') else 'No'}")
            print()

# Run the tests
if __name__ == "__main__":
    asyncio.run(test_multiple_tickets())
