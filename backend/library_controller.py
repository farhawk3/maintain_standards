# backend/library_controller.py
"""
LibraryController: The business logic core for the Standards Library.
This class is independent of any UI framework.
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

from models import Library, Standard, Cluster, MACVector, MACRationale
from file_operations import FileManager

class LibraryController:
    """Handles all business logic for managing the library."""

    def __init__(self):
        self.file_manager = FileManager()
        self.library: Optional[Library] = self._load_initial_library()

    def _load_initial_library(self) -> Library:
        """Loads the library from disk or creates a new one."""
        if self.file_manager.library_exists():
            library = self.file_manager.load_library()
            if library:
                return library
        
        # If no library exists or loading fails, create and save an empty one.
        empty_library = self.file_manager.create_empty_library()
        self.file_manager.save_library(empty_library)
        return empty_library

    def get_library_version(self) -> str:
        """Returns the version of the current library."""
        return self.library.version if self.library else "N/A"

    def get_all_standards(self) -> list[dict]:
        """
        Returns a list of all standards, converted to dictionaries for JSON serialization.
        """
        if not self.library:
            return []
        return [std.to_dict() for std in self.library.standards]

    def get_all_clusters(self) -> list[dict]:
        """
        Returns a list of all clusters, converted to dictionaries.
        """
        if not self.library:
            return []
        return [cluster.to_dict() for cluster in self.library.clusters]

    def create_standard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new standard, adds it to the library, and saves the file.
        """
        if not self.library:
            # This should ideally not happen if the controller is initialized properly
            raise Exception("Library not loaded. Cannot create standard.")
        
        standard_id = data.get("id")
        if not standard_id:
            raise ValueError("Standard ID is a required field.")

        # --- Validation: Check for uniqueness ---
        existing_ids = {std['id'] for std in self.get_all_standards()}
        if standard_id in existing_ids:
            raise ValueError(f"Standard ID '{standard_id}' already exists. Please choose a unique ID.")

        cluster_id = data.get("cluster")
        if not cluster_id:
            raise ValueError("Cluster ID is required to create a standard.")
            
        # Create a new Standard object from the incoming data
        new_standard = Standard(
            id=standard_id,
            name=data.get("name", ""),
            description=data.get("description", ""),
            cluster=cluster_id,
            # Provide default values for all other required fields
            importance_weight=0.5,
            mac_vector=MACVector(
                family=0.0,
                group=0.0,
                reciprocity=0.0,
                heroism=0.0,
                deference=0.0,
                fairness=0.0,
                property=0.0
            ),
            primary_focus="Object/Concept",
            secondary_focus="Action",
            impacted_emotions=[],
            rationale=MACRationale(), # Assumes default empty strings in model
            date_created=datetime.now().strftime("%Y-%m-%d"),
            date_modified=datetime.now().strftime("%Y-%m-%d")
        )
        
        # Add the new standard to the library's main list of standards
        self.library.standards.append(new_standard)
        
        # Save the updated library back to the JSON file
        self.file_manager.save_library(self.library)

        # Return the new standard's data so the frontend can confirm creation
        return new_standard.to_dict()

    def update_standard(self, standard_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finds a standard by its ID, validates the incoming data,
        updates the standard, saves the library, and returns the updated standard.
        """
        std = next((s for s in self.library.standards if s.id == standard_id), None)
        if not std:
            raise ValueError(f"Could not find standard {standard_id} to save.")

        # --- Validation ---
        # Pydantic will validate the structure of mac_vector and rationale upon object creation
        new_mac_vector = MACVector(**form_data.get("mac_vector", {}))
        if not new_mac_vector.is_valid():
            raise ValueError("Save failed: MAC vector must sum to 1.0.")

        importance_weight = float(form_data.get("importance_weight", std.importance_weight))
        if not (0.0 <= importance_weight <= 1.0):
            raise ValueError("Save failed: Importance Weight must be between 0.0 and 1.0.")

        # --- Update the standard object ---
        std.name = form_data.get("name", std.name)
        std.description = form_data.get("description", std.description)
        std.importance_weight = importance_weight
        std.primary_focus = form_data.get("primary_focus", std.primary_focus)
        std.secondary_focus = form_data.get("secondary_focus", std.secondary_focus)
        std.impacted_emotions = form_data.get("impacted_emotions", std.impacted_emotions)
        std.cluster = form_data.get("cluster", std.cluster)
        std.mac_vector = new_mac_vector
        std.rationale = MACRationale(**form_data.get("rationale", {}))
        std.date_modified = datetime.now().strftime("%Y-%m-%d")

        self.file_manager.save_library(self.library)
        return std.to_dict()

    def delete_standard(self, standard_id: str) -> bool:
        """
        Finds a standard by its ID and removes it from the library.
        Returns True on success, False if the standard was not found.
        """
        initial_length = len(self.library.standards)
        self.library.standards = [s for s in self.library.standards if s.id != standard_id]
        
        if len(self.library.standards) < initial_length:
            self.file_manager.save_library(self.library)
            return True
        
        return False

    def create_backup(self) -> str:
        """
        Delegates the creation of a timestamped backup to the FileManager.
        Returns the filename of the created backup file.
        """
        backup_filename = self.file_manager.create_backup()
        if backup_filename:
            return backup_filename
        raise Exception("File manager failed to create or return backup filename.")

    def get_backup_files(self) -> list[str]:
        """Returns a list of existing backup filenames."""
        backups = self.file_manager.list_backups()
        return [b['filename'] for b in backups]

    def delete_backup_file(self, filename: str) -> bool:
        """Delegates the deletion of a specific backup file to the FileManager."""
        return self.file_manager.delete_backup_file(filename)

    def restore_from_file(self, file_stream) -> bool:
        """
        Overwrites the main library with the content from an uploaded file stream.
        """
        # DELEGATE to the FileManager.
        if self.file_manager.restore_from_file_stream(file_stream):
            self.library = self._load_initial_library() # Reload the library in memory
            return True
        return False

    def restore_from_backup(self, filename: str) -> bool:
        """
        Restores the library from a specific backup filename on the server.
        """
        if self.file_manager.restore_backup(filename):
            self.library = self._load_initial_library() # Reload the library in memory
            return True
        return False

    def get_exported_data(self, export_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies filters to the current library in memory and returns the
        resulting data as a dictionary, ready for export.
        """
        if not self.library:
            raise ValueError("Library not loaded.")

        filtered_standards = self.library.standards

        if export_options.get("cluster_ids"):
            filtered_standards = [s for s in filtered_standards if s.cluster in export_options["cluster_ids"]]
        
        if export_options.get("standard_ids"):
            filtered_standards = [s for s in filtered_standards if s.id in export_options["standard_ids"]]

        standards_as_dicts = []
        for std in filtered_standards:
            std_dict = std.to_dict()
            if not export_options.get("include_rationales", True):
                del std_dict['rationale']
            standards_as_dicts.append(std_dict)

        return {
            "version": self.library.version,
            "exported": datetime.now().isoformat(),
            "clusters": [c.to_dict() for c in self.library.clusters],
            "standards": standards_as_dicts
        }

    # --- Cluster Maintenance ---

    def _reorder_clusters(self, target_order: int, cluster_to_exclude_id: Optional[str] = None):
        """Shifts cluster orders to make room for a new or updated cluster."""
        for cluster in self.library.clusters:
            if cluster.id == cluster_to_exclude_id:
                continue
            if cluster.order >= target_order:
                cluster.order += 1

    def create_cluster(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new cluster, reorders others, and saves."""
        new_id = data.get("id")
        if not new_id or not new_id.strip():
            raise ValueError("Cluster ID cannot be empty.")
        if any(c.id == new_id for c in self.library.clusters):
            raise ValueError(f"Cluster ID '{new_id}' already exists.")

        new_order = int(data.get("order", 1))
        self._reorder_clusters(new_order)

        new_cluster = Cluster(
            id=new_id,
            name=data.get("name", "New Cluster"),
            description=data.get("description", ""),
            order=new_order
        )
        self.library.clusters.append(new_cluster)
        self.library.clusters.sort(key=lambda c: c.order)
        self.file_manager.save_library(self.library)
        return new_cluster.to_dict()

    def update_cluster(self, cluster_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing cluster's details."""
        cluster_to_update = next((c for c in self.library.clusters if c.id == cluster_id), None)
        if not cluster_to_update:
            raise ValueError(f"Cluster '{cluster_id}' not found.")

        new_order = int(data.get("order", cluster_to_update.order))
        if new_order != cluster_to_update.order:
            self._reorder_clusters(new_order, cluster_to_exclude_id=cluster_id)

        cluster_to_update.name = data.get("name", cluster_to_update.name)
        cluster_to_update.description = data.get("description", cluster_to_update.description)
        cluster_to_update.order = new_order

        self.library.clusters.sort(key=lambda c: c.order)
        self.file_manager.save_library(self.library)
        return cluster_to_update.to_dict()

    def delete_cluster(self, cluster_id: str):
        """Deletes a cluster if it is not in use."""
        standards_using_cluster = [s.id for s in self.library.standards if s.cluster == cluster_id]
        if standards_using_cluster:
            raise ValueError(f"Cannot delete cluster '{cluster_id}' because it is in use by {len(standards_using_cluster)} standard(s).")

        cluster_to_delete = next((c for c in self.library.clusters if c.id == cluster_id), None)
        if not cluster_to_delete:
            # This case should ideally not be hit if called from a valid UI, but it's good practice.
            return

        deleted_order = cluster_to_delete.order

        # Remove the cluster
        self.library.clusters = [c for c in self.library.clusters if c.id != cluster_id]

        # Decrement the order of subsequent clusters
        for cluster in self.library.clusters:
            if cluster.order > deleted_order:
                cluster.order -= 1

        self.file_manager.save_library(self.library)

    # --- Import Logic ---

    def _import_clusters(self, clusters_data: list, report: dict):
        """Helper method to process and import clusters."""
        for cluster_data in clusters_data:
            cluster_id = cluster_data.get("id")
            if not cluster_id:
                continue  # Skip clusters without an ID

            if any(c.id == cluster_id for c in self.library.clusters):
                self.update_cluster(cluster_id, cluster_data)
                report["clusters_updated"] += 1
            else:
                self.create_cluster(cluster_data)
                report["clusters_added"] += 1

    def _import_standards(self, standards_data: list, report: dict):
        """Helper method to process and import standards."""
        existing_standard_ids = {s.id for s in self.library.standards}
        existing_cluster_ids = {c.id for c in self.library.clusters}

        for standard_data in standards_data:
            standard_id = standard_data.get("id")
            cluster_id = standard_data.get("cluster")

            if not standard_id or not cluster_id:
                continue  # Skip standards without an ID or cluster

            if cluster_id not in existing_cluster_ids:
                report["standards_skipped"] += 1
                report["skipped_reasons"].append(
                    f"Standard '{standard_id}' skipped: Cluster '{cluster_id}' does not exist."
                )
                continue

            if standard_id in existing_standard_ids:
                self.update_standard(standard_id, standard_data)
                report["standards_updated"] += 1
            else:
                self.create_standard(standard_data)
                report["standards_added"] += 1

    def import_from_file(self, file_stream) -> Dict[str, Any]:
        """
        Imports clusters and standards from an uploaded file stream using a
        two-pass 'merge and validate' strategy.
        """
        try:
            import_data = json.load(file_stream)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Invalid JSON file. Please ensure the file is a valid JSON.")

        report = {
            "clusters_added": 0,
            "clusters_updated": 0,
            "standards_added": 0,
            "standards_updated": 0,
            "standards_skipped": 0,
            "skipped_reasons": []
        }

        # --- Pass 1: Synchronize Clusters ---
        self._import_clusters(import_data.get("clusters", []), report)

        # --- Pass 2: Merge Standards ---
        self._import_standards(import_data.get("standards", []), report)

        return report