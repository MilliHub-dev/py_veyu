"""
Service mapping configuration and processor for dealership services.

This module provides centralized service mapping between frontend service selections
and backend dealership boolean fields, with support for case-insensitive matching
and validation.
"""

import logging
from typing import Dict, List, Set, Tuple
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Centralized service mapping configuration
SERVICE_MAPPING = {
    # Core boolean field mappings - each key maps to a dealership model field
    'offers_purchase': [
        'Car Sale', 'Car Sales', 'Vehicle Sales', 'Vehicle Sale',
        'Auto Sales', 'Automobile Sales', 'Car Selling', 'Vehicle Selling'
    ],
    'offers_rental': [
        'Car Rental', 'Car Leasing', 'Vehicle Rental', 'Vehicle Leasing',
        'Auto Rental', 'Automobile Rental', 'Car Hire', 'Vehicle Hire'
    ],
    'offers_drivers': [
        'Drivers', 'Driver Services', 'Chauffeur Services', 'Driver Service',
        'Chauffeur Service', 'Professional Drivers', 'Driving Services'
    ],
    'offers_trade_in': [
        'Trade-In Services', 'Trade In', 'Vehicle Trade-In', 'Car Trade-In',
        'Trade-in Service', 'Vehicle Trade In', 'Car Trade In', 'Sell-Your-Car'
    ],
    
    # Extended services (for future expansion) - stored in extended_services field
    'extended_services': [
        'Vehicle Financing', 'Car Financing', 'Auto Financing',
        'Vehicle Inspection', 'Car Inspection', 'Auto Inspection',
        'Extended Warranty', 'Vehicle Warranty', 'Car Warranty',
        'Vehicle Insurance', 'Car Insurance', 'Auto Insurance',
        'Vehicle Maintenance', 'Car Maintenance', 'Auto Maintenance',
        'Parts & Accessories', 'Auto Parts', 'Vehicle Parts',
        'Vehicle Delivery', 'Car Delivery', 'Auto Delivery',
        'Test Drive Services', 'Test Drive', 'Vehicle Test Drive',
        'Vehicle Registration', 'Car Registration', 'Auto Registration',
        'Export Services', 'Vehicle Export', 'Car Export',
        'Aircraft Sales & Leasing', 'Aircraft Sales', 'Aircraft Leasing',
        'Boat Sales & Leasing', 'Boat Sales', 'Boat Leasing',
        'UAV/Drone Sales', 'Drone Sales', 'UAV Sales',
        'Motorbike Sales & Leasing', 'Motorbike Sales', 'Motorcycle Sales'
    ]
}


class DealershipServiceProcessor:
    """
    Processes dealership service selections and maps them to appropriate model fields.
    
    Provides case-insensitive service name matching, validation, and mapping
    to both boolean fields and extended services.
    """
    
    def __init__(self):
        """Initialize the processor with normalized service mappings."""
        self._normalized_mapping = self._create_normalized_mapping()
        self._all_services = self._get_all_services()
    
    def _create_normalized_mapping(self) -> Dict[str, str]:
        """
        Create a normalized mapping from service names to field names.
        
        Returns:
            Dict mapping lowercase service names to their corresponding field names.
        """
        normalized = {}
        for field_name, service_names in SERVICE_MAPPING.items():
            for service_name in service_names:
                normalized[service_name.lower().strip()] = field_name
        return normalized
    
    def _get_all_services(self) -> Set[str]:
        """
        Get all available service names.
        
        Returns:
            Set of all service names across all categories.
        """
        all_services = set()
        for service_names in SERVICE_MAPPING.values():
            all_services.update(service_names)
        return all_services
    
    def _normalize_service_name(self, service_name: str) -> str:
        """
        Normalize a service name for case-insensitive matching.
        
        Args:
            service_name: The service name to normalize.
            
        Returns:
            Normalized service name (lowercase, stripped).
        """
        return service_name.lower().strip()
    
    def _find_field_for_service(self, service_name: str) -> str:
        """
        Find the field name for a given service name.
        
        Args:
            service_name: The service name to look up.
            
        Returns:
            Field name if found, None otherwise.
        """
        normalized_name = self._normalize_service_name(service_name)
        return self._normalized_mapping.get(normalized_name)
    
    def _suggest_similar_services(self, service_name: str, max_suggestions: int = 3) -> List[str]:
        """
        Suggest similar service names for typos or close matches.
        
        Args:
            service_name: The service name to find suggestions for.
            max_suggestions: Maximum number of suggestions to return.
            
        Returns:
            List of suggested service names.
        """
        normalized_input = self._normalize_service_name(service_name)
        suggestions = []
        
        # Enhanced similarity matching with multiple strategies
        scored_suggestions = []
        
        for service in self._all_services:
            normalized_service = self._normalize_service_name(service)
            score = 0
            
            # Exact substring match (highest priority)
            if normalized_input in normalized_service or normalized_service in normalized_input:
                score = 0.9
            # Word-based matching for compound service names
            elif self._has_common_words(normalized_input, normalized_service):
                score = 0.8
            # Character similarity for typos
            elif self._calculate_similarity(normalized_input, normalized_service) > 0.6:
                score = self._calculate_similarity(normalized_input, normalized_service)
            # Partial word matching (e.g., "sale" matches "Car Sale")
            elif any(word in normalized_service for word in normalized_input.split() if len(word) > 2):
                score = 0.5
            
            if score > 0:
                scored_suggestions.append((service, score))
        
        # Sort by score (descending) and return top suggestions
        scored_suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = [service for service, _ in scored_suggestions[:max_suggestions]]
        
        return suggestions
    
    def _has_common_words(self, str1: str, str2: str) -> bool:
        """
        Check if two strings have common words.
        
        Args:
            str1: First string.
            str2: Second string.
            
        Returns:
            True if strings have common words, False otherwise.
        """
        words1 = set(word for word in str1.split() if len(word) > 2)
        words2 = set(word for word in str2.split() if len(word) > 2)
        return len(words1.intersection(words2)) > 0
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate simple similarity between two strings.
        
        Args:
            str1: First string.
            str2: Second string.
            
        Returns:
            Similarity score between 0 and 1.
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple Jaccard similarity based on character sets
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def validate_services(self, selected_services: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate selected services and identify unmapped ones.
        
        Args:
            selected_services: List of service names to validate.
            
        Returns:
            Tuple of (is_valid, unmapped_services, unique_suggestions).
        """
        if not selected_services:
            return False, [], []
        
        # Ensure selected_services is a list (handle edge case of single string)
        if isinstance(selected_services, str):
            selected_services = [selected_services]
        
        unmapped_services = []
        all_suggestions = []
        
        for service in selected_services:
            if not self._find_field_for_service(service):
                unmapped_services.append(service)
                service_suggestions = self._suggest_similar_services(service, max_suggestions=5)
                if service_suggestions:
                    all_suggestions.extend(service_suggestions)
        
        # Remove duplicates while preserving order and limit to reasonable number
        unique_suggestions = []
        seen = set()
        for suggestion in all_suggestions:
            if suggestion not in seen and len(unique_suggestions) < 10:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
        
        is_valid = len(unmapped_services) == 0
        return is_valid, unmapped_services, unique_suggestions
    
    def process_services(self, selected_services: List[str]) -> Dict[str, any]:
        """
        Process selected services and return field updates for dealership model.
        
        Args:
            selected_services: List of service names from frontend.
            
        Returns:
            Dict containing field updates for the dealership model.
            
        Raises:
            ValidationError: If no services are selected or validation fails.
        """
        if not selected_services:
            raise ValidationError("At least one service must be selected")
        
        # Ensure selected_services is a list (handle edge case of single string)
        if isinstance(selected_services, str):
            selected_services = [selected_services]
        
        # Validate services first
        is_valid, unmapped_services, suggestions = self.validate_services(selected_services)
        
        if unmapped_services:
            logger.warning(f"Unmapped services detected: {unmapped_services}")
            # Log for debugging but don't fail - we'll handle unmapped services gracefully
        
        # Initialize field updates with all boolean fields set to False
        field_updates = {
            'offers_rental': False,
            'offers_purchase': False,
            'offers_drivers': False,
            'offers_trade_in': False,
            'extended_services': []
        }
        
        # Process each selected service
        mapped_services_count = 0
        extended_services = []
        
        for service in selected_services:
            field_name = self._find_field_for_service(service)
            
            if field_name:
                if field_name == 'extended_services':
                    # Add to extended services list
                    extended_services.append(service)
                else:
                    # Set boolean field to True
                    field_updates[field_name] = True
                    mapped_services_count += 1
            else:
                # Log unmapped service for debugging
                logger.info(f"Unmapped service: {service}")
        
        # Set extended services
        if extended_services:
            field_updates['extended_services'] = extended_services
            mapped_services_count += len(extended_services)
        
        # Validate that at least one service was mapped
        if mapped_services_count == 0:
            error_msg = "No valid services were selected from the provided list"
            if unmapped_services:
                error_msg += f". Unrecognized services: {', '.join(unmapped_services[:3])}"
                if len(unmapped_services) > 3:
                    error_msg += f" and {len(unmapped_services) - 3} more"
            if suggestions:
                error_msg += f". Did you mean: {', '.join(suggestions[:3])}?"
            raise ValidationError(error_msg)
        
        # Log successful mapping with details
        core_services = sum([
            field_updates['offers_purchase'],
            field_updates['offers_rental'], 
            field_updates['offers_drivers'],
            field_updates['offers_trade_in']
        ])
        extended_count = len(field_updates['extended_services'])
        
        logger.info(f"Successfully mapped {mapped_services_count} services: {core_services} core services, {extended_count} extended services")
        
        if unmapped_services:
            logger.debug(f"Unmapped services (ignored): {unmapped_services}")
        
        return field_updates
    
    def get_available_services(self) -> Dict[str, List[str]]:
        """
        Get all available services organized by category.
        
        Returns:
            Dict mapping category names to lists of service names.
        """
        return SERVICE_MAPPING.copy()
    
    def get_service_categories(self) -> List[str]:
        """
        Get list of service categories.
        
        Returns:
            List of category names.
        """
        return list(SERVICE_MAPPING.keys())