"""
Validation utilities for the API.
"""
import json
import os
import re
from typing import Dict, List, Any, Optional, Set, Tuple

import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()


class ClassificationValidator:
    """Validator for ticket classifications."""
    
    def __init__(self, syndicators_path: str = None, dealer_mapping_path: str = None):
        """
        Initialize the validator.
        
        Args:
            syndicators_path: Path to syndicators CSV
            dealer_mapping_path: Path to dealer mapping CSV
        """
        self.syndicators_path = syndicators_path or settings.SYNDICATORS_CSV
        self.dealer_mapping_path = dealer_mapping_path or settings.DEALER_MAPPING_CSV
        
        # Load reference data
        self.syndicators = self._load_syndicators()
        self.approved_syndicators = {s.lower() for s in self.syndicators}
        self.dealer_mapping = self._load_dealer_mapping()
        
        # Valid categories and subcategories from settings
        self.valid_categories = set(settings.VALID_CATEGORIES)
        self.valid_subcategories = set(settings.VALID_SUBCATEGORIES)
        self.valid_inventory_types = set(settings.VALID_INVENTORY_TYPES)
    
    def _load_syndicators(self) -> List[str]:
        """
        Load syndicators from CSV.
        
        Returns:
            List of syndicator names
        """
        try:
            if os.path.exists(self.syndicators_path):
                df = pd.read_csv(self.syndicators_path)
                if "Syndicator" in df.columns:
                    return df["Syndicator"].dropna().tolist()
            logger.warning(f"Syndicators CSV not found or invalid: {self.syndicators_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading syndicators: {str(e)}")
            return []
    
    def _load_dealer_mapping(self) -> pd.DataFrame:
        """
        Load dealer mapping from CSV.
        
        Returns:
            DataFrame with dealer mapping
        """
        try:
            if os.path.exists(self.dealer_mapping_path):
                return pd.read_csv(self.dealer_mapping_path)
            logger.warning(f"Dealer mapping CSV not found: {self.dealer_mapping_path}")
            return pd.DataFrame(columns=["Rep Name", "Dealer Name", "Dealer ID"])
        except Exception as e:
            logger.error(f"Error loading dealer mapping: {str(e)}")
            return pd.DataFrame(columns=["Rep Name", "Dealer Name", "Dealer ID"])
    
    def validate_classification(
        self, classification: Dict[str, Any], ticket_text: str = ""
    ) -> Dict[str, str]:
        """
        Validate and normalize a classification.
        
        Args:
            classification: Classification to validate
            ticket_text: Original ticket text for fallback extraction
            
        Returns:
            Validated and normalized classification
        """
        # Initialize result with empty strings for all required fields
        result = {
            "contact": "",
            "dealer_name": "",
            "dealer_id": "",
            "rep": "",
            "category": "",
            "sub_category": "",
            "syndicator": "",
            "inventory_type": ""
        }
        
        # Update with values from classification
        for field in result.keys():
            if field in classification and classification[field]:
                result[field] = str(classification[field]).strip()
        
        # Validate category
        if result["category"] not in self.valid_categories:
            result["category"] = ""
        
        # Validate sub_category
        if result["sub_category"] not in self.valid_subcategories:
            result["sub_category"] = ""
        
        # Validate inventory_type
        if result["inventory_type"] not in self.valid_inventory_types:
            result["inventory_type"] = ""
        
        # Validate syndicator
        syndicator = result["syndicator"].lower()
        if syndicator and syndicator not in self.approved_syndicators:
            # Try to find a close match
            for s in self.approved_syndicators:
                if syndicator in s or s in syndicator:
                    result["syndicator"] = s.title()
                    break
            else:
                result["syndicator"] = ""
        elif syndicator in self.approved_syndicators:
            # Normalize case using the original list
            for s in self.syndicators:
                if s.lower() == syndicator:
                    result["syndicator"] = s
                    break
        
        # Verify dealer info if dealer_name is provided
        if result["dealer_name"] and not result["dealer_name"].lower().startswith("multiple"):
            dealer_info = self._lookup_dealer(result["dealer_name"])
            if dealer_info:
                result["dealer_name"] = dealer_info.get("dealer_name", result["dealer_name"])
                result["dealer_id"] = dealer_info.get("dealer_id", result["dealer_id"])
                # Only set rep if empty and available from mapping
                if not result["rep"] and dealer_info.get("rep"):
                    result["rep"] = dealer_info.get("rep")
        
        return result
    
    def _lookup_dealer(self, dealer_name: str) -> Dict[str, str]:
        """
        Look up dealer information from the mapping.
        
        Args:
            dealer_name: Dealer name to look up
            
        Returns:
            Dictionary with dealer_name, dealer_id, rep
        """
        if not dealer_name or not isinstance(dealer_name, str) or self.dealer_mapping.empty:
            return {"dealer_name": dealer_name.title() if dealer_name else ""}
        
        # Normalize the dealer name
        name_norm = self._normalize_dealer_name(dealer_name)
        
        try:
            # Add normalized names to the mapping
            self.dealer_mapping["Normalized Name"] = self.dealer_mapping["Dealer Name"].apply(
                self._normalize_dealer_name
            )
            
            # 1. Exact match
            exact = self.dealer_mapping[self.dealer_mapping["Normalized Name"] == name_norm]
            if not exact.empty:
                row = exact.iloc[0]
                return {
                    "dealer_name": row["Dealer Name"],
                    "dealer_id": str(row["Dealer ID"]),
                    "rep": row["Rep Name"]
                }
            
            # 2. Substring match
            for idx, row in self.dealer_mapping.iterrows():
                normalized = row["Normalized Name"]
                if name_norm in normalized or normalized in name_norm:
                    return {
                        "dealer_name": row["Dealer Name"],
                        "dealer_id": str(row["Dealer ID"]),
                        "rep": row["Rep Name"]
                    }
            
            # 3. Default to the original name if no match
            return {"dealer_name": dealer_name.title()}
            
        except Exception as e:
            logger.error(f"Error looking up dealer: {str(e)}")
            return {"dealer_name": dealer_name.title()}
    
    def _normalize_dealer_name(self, name: str) -> str:
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


def validate_ticket_id(ticket_id: str) -> bool:
    """
    Validate a ticket ID.
    
    Args:
        ticket_id: Ticket ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not ticket_id:
        return False
    
    # Ticket IDs are typically numeric or alphanumeric
    return bool(re.match(r'^[a-zA-Z0-9-]+$', ticket_id))


def validate_json_schema(data: Dict[str, Any], schema_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON data against a schema.
    
    Args:
        data: Data to validate
        schema_path: Path to JSON schema
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import jsonschema
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        jsonschema.validate(data, schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"