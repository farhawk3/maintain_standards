"""
Validation logic for Standards Library
"""
from typing import List, Tuple
from models import Library, Standard, Cluster, MACVector

class ValidationError:
    """Represents a validation error"""
    def __init__(self, severity: str, standard_id: str, message: str):
        self.severity = severity  # "error" or "warning"
        self.standard_id = standard_id
        self.message = message
    
    def __str__(self):
        icon = "❌" if self.severity == "error" else "⚠️"
        return f"{icon} [{self.standard_id}] {self.message}"

class LibraryValidator:
    """Validates the entire library"""
    
    def __init__(self, library: Library):
        self.library = library
        self.errors: List[ValidationError] = []
    
    def validate_all(self) -> List[ValidationError]:
        """Run all validations and return list of errors"""
        self.errors = []
        
        self._validate_mac_vectors()
        self._validate_cluster_references()
        self._validate_duplicate_ids()
        self._validate_required_fields()
        self._check_missing_rationales()
        
        return self.errors
    
    def _validate_mac_vectors(self):
        """Check all MAC vectors sum to 1.0"""
        for std in self.library.standards:
            if not std.mac_vector.is_valid():
                actual_sum = std.mac_vector.sum()
                self.errors.append(ValidationError(
                    "error",
                    std.id,
                    f"MAC vector sums to {actual_sum:.4f}, must be 1.0"
                ))
    
    def _validate_cluster_references(self):
        """Check all standards reference valid clusters"""
        cluster_ids = {c.id for c in self.library.clusters}
        
        for std in self.library.standards:
            if std.cluster not in cluster_ids:
                self.errors.append(ValidationError(
                    "error",
                    std.id,
                    f"References non-existent cluster '{std.cluster}'"
                ))
    
    def _validate_duplicate_ids(self):
        """Check for duplicate standard IDs"""
        seen_ids = set()
        
        for std in self.library.standards:
            if std.id in seen_ids:
                self.errors.append(ValidationError(
                    "error",
                    std.id,
                    f"Duplicate standard ID"
                ))
            seen_ids.add(std.id)
        
        # Check cluster IDs too
        seen_cluster_ids = set()
        for cluster in self.library.clusters:
            if cluster.id in seen_cluster_ids:
                self.errors.append(ValidationError(
                    "error",
                    f"CLUSTER:{cluster.id}",
                    f"Duplicate cluster ID"
                ))
            seen_cluster_ids.add(cluster.id)
    
    def _validate_required_fields(self):
        """Check all required fields are present"""
        for std in self.library.standards:
            if not std.id:
                self.errors.append(ValidationError("error", "???", "Missing ID"))
            if not std.name:
                self.errors.append(ValidationError("error", std.id, "Missing name"))
            if not std.cluster:
                self.errors.append(ValidationError("error", std.id, "Missing cluster"))
            if not (0 <= std.importance_weight <= 1):
                self.errors.append(ValidationError(
                    "error",
                    std.id,
                    f"Importance weight {std.importance_weight} not in [0,1]"
                ))
    
    def _check_missing_rationales(self):
        """Check for missing rationale text (warnings, not errors)"""
        for std in self.library.standards:
            rat = std.rationale
            
            # Check if any MAC dimension > 0.1 but has no rationale
            if std.mac_vector.family > 0.1 and not rat.family_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing family_rationale (MAC value > 0.1)"
                ))
            if std.mac_vector.group > 0.1 and not rat.group_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing group_rationale (MAC value > 0.1)"
                ))
            if std.mac_vector.reciprocity > 0.1 and not rat.reciprocity_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing reciprocity_rationale (MAC value > 0.1)"
                ))
            if std.mac_vector.heroism > 0.1 and not rat.heroism_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing heroism_rationale (MAC value > 0.1)"
                ))
            if std.mac_vector.deference > 0.1 and not rat.deference_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing deference_rationale (MAC value > 0.1)"
                ))
            if std.mac_vector.fairness > 0.1 and not rat.fairness_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing fairness_rationale (MAC value > 0.1)"
                ))
            if std.mac_vector.property > 0.1 and not rat.property_rationale.strip():
                self.errors.append(ValidationError(
                    "warning",
                    std.id,
                    "Missing property_rationale (MAC value > 0.1)"
                ))
    
    def has_errors(self) -> bool:
        """Check if there are any errors (not warnings)"""
        return any(e.severity == "error" for e in self.errors)
    
    def get_errors_by_severity(self) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Return (errors, warnings) separately"""
        errors = [e for e in self.errors if e.severity == "error"]
        warnings = [e for e in self.errors if e.severity == "warning"]
        return errors, warnings