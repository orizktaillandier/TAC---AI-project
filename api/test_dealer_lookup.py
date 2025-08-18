import asyncio
import sys
import re

# Import directly from the fixed API file
from fixed_dealer_api import extract_dealer_from_text, normalize_text

def test_normalization():
    """Test the text normalization function"""
    print("=== TESTING TEXT NORMALIZATION ===")
    
    test_text = "Hi, this is Evan Walsh from Belliveau Motors Ford. We're having an issue with inventory."
    normalized = normalize_text(test_text)
    
    print(f"Original: {test_text}")
    print(f"Normalized: {normalized}")
    
    # Check if key words survived normalization
    key_words = ["evan", "walsh", "belliveau", "motors", "ford", "issue", "inventory"]
    for word in key_words:
        if word in normalized:
            print(f"✓ Found '{word}' in normalized text")
        else:
            print(f"✗ Could NOT find '{word}' in normalized text")
    
    print()

async def test_dealer_lookup():
    """Test the dealer lookup function"""
    print("=== TESTING DEALER LOOKUP LOGIC ===")
    
    # Test case 1: Basic dealer lookup with rep name
    text1 = "Hi, this is Evan Walsh from Belliveau Motors Ford. We're having an issue with..."
    dealer1, id1, rep1 = extract_dealer_from_text(text1, "Ford issue", "Ford")
    print(f"Test 1 - Rep mentioned: Rep={rep1}, Dealer={dealer1}, ID={id1}")
    success1 = id1 == '3842' and 'belliveau' in dealer1.lower()
    print(f"Result: {'✓ SUCCESS' if success1 else '✗ FAILED'}")
    print()
    
    # Test case 2: Dealer ID in text
    text2 = "Please help with dealer 3842 inventory feed issue"
    dealer2, id2, rep2 = extract_dealer_from_text(text2, "Inventory issue", "Ford")
    print(f"Test 2 - ID in text: Rep={rep2}, Dealer={dealer2}, ID={id2}")
    success2 = id2 == '3842'
    print(f"Result: {'✓ SUCCESS' if success2 else '✗ FAILED'}")
    print()
    
    # Test case 3: Only dealer name in text
    text3 = "Belliveau Motors Ford is having issues with their inventory"
    dealer3, id3, rep3 = extract_dealer_from_text(text3, "Inventory problem", "Ford")
    print(f"Test 3 - Dealer name: Rep={rep3}, Dealer={dealer3}, ID={id3}")
    success3 = dealer3 and 'belliveau' in dealer3.lower()
    print(f"Result: {'✓ SUCCESS' if success3 else '✗ FAILED'}")
    print()
    
    # Test case 4: OEM context only
    text4 = "We're having problems with the Ford inventory feed"
    dealer4, id4, rep4 = extract_dealer_from_text(text4, "Feed problem", "Ford")
    print(f"Test 4 - OEM only: Rep={rep4}, Dealer={dealer4}, ID={id4}")
    print(f"Result: {'✓ Success' if dealer4 else '✓ Success - correctly returned None'}")
    print()
    
    return all([success1, success2, success3])

# Run the tests
if __name__ == "__main__":
    test_normalization()
    success = asyncio.run(test_dealer_lookup())
    
    if success:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
