"""
Data models for Standards Library
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class MACVector:
    """Represents the 7-dimensional MAC composition"""
    family: float = 0.0
    group: float = 0.0
    reciprocity: float = 0.0
    heroism: float = 0.0
    deference: float = 0.0
    fairness: float = 0.0
    property: float = 0.0
    
    def sum(self) -> float:
        """Return sum of all dimensions"""
        return (self.family + self.group + self.reciprocity + 
                self.heroism + self.deference + self.fairness + 
                self.property)
    
    def is_valid(self, tolerance: float = 0.0001) -> bool:
        """Check if vector sums to 1.0 within tolerance"""
        return abs(self.sum() - 1.0) < tolerance
    
    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "group": self.group,
            "reciprocity": self.reciprocity,
            "heroism": self.heroism,
            "deference": self.deference,
            "fairness": self.fairness,
            "property": self.property
        }

@dataclass
class MACRationale:
    """Theoretical justifications for MAC vector values"""
    family_rationale: str = ""
    group_rationale: str = ""
    reciprocity_rationale: str = ""
    heroism_rationale: str = ""
    deference_rationale: str = ""
    fairness_rationale: str = ""
    property_rationale: str = ""
    overall_rationale: str = ""
    
    def to_dict(self) -> dict:
        return {
            "family_rationale": self.family_rationale,
            "group_rationale": self.group_rationale,
            "reciprocity_rationale": self.reciprocity_rationale,
            "heroism_rationale": self.heroism_rationale,
            "deference_rationale": self.deference_rationale,
            "fairness_rationale": self.fairness_rationale,
            "property_rationale": self.property_rationale,
            "overall_rationale": self.overall_rationale
        }

@dataclass
class Standard:
    """Represents a single moral standard"""
    id: str
    name: str
    cluster: str
    description: str = ""
    importance_weight: float = 0.5
    mac_vector: MACVector = field(default_factory=MACVector)
    primary_focus: str = ""
    secondary_focus: str = ""
    impacted_emotions: List[str] = field(default_factory=list)
    rationale: MACRationale = field(default_factory=MACRationale)
    date_created: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    date_modified: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "cluster": self.cluster,
            "description": self.description,
            "importance_weight": self.importance_weight,
            "mac_vector": self.mac_vector.to_dict(),
            "primary_focus": self.primary_focus,
            "secondary_focus": self.secondary_focus,
            "impacted_emotions": self.impacted_emotions,
            "rationale": self.rationale.to_dict(),
            "date_created": self.date_created,
            "date_modified": self.date_modified
        }

@dataclass
class Cluster:
    """Represents a cluster of standards"""
    id: str
    name: str
    description: str = ""
    order: int = 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "order": self.order
        }

@dataclass
class Library:
    """The complete standards library"""
    version: str = "2.7"
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    clusters: List[Cluster] = field(default_factory=list)
    standards: List[Standard] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "last_modified": self.last_modified,
            "clusters": [c.to_dict() for c in self.clusters],
            "standards": [s.to_dict() for s in self.standards]
        }