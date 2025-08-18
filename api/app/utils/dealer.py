"""
Utility functions for dealer name extraction and normalization.
"""
import re
import unicodedata
from typing import List, Dict, Optional


def normalize_dealer_name(name: str) -> str:
    """
    Normalize a dealer name for comparison.
    
    Args:
        name: Dealer name
        
    Returns:
        Normalized dealer name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove leading/trailing whitespace
    name = name.strip()
    
    # Remove punctuation and normalize whitespace
    name = name.replace('.', '').replace('-', ' ').replace('  ', ' ')
    
    # Remove city suffixes
    for loc in ["laval", "montreal", "victoria", "toronto", "vancouver", "ottawa"]:
        name = re.sub(rf"\b{loc}\b", "", name)
    
    # Remove legal suffixes
    legal_suffixes = [
        "ltd", "limited", "inc", "corporation", "corp", "llc", "sales", "auto", 
        "group", "co", "company", "ltee", "autos", "dealership", "sales limited", 
        "société", "dealer", "ltd."
    ]
    for suffix in legal_suffixes:
        name = re.sub(rf"\b{suffix}\b", "", name)
    
    # Normalize whitespace
    name = re.sub(r"\s+", " ", name)
    
    return name.strip()


def extract_dealers(text: str) -> List[str]:
    """
    Extract dealer names from text.
    
    Args:
        text: Text to extract dealer names from
        
    Returns:
        List of extracted dealer names
    """
    if not text or not isinstance(text, str):
        return []
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    extracted = []
    
    # 1. "dealer below" logic: next non-address, multi-word line (at least 3 words)
    for i, line in enumerate(lines):
        if "dealer below" in line.lower():
            for l2 in lines[i+1:i+5]:
                if len(l2.split()) >= 3 and not any(x in l2.lower() for x in [
                    "highway", "qc", "on", "ca", "address", "regards", "best", 
                    "services", "support", "woodbridge", "t5"
                ]):
                    extracted.append(l2)
                    break
            if extracted:
                break
    
    # 2. Fallback: any line >2 words, not address, not signature
    if not extracted:
        for line in lines:
            if (
                len(line.split()) > 2 and
                not any(x in line.lower() for x in [
                    "highway", "qc", "on", "ca", "address", "regards", "best", 
                    "services", "support", "woodbridge"
                ])
            ):
                extracted.append(line)
                break
    
    # 3. Fallback: brand-based detection
    if not extracted:
        brands = re.findall(
            r"\b(?:mazda|toyota|honda|chevrolet|hyundai|genesis|ford|ram|gmc|acura|jeep"
            r"|buick|nissan|volvo|subaru|volkswagen|kia|mitsubishi|infiniti|lexus"
            r"|cadillac|dodge|mini|jaguar|land rover|bmw|mercedes|audi|porsche|tesla)[\w &\-']*",
            text.lower()
        )
        for d in brands:
            if d.strip():
                extracted.append(d.strip().title())
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(extracted))


def extract_dealers_from_subject(subject: str) -> List[str]:
    """
    Extract dealer names from subject line.
    
    Args:
        subject: Subject line
        
    Returns:
        List of extracted dealer names
    """
    if not subject or not isinstance(subject, str):
        return []
    
    brands = [
        "Mazda", "Toyota", "Honda", "Chevrolet", "Hyundai", "Genesis", "Ford", "Ram",
        "GMC", "Acura", "Jeep", "Buick", "Nissan", "Volvo", "Subaru", "Volkswagen",
        "Kia", "Mitsubishi", "Infiniti", "Lexus", "Cadillac", "Dodge", "Mini",
        "Jaguar", "Land Rover", "BMW", "Mercedes", "Audi", "Porsche", "Tesla"
    ]
    
    candidates = []
    
    # Match 'Brand City', 'City Brand', and 'Brand - City'
    for brand in brands:
        # Brand followed by city/location
        matches = re.findall(rf"\b{brand}\s+[A-Za-z0-9\-éèêàâîôùçëïü']+", subject, re.IGNORECASE)
        # City/location followed by brand
        matches += re.findall(rf"\b[A-Za-z0-9\-éèêàâîôùçëïü']+\s+{brand}\b", subject, re.IGNORECASE)
        # Brand - City format
        matches += re.findall(rf"\b{brand}\s*-\s*[A-Za-z0-9\-éèêàâîôùçëïü']+", subject, re.IGNORECASE)
        
        candidates.extend(matches)
    
    # Remove duplicates and clean up
    return list(dict.fromkeys([c.strip().replace(" - ", " ") for c in candidates]))


def lookup_dealer_by_name(name: str, dealer_mapping=None) -> Dict[str, str]:
    """
    Look up dealer information by name.
    
    Args:
        name: Dealer name
        dealer_mapping: Dataframe with dealer mapping
        
    Returns:
        Dictionary with dealer_name, dealer_id, rep
    """
    if not name or not isinstance(name, str) or not dealer_mapping is not None:
        return {"dealer_name": name.title() if name else ""}
    
    # Normalize the dealer name
    name_norm = normalize_dealer_name(name)
    
    try:
        # Add normalized names to the mapping
        dealer_mapping["Normalized Name"] = dealer_mapping["Dealer Name"].apply(normalize_dealer_name)
        
        # 1. Exact match
        exact = dealer_mapping[dealer_mapping["Normalized Name"] == name_norm]
        if not exact.empty:
            row = exact.iloc[0]
            return {
                "dealer_name": row["Dealer Name"].title(),
                "dealer_id": str(row["Dealer ID"]),
                "rep": row["Rep Name"]
            }
        
        # 2. Fuzzy match (check if one is contained in the other)
        for idx, row in dealer_mapping.iterrows():
            normalized = row["Normalized Name"]
            if name_norm in normalized or normalized in name_norm:
                return {
                    "dealer_name": row["Dealer Name"].title(),
                    "dealer_id": str(row["Dealer ID"]),
                    "rep": row["Rep Name"]
                }
        
        # 3. Default to the original name if no match
        return {"dealer_name": name.title()}
        
    except Exception:
        # If anything goes wrong, just return the original name
        return {"dealer_name": name.title()}