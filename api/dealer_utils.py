import re
import pandas as pd
from difflib import get_close_matches

def normalize_dealer_name(name):
    """Normalize dealer name for consistent matching"""
    name = name.lower().strip()
    name = name.replace('.', '').replace('-', ' ').replace('  ', ' ')
    # Remove city suffixes
    for loc in ["laval", "montreal", "victoria", "toronto"]:
        name = re.sub(rf"\b{loc}\b", "", name)
    # Remove corp/legal suffixes
    name = re.sub(r"\b(ltd|limited|inc|corporation|corp|llc|sales|auto|group|co|company|ltee|autos|dealership|sales limited|société|dealer|ltd.)\b", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def lookup_dealer_by_name(name, csv_path="../data/rep_dealer_mapping.csv"):
    """Look up dealer information by name with fuzzy matching"""
    name = (name or "").strip()
    if not name:
        return {"dealer_name": "", "dealer_id": "", "rep": ""}
    
    try:
        df = pd.read_csv(csv_path)
        
        # Keep original dealer names for exact return
        df["Original_Dealer_Name"] = df["Dealer Name"].astype(str)
        
        # Create normalized column for matching only
        df["Normalized_Dealer_Name"] = df["Dealer Name"].astype(str).map(normalize_dealer_name)
        
        name_norm = normalize_dealer_name(name)
        
        # Exact match on normalized names
        exact_match = df[df["Normalized_Dealer_Name"] == name_norm]
        if not exact_match.empty:
            row = exact_match.iloc[0]
            return {
                "dealer_name": row["Original_Dealer_Name"],  # ✅ Use exact CSV value
                "dealer_id": str(row["Dealer ID"]),
                "rep": row["Rep Name"]
            }
        
        # Fuzzy match on normalized names
        close = get_close_matches(name_norm, df["Normalized_Dealer_Name"], n=1, cutoff=0.5)
        if close:
            match_row = df[df["Normalized_Dealer_Name"] == close[0]].iloc[0]
            return {
                "dealer_name": match_row["Original_Dealer_Name"],  # ✅ Use exact CSV value
                "dealer_id": str(match_row["Dealer ID"]),
                "rep": match_row["Rep Name"]
            }
            
        # Substring match on normalized names
        for i, normalized_name in enumerate(df["Normalized_Dealer_Name"]):
            if name_norm in normalized_name or normalized_name in name_norm:
                row = df.iloc[i]
                return {
                    "dealer_name": row["Original_Dealer_Name"],  # ✅ Use exact CSV value
                    "dealer_id": str(row["Dealer ID"]),
                    "rep": row["Rep Name"]
                }
                
    except Exception as e:
        print(f"Dealer lookup error: {e}")
    
    # Fallback: return input name without modification
    return {"dealer_name": name, "dealer_id": "", "rep": ""}


def extract_dealers_from_subject(subject):
    """Look for likely dealer names in subject: [Brand] [City] - FIXED VERSION"""
    brands = [
        "Mazda", "Toyota", "Honda", "Chevrolet", "Hyundai", "Genesis", "Ford", "Ram", "GMC",
        "Acura", "Jeep", "Buick", "Nissan", "Volvo", "Subaru", "Volkswagen", "Kia", "Mitsubishi",
        "Infiniti", "Lexus", "Cadillac", "Dodge", "Mini", "Jaguar", "Land Rover", "BMW", "Mercedes",
        "Audi", "Porsche", "Tesla"
    ]
    
    candidates = []
    for brand in brands:
        # Pattern 1: [Word] [Brand] - e.g., "Fines Ford", "Downtown Toyota"
        # More restrictive: only match one word before brand
        matches = re.findall(rf"\b([A-Za-z]+)\s+{brand}\b", subject, re.IGNORECASE)
        for match in matches:
            dealer_name = f"{match} {brand}"
            # Filter out bad words that shouldn't be part of dealer names
            if not any(bad_word in match.lower() for bad_word in [
                'assistance', 'request', 'via', 'admin', 'syndication', 'for', 'the', 'and'
            ]):
                candidates.append(dealer_name)
        
        # Pattern 2: [Brand] [Word] - e.g., "Ford Lincoln", "Toyota Downtown"  
        matches = re.findall(rf"\b{brand}\s+([A-Za-z]+)\b", subject, re.IGNORECASE)
        for match in matches:
            dealer_name = f"{brand} {match}"
            # Filter out bad words
            if not any(bad_word in match.lower() for bad_word in [
                'assistance', 'request', 'via', 'admin', 'syndication', 'for', 'the', 'and'
            ]):
                candidates.append(dealer_name)
        
        # Pattern 3: [Brand] - [Word] - e.g., "Ford - Lincoln"
        matches = re.findall(rf"\b{brand}\s*-\s*([A-Za-z]+)\b", subject, re.IGNORECASE)
        for match in matches:
            dealer_name = f"{brand} {match}"
            if not any(bad_word in match.lower() for bad_word in [
                'assistance', 'request', 'via', 'admin', 'syndication', 'for', 'the', 'and'
            ]):
                candidates.append(dealer_name)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(candidates))

def extract_syndicators(text):
    """Extract syndicator names from text"""
    try:
        # Load valid syndicators from CSV
        for csv_path in ["../data/syndicators.csv", "syndicators.csv", "data/syndicators.csv"]:
            try:
                df = pd.read_csv(csv_path)
                approved_syndicators = set(s.lower() for s in df["Syndicator"].dropna())
                break
            except:
                continue
        else:
            # Fallback syndicators if CSV not found
            approved_syndicators = {"kijiji", "autotrader", "cars.com", "trader", "accutrade"}
    except:
        approved_syndicators = {"kijiji", "autotrader", "cars.com", "trader", "accutrade"}
    
    text_lower = text.lower()
    matches = set()
    for syndicator in approved_syndicators:
        if re.search(rf"\b{re.escape(syndicator)}\b", text_lower):
            matches.add(syndicator.title())
    return list(matches)

def extract_image_flags(text):
    """Extract image-related flags from text"""
    flags = []
    lower = text.lower()
    if "image" in lower:
        flags.append("image")
    if "certified" in lower:
        flags.append("certified")
    if "overwrite" in lower or "overwritten" in lower:
        flags.append("overwritten")
    return flags

def detect_edge_case(message: str, zoho_fields=None):
    """Detect specific edge cases in ticket messages"""
    text = message.lower()
    synd = (zoho_fields or {}).get("syndicator", "").lower()
    
    if ("trader" in text or synd == "trader") and "used" in text and "new" in text:
        return "E55"
    if re.search(r"(stock number|stock#).*?[<>\"']", text):
        return "E44"
    if "firewall" in text:
        return "E74"
    if "partial" in text and "trim" in text and "inventory+" in text and "omni" in text:
        return "E77"
    return ""

def preprocess_ticket(text):
    """Preprocess ticket text and extract basic metadata"""
    return {
        "message": text,
        "contains_french": detect_language(text) == "fr",
        "contains_stock_number": detect_stock_number(text),
        "contacts_found": [extract_contacts(text)],
        "dealers_found": extract_dealers(text),
        "syndicators": extract_syndicators(text),
        "image_flags": extract_image_flags(text),
        "line_count": text.count("\n") + 1
    }

def detect_language(text):
    """Detect if text is French or English"""
    return "fr" if re.search(r"\b(merci|bonjour|véhicule|images|depuis)\b", text.lower()) else "en"

def detect_stock_number(text):
    """Detect if text contains stock numbers"""
    return bool(re.search(r"\b[A-Z0-9]{6,}\b", text))

def extract_contacts(text):
    """Extract contact names from text"""
    lines = text.strip().split('\n')
    for i in range(len(lines) - 1):
        line = lines[i].strip().lower()
        if re.match(r'^(best regards|regards|merci|thanks|cordially|from:|envoyé par|de:)', line, re.IGNORECASE):
            next_line = lines[i + 1].strip()
            name_match = re.match(r'^[A-Z][a-z]+( [A-Z][a-z]+)+$', next_line)
            if name_match:
                return next_line
                
    greet_match = re.search(r'^(hi|bonjour|hello|salut)[\s,:-]+([A-Z][a-z]+)', text.strip(), re.IGNORECASE | re.MULTILINE)
    if greet_match:
        candidate = greet_match.group(2)
        if not re.match(r'^(nous|client|dealer|photos?|images?|request|inventory)$', candidate, re.IGNORECASE):
            return candidate
            
    match = re.search(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', text)
    if match and not re.match(r'^(nous|client|dealer|photos?|images?|request|inventory)$', match.group(1), re.IGNORECASE):
        return match.group(1)
    return ""