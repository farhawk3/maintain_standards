"""
File operations for Standards Library
"""
import json
import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from models import Library, Standard, Cluster, MACVector, MACRationale

class FileManager:
    """Manages all file operations for the library"""
    
    def __init__(self, base_dir: str = "standards_library"):
        # In a serverless environment like Cloud Run, only /tmp is guaranteed to be writable.
        # We check for the K_SERVICE environment variable, which is set by Cloud Run.
        if os.environ.get('K_SERVICE'):
            self.base_dir = Path("/tmp") / base_dir
        else:
            # Use local directory for local development
            self.base_dir = Path(base_dir)

        self.library_file = self.base_dir / "library.json"
        self.backups_dir = self.base_dir / "backups"
        self.exports_dir = self.base_dir / "exports"
        self.max_backups = 5

    def _ensure_directories(self):
        """Create directory structure if needed"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
    
    def library_exists(self) -> bool:
        """Check if library file exists"""
        # No need to ensure dirs exist just to check for a file.
        return self.library_file.exists()
    
    def load_library(self) -> Optional[Library]:
        """Load library from JSON file"""
        self._ensure_directories() # Ensure directory exists before trying to read.
        if not self.library_exists():
            return None
        
        try:
            with open(self.library_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._dict_to_library(data)
        
        except Exception as e:
            print(f"Error loading library: {e}")
            return None
    
    def save_library(self, library: Library) -> bool:
        """Save library to JSON file"""
        self._ensure_directories()
        try:
            # Update last_modified timestamp
            library.last_modified = datetime.now().isoformat()
            
            # Convert to dict and save
            data = library.to_dict()
            
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving library: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create a backup of current library"""
        self._ensure_directories()
        if not self.library_exists():
            return False
        
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backups_dir / f"library_backup_{timestamp}.json"
            
            # Copy current library to backup
            shutil.copy2(self.library_file, backup_file)
            
            # Manage backup rotation (keep only max_backups)
            self._rotate_backups()
            
            return True
        
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _rotate_backups(self):
        """Keep only the most recent max_backups backups"""
        backups = sorted(self.backups_dir.glob("library_backup_*.json"), 
                        key=lambda p: p.stat().st_mtime, 
                        reverse=True)
        
        # Delete oldest backups if we exceed max_backups
        for old_backup in backups[self.max_backups:]:
            old_backup.unlink()
    
    def list_backups(self) -> List[dict]:
        """List all available backups with metadata"""
        self._ensure_directories()
        backups = []
        
        for backup_file in sorted(self.backups_dir.glob("library_backup_*.json"), 
                                  key=lambda p: p.stat().st_mtime, 
                                  reverse=True):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": backup_file,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size": stat.st_size
            })
        
        return backups
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore library from a backup file"""
        self._ensure_directories()
        backup_path = self.backups_dir / backup_filename
        
        if not backup_path.exists():
            return False
        
        try:
            # Copy backup to main library file
            shutil.copy2(backup_path, self.library_file)
            return True
        
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def delete_all_backups(self) -> bool:
        """Delete all backup files"""
        self._ensure_directories()
        try:
            for backup_file in self.backups_dir.glob("library_backup_*.json"):
                backup_file.unlink()
            return True
        
        except Exception as e:
            print(f"Error deleting backups: {e}")
            return False
    
    def export_library(self, 
                      library: Library, 
                      filename: str,
                      cluster_ids: Optional[List[str]] = None,
                      standard_ids: Optional[List[str]] = None,
                      include_rationales: bool = False) -> bool:
        """
        Export library or subset to file
        
        Args:
            library: Library to export
            filename: Export filename
            cluster_ids: If provided, only export standards from these clusters
            standard_ids: If provided, only export these specific standards
            include_rationales: Whether to include rationale fields
        """
        self._ensure_directories()
        try:
            export_path = self.exports_dir / filename
            
            # Create filtered library
            filtered_standards = library.standards
            
            if cluster_ids:
                filtered_standards = [s for s in filtered_standards 
                                     if s.cluster in cluster_ids]
            
            if standard_ids:
                filtered_standards = [s for s in filtered_standards 
                                     if s.id in standard_ids]
            
            # Build export data
            export_data = {
                "version": library.version,
                "exported": datetime.now().isoformat(),
                "clusters": [c.to_dict() for c in library.clusters],
                "standards": []
            }
            
            for std in filtered_standards:
                std_dict = std.to_dict()
                
                # Remove rationales if not needed (for runtime use)
                if not include_rationales:
                    del std_dict["rationale"]
                
                export_data["standards"].append(std_dict)
            
            # Save export file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error exporting library: {e}")
            return False
    
    def _dict_to_library(self, data: dict) -> Library:
        """Convert dictionary to Library object"""
        library = Library(
            version=data.get("version", "2.7"),
            last_modified=data.get("last_modified", "")
        )
        
        # Load clusters
        for cluster_data in data.get("clusters", []):
            cluster = Cluster(
                id=cluster_data["id"],
                name=cluster_data["name"],
                description=cluster_data.get("description", ""),
                order=cluster_data.get("order", 0)
            )
            library.clusters.append(cluster)
        
        # Load standards
        for std_data in data.get("standards", []):
            # Parse MAC vector
            mac_data = std_data.get("mac_vector", {})
            mac_vector = MACVector(
                family=mac_data.get("family", 0.0),
                group=mac_data.get("group", 0.0),
                reciprocity=mac_data.get("reciprocity", 0.0),
                heroism=mac_data.get("heroism", 0.0),
                deference=mac_data.get("deference", 0.0),
                fairness=mac_data.get("fairness", 0.0),
                property=mac_data.get("property", 0.0)
            )
            
            # Parse rationale
            rat_data = std_data.get("rationale", {})
            rationale = MACRationale(
                family_rationale=rat_data.get("family_rationale", ""),
                group_rationale=rat_data.get("group_rationale", ""),
                reciprocity_rationale=rat_data.get("reciprocity_rationale", ""),
                heroism_rationale=rat_data.get("heroism_rationale", ""),
                deference_rationale=rat_data.get("deference_rationale", ""),
                fairness_rationale=rat_data.get("fairness_rationale", ""),
                property_rationale=rat_data.get("property_rationale", "")
            )
            
            standard = Standard(
                id=std_data["id"],
                name=std_data["name"],
                cluster=std_data["cluster"],
                description=std_data.get("description", ""),
                importance_weight=std_data.get("importance_weight", 0.5),
                mac_vector=mac_vector,
                primary_focus=std_data.get("primary_focus", ""),
                secondary_focus=std_data.get("secondary_focus", ""),
                impacted_emotions=std_data.get("impacted_emotions", []),
                rationale=rationale,
                date_created=std_data.get("date_created", ""),
                date_modified=std_data.get("date_modified", "")
            )
            
            library.standards.append(standard)
        
        return library
    
    def create_empty_library(self) -> Library:
        """Create a new empty library with default structure"""
        library = Library()
        
        # Add default clusters (from v2.7 document)
        default_clusters = [
            Cluster("ENH", "Empathy & Non-Harm", "Standards establishing fundamental moral principle...", 1),
            Cluster("PAW", "Prosocial Action & Welfare", "Standards governing capacity to recognize opportunities...", 2),
            Cluster("JE", "Justice & Equity", "Standards providing framework for fairness...", 3),
            Cluster("IT", "Integrity & Truthfulness", "Standards representing commitment to truth...", 4),
            Cluster("CI", "Cognitive Integrity", "Standards governing belief formation...", 5),
            Cluster("RT", "Reciprocity & Trust", "Standards governing social exchanges...", 6),
            Cluster("CCG", "Community & Collective Good", "Standards governing relationship with collective...", 7),
            Cluster("RA", "Respect for Autonomy", "Standards establishing respect for sovereignty...", 8),
            Cluster("SOD", "Social Order & Deference", "Standards governing relationship with social structures...", 9),
            Cluster("PC", "Privacy & Confidentiality", "Standards establishing duty to protect information...", 10),
            Cluster("CD", "Competence & Diligence", "Standards establishing ethical importance of skill...", 11),
            Cluster("UWS", "Universal Welfare & Stewardship", "Standards expanding circle of moral concern...", 12),
            Cluster("VC", "Virtues of Character", "Standards governing internal dispositions...", 13),
            Cluster("FR", "Foundational Reverence", "Standards governing reverence for concepts of value...", 14),
            Cluster("ES", "Existential Stewardship", "Standards representing apex of moral responsibility...", 15)
        ]
        
        library.clusters = default_clusters
        
        return library