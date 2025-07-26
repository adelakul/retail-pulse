"""
Column Mapper - Smart Column Detection Engine
Intelligently maps dataset columns to standardized field names using fuzzy matching and patterns.
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import pandas as pd
from dataclasses import dataclass


@dataclass
class ColumnMappingResult:
    """Result of column mapping operation"""
    mapped_columns: Dict[str, str]  # standardized_name -> actual_column_name
    confidence_scores: Dict[str, float]  # standardized_name -> confidence (0-1)
    unmapped_columns: List[str]  # columns that couldn't be mapped
    missing_required: List[str]  # required columns that weren't found


class ColumnMapper:
    """
    Smart column mapping engine that can identify columns across different datasets
    using fuzzy matching, pattern recognition, and configurable rules.
    """
    
    def __init__(self, config_path: str):
        """Initialize with mapping configuration"""
        self.config = self._load_config(config_path)
        self.field_mappings = self.config.get('field_mappings', {})
        self.required_fields = self.config.get('required_fields', [])
        self.optional_fields = self.config.get('optional_fields', [])
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load mapping configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def map_columns(self, df: pd.DataFrame, min_confidence: float = 0.6) -> ColumnMappingResult:
        """
        Map DataFrame columns to standardized field names
        
        Args:
            df: Input DataFrame
            min_confidence: Minimum confidence score to accept a mapping
            
        Returns:
            ColumnMappingResult with mapping details
        """
        available_columns = list(df.columns)
        mapped_columns = {}
        confidence_scores = {}
        unmapped_columns = available_columns.copy()
        
        # Process each standardized field
        all_fields = list(self.field_mappings.keys())
        
        for std_field in all_fields:
            best_match, confidence = self._find_best_match(
                std_field, available_columns, min_confidence
            )
            
            if best_match:
                mapped_columns[std_field] = best_match
                confidence_scores[std_field] = confidence
                if best_match in unmapped_columns:
                    unmapped_columns.remove(best_match)
        
        # Check for missing required fields
        missing_required = [
            field for field in self.required_fields 
            if field not in mapped_columns
        ]
        
        return ColumnMappingResult(
            mapped_columns=mapped_columns,
            confidence_scores=confidence_scores,
            unmapped_columns=unmapped_columns,
            missing_required=missing_required
        )
    
    def _find_best_match(self, std_field: str, available_columns: List[str], 
                        min_confidence: float) -> Tuple[Optional[str], float]:
        """
        Find the best matching column for a standardized field
        
        Args:
            std_field: Standardized field name to match
            available_columns: List of available column names
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (best_match_column, confidence_score)
        """
        field_config = self.field_mappings.get(std_field, {})
        best_match = None
        best_confidence = 0.0
        
        for column in available_columns:
            confidence = self._calculate_match_confidence(
                std_field, column, field_config
            )
            
            if confidence > best_confidence and confidence >= min_confidence:
                best_match = column
                best_confidence = confidence
        
        return best_match, best_confidence
    
    def _calculate_match_confidence(self, std_field: str, column: str, 
                                  field_config: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a potential column match
        
        Args:
            std_field: Standardized field name
            column: Actual column name to evaluate
            field_config: Configuration for this field
            
        Returns:
            Confidence score between 0 and 1
        """
        column_lower = column.lower().strip()
        scores = []
        
        # 1. Exact match with aliases
        aliases = field_config.get('aliases', [])
        if column_lower in [alias.lower() for alias in aliases]:
            return 1.0
        
        # 2. Fuzzy string matching with aliases
        for alias in aliases:
            similarity = SequenceMatcher(None, column_lower, alias.lower()).ratio()
            scores.append(similarity * 0.9)  # Slightly lower weight for fuzzy
        
        # 3. Pattern matching
        patterns = field_config.get('patterns', [])
        for pattern in patterns:
            if re.search(pattern, column_lower, re.IGNORECASE):
                scores.append(0.85)
        
        # 4. Keyword matching
        keywords = field_config.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in column_lower:
                scores.append(0.7)
        
        # 5. Contains standardized field name
        if std_field.lower() in column_lower:
            scores.append(0.6)
        
        return max(scores) if scores else 0.0
    
    def get_mapped_dataframe(self, df: pd.DataFrame, 
                           mapping_result: ColumnMappingResult) -> pd.DataFrame:
        """
        Create a new DataFrame with standardized column names
        
        Args:
            df: Original DataFrame
            mapping_result: Result from map_columns()
            
        Returns:
            DataFrame with standardized column names
        """
        # Create column rename mapping (actual_name -> standardized_name)
        rename_mapping = {
            actual_col: std_field 
            for std_field, actual_col in mapping_result.mapped_columns.items()
        }
        
        # Select only mapped columns and rename them
        mapped_df = df[list(rename_mapping.keys())].copy()
        mapped_df = mapped_df.rename(columns=rename_mapping)
        
        return mapped_df
    
    def validate_mapping(self, mapping_result: ColumnMappingResult, 
                        strict: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate the mapping result
        
        Args:
            mapping_result: Result from map_columns()
            strict: If True, all required fields must be mapped
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for missing required fields
        if mapping_result.missing_required:
            issues.append(f"Missing required fields: {mapping_result.missing_required}")
        
        # Check confidence scores
        low_confidence = [
            f"{field} ({score:.2f})" 
            for field, score in mapping_result.confidence_scores.items() 
            if score < 0.8
        ]
        if low_confidence:
            issues.append(f"Low confidence mappings: {low_confidence}")
        
        # Determine if valid
        is_valid = True
        if strict and mapping_result.missing_required:
            is_valid = False
        
        return is_valid, issues
    
    def print_mapping_summary(self, mapping_result: ColumnMappingResult):
        """Print a human-readable summary of the mapping result"""
        print("🔄 COLUMN MAPPING SUMMARY")
        print("=" * 50)
        
        print(f"\n✅ MAPPED COLUMNS ({len(mapping_result.mapped_columns)}):")
        for std_field, actual_col in mapping_result.mapped_columns.items():
            confidence = mapping_result.confidence_scores[std_field]
            status = "🎯" if confidence >= 0.9 else "⚠️" if confidence >= 0.7 else "❓"
            print(f"  {status} {std_field:<20} → {actual_col:<25} ({confidence:.2f})")
        
        if mapping_result.missing_required:
            print(f"\n❌ MISSING REQUIRED ({len(mapping_result.missing_required)}):")
            for field in mapping_result.missing_required:
                print(f"  • {field}")
        
        if mapping_result.unmapped_columns:
            print(f"\n❓ UNMAPPED COLUMNS ({len(mapping_result.unmapped_columns)}):")
            for col in mapping_result.unmapped_columns:
                print(f"  • {col}")
        
        print("\n" + "=" * 50)


# Usage example and testing functions
def test_column_mapper():
    """Test the column mapper with sample data"""
    
    # Create sample DataFrame with various column naming conventions
    sample_data = {
        'Product_Name': ['Widget A', 'Widget B', 'Widget C'],
        'sales_amount': [100.50, 200.75, 150.25],
        'order_date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'customer_id': [1001, 1002, 1003],
        'qty_sold': [5, 10, 7],
        'store_location': ['NYC', 'LA', 'Chicago'],
        'random_column': ['A', 'B', 'C']
    }
    
    df = pd.DataFrame(sample_data)
    
    print("📊 ORIGINAL DATAFRAME:")
    print(df.head())
    print(f"\nColumns: {list(df.columns)}")
    
    # Test mapping (assuming config file exists)
    try:
        mapper = ColumnMapper('configs/sales_mapping_config.json')
        result = mapper.map_columns(df)
        
        mapper.print_mapping_summary(result)
        
        # Get mapped DataFrame
        mapped_df = mapper.get_mapped_dataframe(df, result)
        print("\n📋 MAPPED DATAFRAME:")
        print(mapped_df.head())
        
        # Validate mapping
        is_valid, issues = mapper.validate_mapping(result)
        print(f"\n✓ Mapping Valid: {is_valid}")
        if issues:
            print("Issues:", issues)
            
    except FileNotFoundError as e:
        print(f"⚠️ Config file not found: {e}")
        print("Please create the configuration file first.")


if __name__ == "__main__":
    test_column_mapper()