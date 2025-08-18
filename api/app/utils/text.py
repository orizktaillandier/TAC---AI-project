"""
Utility functions for text processing.
"""
import re
import unicodedata
from typing import List, Dict, Any, Optional
import nltk

# Ensure nltk data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing unicode.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def detect_language(text: str) -> str:
    """
    Detect whether text is in French or English.
    
    Args:
        text: Text to analyze
        
    Returns:
        'fr' for French, 'en' for English
    """
    if not text or not isinstance(text, str):
        return "en"
    
    # Common French words
    french_markers = [
        "merci", "bonjour", "véhicule", "voiture", "concessionnaire", "depuis",
        "cela", "je", "vous", "nous", "ils", "elles", "cette", "ces", "comme",
        "pour", "avec", "sans", "dans", "sur", "sous", "chez", "voilà", "puis",
        "donc", "alors", "ensuite", "enfin", "maintenant", "toujours", "jamais",
        "souvent", "parfois", "peu", "beaucoup", "trop", "assez", "bien", "mal",
        "très", "plus", "moins", "aussi", "autant", "même", "autre", "chaque",
        "tout", "rien", "personne", "quelqu'un", "quelque", "quel", "quelle"
    ]
    
    # Check for French markers
    text_lower = text.lower()
    french_count = sum(1 for word in french_markers if f" {word} " in f" {text_lower} ")
    
    # Threshold for detection
    return "fr" if french_count >= 3 else "en"


def extract_contacts(text: str) -> str:
    """
    Extract contact name from text.
    
    Args:
        text: Text to extract contact from
        
    Returns:
        Contact name or empty string if not found
    """
    if not text or not isinstance(text, str):
        return ""
    
    lines = text.strip().split('\n')
    
    # Look for signatures after "Best regards", "Regards", etc.
    for i in range(len(lines) - 1):
        line = lines[i].strip().lower()
        if re.match(r'^(best regards|regards|merci|thanks|cordially|from:|envoyé par|de:)', line, re.IGNORECASE):
            next_line = lines[i + 1].strip()
            name_match = re.match(r'^[A-Z][a-z]+( [A-Z][a-z]+)+$', next_line)
            if name_match:
                return next_line
    
    # Look for greeting lines
    greet_match = re.search(r'^(hi|bonjour|hello|salut)[\s,:-]+([A-Z][a-z]+)', text.strip(), re.IGNORECASE | re.MULTILINE)
    if greet_match:
        candidate = greet_match.group(2)
        if not re.match(r'^(nous|client|dealer|photos?|images?|request|inventory)$', candidate, re.IGNORECASE):
            return candidate
    
    # Look for any name-like pattern
    match = re.search(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', text)
    if match and not re.match(r'^(nous|client|dealer|photos?|images?|request|inventory)$', match.group(1), re.IGNORECASE):
        return match.group(1)
    
    return ""


def extract_syndicators(text: str, approved_syndicators: List[str]) -> List[str]:
    """
    Extract syndicator names from text.
    
    Args:
        text: Text to extract syndicators from
        approved_syndicators: List of approved syndicator names
        
    Returns:
        List of extracted syndicator names
    """
    if not text or not isinstance(text, str) or not approved_syndicators:
        return []
    
    text_lower = text.lower()
    matches = set()
    
    for syndicator in approved_syndicators:
        if re.search(rf"\b{re.escape(syndicator.lower())}\b", text_lower):
            matches.add(syndicator.title())
    
    return list(matches)


def extract_image_flags(text: str) -> List[str]:
    """
    Extract image-related flags from text.
    
    Args:
        text: Text to extract flags from
        
    Returns:
        List of image-related flags
    """
    if not text or not isinstance(text, str):
        return []
    
    flags = []
    text_lower = text.lower()
    
    if "image" in text_lower or "photo" in text_lower or "picture" in text_lower:
        flags.append("image")
    
    if "certified" in text_lower:
        flags.append("certified")
    
    if "overwrite" in text_lower or "overwritten" in text_lower:
        flags.append("overwritten")
    
    return flags


def detect_stock_number(text: str) -> bool:
    """
    Detect if text contains a stock number.
    
    Args:
        text: Text to check
        
    Returns:
        True if stock number found, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    # Common stock number patterns
    stock_patterns = [
        r'\b[A-Z0-9]{6,}\b',  # 6+ alphanumeric characters
        r'\bSTK#\s*[A-Z0-9]+',  # STK# followed by alphanumeric
        r'\bSTOCK#\s*[A-Z0-9]+',  # STOCK# followed by alphanumeric
        r'\bSTOCK\s+NUMBER\s*[A-Z0-9]+',  # STOCK NUMBER followed by alphanumeric
        r'\bVIN\s*[A-Z0-9]+',  # VIN followed by alphanumeric
    ]
    
    for pattern in stock_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def preprocess_ticket(text: str, approved_syndicators: List[str] = None) -> Dict[str, Any]:
    """
    Preprocess a ticket text to extract various features.
    
    Args:
        text: Ticket text
        approved_syndicators: List of approved syndicator names
        
    Returns:
        Dictionary of extracted features
    """
    cleaned_text = clean_text(text)
    
    return {
        "message": cleaned_text,
        "contains_french": detect_language(cleaned_text) == "fr",
        "contains_stock_number": detect_stock_number(cleaned_text),
        "contacts_found": [extract_contacts(cleaned_text)],
        "dealers_found": extract_dealers(cleaned_text),
        "syndicators": extract_syndicators(cleaned_text, approved_syndicators or []),
        "image_flags": extract_image_flags(cleaned_text),
        "line_count": cleaned_text.count("\n") + 1
    }