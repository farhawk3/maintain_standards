"""
File operations for Standards Library
"""
import json
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import Library, Standard, Cluster, MACVector, MACRationale

class FileManager:
    """Manages all file operations for the library"""
    
    def __init__(self, base_dir_name: str = "standards_library"):
        # In a serverless environment like Cloud Run, only /tmp is guaranteed to be writable.
        if os.environ.get('K_SERVICE'):
            self.base_dir = Path("/tmp") / base_dir_name
            self.library_file = self.base_dir / "library.json"
        else:
            # For local development, find the project root and then the data directory.
            project_root = Path(__file__).resolve().parent.parent
            self.base_dir = project_root / base_dir_name
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
        return self.library_file.exists() and self.library_file.is_file()
    
    def load_library(self) -> Optional[Library]:
        """Load library from JSON file"""
        if not self.library_exists():
            return None
        
        try:
            with open(self.library_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._dict_to_library(data)
        
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading library: {e}")
            return None
    
    def save_library(self, library: Library) -> bool:
        """Save library to JSON file"""
        self._ensure_directories()
        try:
            library.last_modified = datetime.now().isoformat()
            data = library.to_dict()
            
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving library: {e}")
            return False

    def create_backup(self) -> Optional[str]:
        """Create a backup of current library"""
        self._ensure_directories()
        if not self.library_exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backups_dir / f"library_backup_{timestamp}.json"
            shutil.copy2(self.library_file, backup_file)
            self._rotate_backups()
            return backup_file.name
        
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def _rotate_backups(self):
        """Keep only the most recent max_backups backups"""
        backups = sorted(self.backups_dir.glob("library_backup_*.json"), 
                        key=lambda p: p.stat().st_mtime, 
                        reverse=True)
        
        for old_backup in backups[self.max_backups:]:
            old_backup.unlink()
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        self._ensure_directories()
        backups = []
        
        for backup_file in sorted(self.backups_dir.glob("library_backup_*.json"), 
                                  key=lambda p: p.stat().st_mtime, 
                                  reverse=True):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
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
            shutil.copy2(backup_path, self.library_file)
            return True
        
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def delete_backup_file(self, filename: str) -> bool:
        """Deletes a specific backup file by its name."""
        self._ensure_directories()
        backup_path = self.backups_dir / filename
        
        # Security check to ensure we are only deleting from the backups directory
        if backup_path.exists() and backup_path.parent == self.backups_dir:
            try:
                backup_path.unlink()
                return True
            except Exception as e:
                print(f"Error deleting backup file {filename}: {e}")
        return False

    def delete_all_backups(self) -> bool:
        """Delete all backup files"""
        self._ensure_directories()
        try:
            if self.backups_dir.exists():
                shutil.rmtree(self.backups_dir)
                self.backups_dir.mkdir()
            return True
        
        except Exception as e:
            print(f"Error deleting backups: {e}")
            return False

    def restore_from_file_stream(self, file_stream) -> bool:
        """Overwrites the main library file with content from a file stream."""
        self._ensure_directories()
        try:
            # Save the stream content directly to the main library file
            with open(self.library_file, 'wb') as f:
                f.write(file_stream.read())
            return True
        except Exception as e:
            print(f"Error restoring from file stream: {e}")
            return False
    
    def export_library(self, 
                      library: Library, 
                      filename: str,
                      cluster_ids: Optional[List[str]] = None,
                      standard_ids: Optional[List[str]] = None,
                      include_rationales: bool = False) -> bool:
        """Export library or subset to file"""
        self._ensure_directories()
        try:
            export_path = self.exports_dir / filename
            
            filtered_standards = library.standards
            
            if cluster_ids:
                filtered_standards = [s for s in filtered_standards if s.cluster in cluster_ids]
            
            if standard_ids:
                filtered_standards = [s for s in filtered_standards if s.id in standard_ids]
            
            export_data = {
                "version": library.version,
                "exported": datetime.now().isoformat(),
                "clusters": [c.to_dict() for c in library.clusters],
            }
            
            # Convert standards to dicts and then filter rationales if needed
            standards_as_dicts = []
            for std in filtered_standards:
                std_dict = std.to_dict()
                if not include_rationales:
                    del std_dict['rationale']
                standards_as_dicts.append(std_dict)
            export_data["standards"] = standards_as_dicts

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
        
        library.clusters = [Cluster(**c) for c in data.get("clusters", [])]
        
        for std_data in data.get("standards", []):
            mac_vector = MACVector(**std_data.get("mac_vector", {}))
            rationale = MACRationale(**std_data.get("rationale", {}))
            std_data["mac_vector"] = mac_vector
            std_data["rationale"] = rationale
            library.standards.append(Standard(**std_data))
        
        return library
    
    def create_empty_library(self) -> Library:
        """Create a new empty library with default structure"""
        library = Library()
        
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
