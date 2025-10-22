"""
Standards Library Maintenance Tool
A Streamlit app for managing moral standards library
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, List

from models import Library, Standard, Cluster, MACVector, MACRationale
from validator import LibraryValidator
from file_operations import FileManager

# Constants
FOCUS_OPTIONS = ["Action", "State/Event", "Object/Concept", "N/A"]
EMOTION_OPTIONS = [
    "Praiseworthiness", "Valence", "Arousal", "Dominance", 
    "Belonging", "Goal Relevance", "Social Impact", "Prospect",
    "Agency", "Intentionality", "Expectation", "Familiarity"
]

# Page configuration
st.set_page_config(
    page_title="Standards Library Editor",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'library' not in st.session_state:
    st.session_state.library = None
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = FileManager()
if 'selected_standard' not in st.session_state:
    st.session_state.selected_standard = None
if 'selected_cluster' not in st.session_state:
    st.session_state.selected_cluster = None
if 'navigate_to' not in st.session_state:
    st.session_state.navigate_to = None

# Initialize or load library
def initialize_library():
    """Load existing library or create new one"""
    fm = st.session_state.file_manager
    
    if fm.library_exists():
        library = fm.load_library()
        if library:
            st.session_state.library = library
            return True
    
    # Create new library if none exists
    st.session_state.library = fm.create_empty_library()
    return False

# Sidebar navigation
def render_sidebar():
    """Render sidebar menu"""
    st.sidebar.title("📚 Standards Library")
    st.sidebar.markdown("---")
    
    menu_options = [
        "Library Overview",
        "Browse & Search",
        "Create New Standard",
        "Manage Clusters",
        "Backup & Restore",
        "Export",
        "Validate Library"
    ]
    
    choice = st.sidebar.radio("Navigation", menu_options, key="nav_menu")
    
    st.sidebar.markdown("---")    
    # Quick stats
    if st.session_state.library:
        lib = st.session_state.library
        st.sidebar.metric("Total Standards", len(lib.standards))
        st.sidebar.metric("Total Clusters", len(lib.clusters))
    
    return choice

# Screen 1: Library Overview
def screen_library_overview():
    """Display library overview dashboard"""
    st.title("📊 Library Overview")
    
    lib = st.session_state.library
    
    if not lib:
        st.warning("No library loaded")
        return
    
    # Header metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Standards", len(lib.standards))
    with col2:
        st.metric("Total Clusters", len(lib.clusters))
    with col3:
        st.metric("Version", lib.version)
    
    st.markdown(f"**Last Modified:** {lib.last_modified}")
    
    # Standards per cluster
    st.subheader("Standards Distribution by Cluster")
    
    cluster_counts = {}
    for std in lib.standards:
        cluster_counts[std.cluster] = cluster_counts.get(std.cluster, 0) + 1
    
    if cluster_counts:
        df = pd.DataFrame([
            {"Cluster": k, "Count": v} 
            for k, v in sorted(cluster_counts.items())
        ])
        st.bar_chart(df.set_index("Cluster"))
    else:
        st.info("No standards in library yet")
    
    # Quick health check
    st.subheader("Quick Health Check")
    validator = LibraryValidator(lib)
    errors = validator.validate_all()
    
    if not errors:
        st.success("✅ Library is valid - no issues found")
    else:
        error_list = [e for e in errors if e.severity == "error"]
        warning_list = [e for e in errors if e.severity == "warning"]
        
        if error_list:
            st.error(f"❌ {len(error_list)} errors found")
        if warning_list:
            st.warning(f"⚠️ {len(warning_list)} warnings found")

# Screen 2: Browse & Search
def screen_browse_search():
    """Browse and search standards"""
    st.title("🔍 Browse & Search Standards")
    
    lib = st.session_state.library
    
    if not lib or not lib.standards:
        st.info("No standards in library yet. Create one to get started!")
        return
    
    # Filters
    col1, col2 = st.columns([1, 2])
    
# Filters
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create formatted cluster options: "(ID) Name"
        cluster_dict = {f"({c.id}) {c.name}": c.id for c in lib.clusters}
        cluster_options = ["All"] + list(cluster_dict.keys())
        
        selected_cluster_display = st.selectbox("Filter by Cluster", cluster_options)
        
        # Extract the ID from the formatted string (or keep "All")
        if selected_cluster_display == "All":
            selected_cluster = "All"
        else:
            selected_cluster = cluster_dict[selected_cluster_display]
    
    with col2:
        search_term = st.text_input("Search by ID or Name", "")    
    # Filter standards
    filtered_standards = lib.standards
    
    if selected_cluster != "All":
        filtered_standards = [s for s in filtered_standards if s.cluster == selected_cluster]
    
    if search_term:
        search_lower = search_term.lower()
        filtered_standards = [
            s for s in filtered_standards 
            if search_lower in s.id.lower() or search_lower in s.name.lower()
        ]
    
# Display as table
    if filtered_standards:
        st.write(f"**Showing {len(filtered_standards)} standards**")
        
        # Create cluster name lookup
        cluster_names = {c.id: c.name for c in lib.clusters}
        
        data = []
        for idx, std in enumerate(filtered_standards, start=1):
            data.append({
                "#": idx,
                "ID": std.id,
                "Name": std.name,
                "Cluster": cluster_names.get(std.cluster, std.cluster),  # Use name instead of ID
                "Weight": f"{std.importance_weight:.2f}"
            })
        
        df = pd.DataFrame(data)
        
        # Make table clickable via selectbox
        selected_id = st.selectbox(
            "Select standard to edit:",
            options=[s.id for s in filtered_standards],
            format_func=lambda x: f"{x} - {next(s.name for s in filtered_standards if s.id == x)}"
        )
        
        if st.button("Edit Selected Standard"):
            # Find the standard and store in session state
            found_standard = next(s for s in lib.standards if s.id == selected_id)
            st.session_state.selected_standard = found_standard
            
            # Navigate to Edit Standard screen
            st.session_state.navigate_to = "Edit Standard"
            st.rerun()
        
        # Show table with column configuration
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn(
                    "#",
                    width="small",
                    help="Row number"
                )
            }
        )
    else:
        st.info("No standards match your filters")

# Screen 3: Edit Standard
def screen_edit_standard():
    """Edit an existing standard"""
    st.title("✏️ Edit Standard")

    lib = st.session_state.library
    selected = st.session_state.selected_standard

    # Check if a standard is selected FIRST
    if not selected:
        st.info("No standard selected. Go to Browse & Search to select one.")
        
        if st.button("← Back to Browse"):
            st.session_state.navigate_to = "Browse & Search"
            st.rerun()
        return
    
    # Now we know selected is not None, safe to access its properties
    st.subheader(f"Editing: {selected.id}")
    
    # Find the actual standard in library (in case it's been modified)
    try:
        std_index = next(i for i, s in enumerate(lib.standards) if s.id == selected.id)
        std = lib.standards[std_index]
    except StopIteration:
        st.error(f"Standard '{selected.id}' not found in library")
        if st.button("← Back to Browse"):
            st.session_state.selected_standard = None
            st.session_state.navigate_to = "Browse & Search"
            st.rerun()
        return
    
    # Create form
    with st.form("edit_standard_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Standard ID", value=std.id, disabled=True)
            name = st.text_input("Name", value=std.name)
            
            # Create formatted cluster options: "(ID) Name"
            cluster_dict = {f"({c.id}) {c.name}": c.id for c in lib.clusters}
            cluster_options = list(cluster_dict.keys())

            # Find current cluster's formatted version
            current_cluster_formatted = next((k for k, v in cluster_dict.items() if v == std.cluster), cluster_options[0])
            cluster_index = cluster_options.index(current_cluster_formatted)
            
            cluster_display = st.selectbox("Cluster", cluster_options, index=cluster_index)
            cluster = cluster_dict[cluster_display]  # Extract the ID from the formatted string            
            importance_weight = st.slider("Importance Weight (wbase)", 0.0, 1.0, float(std.importance_weight), 0.05)
        
        with col2:
            primary_focus = st.selectbox(
                "Primary Focus", 
                FOCUS_OPTIONS,
                index=FOCUS_OPTIONS.index(std.primary_focus) if std.primary_focus in FOCUS_OPTIONS else 0
            )
            
            secondary_focus = st.selectbox(
                "Secondary Focus",
                FOCUS_OPTIONS,
                index=FOCUS_OPTIONS.index(std.secondary_focus) if std.secondary_focus in FOCUS_OPTIONS else 0
            )
            
            impacted_emotions = st.multiselect(
                "Impacted Emotion Dimensions",
                EMOTION_OPTIONS,
                default=std.impacted_emotions
            )
        
        description = st.text_area("Description", value=std.description, height=100)
        
        # MAC Vector
        st.subheader("MAC Vector")
        st.caption("Values must sum to exactly 1.0")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            mac_family = st.number_input("Family", 0.0, 1.0, float(std.mac_vector.family), 0.01, format="%.3f")
            mac_group = st.number_input("Group", 0.0, 1.0, float(std.mac_vector.group), 0.01, format="%.3f")
        
        with col2:
            mac_reciprocity = st.number_input("Reciprocity", 0.0, 1.0, float(std.mac_vector.reciprocity), 0.01, format="%.3f")
            mac_heroism = st.number_input("Heroism", -1.0, 1.0, float(std.mac_vector.heroism), 0.01, format="%.3f")
        
        with col3:
            mac_deference = st.number_input("Deference", -1.0, 1.0, float(std.mac_vector.deference), 0.01, format="%.3f")
            mac_fairness = st.number_input("Fairness", -1.0, 1.0, float(std.mac_vector.fairness), 0.01, format="%.3f")
        
        with col4:
            mac_property = st.number_input("Property", 0.0, 1.0, float(std.mac_vector.property), 0.01, format="%.3f")
        
        # Calculate and display sum
        mac_sum = mac_family + mac_group + mac_reciprocity + mac_heroism + mac_deference + mac_fairness + mac_property
        
        if abs(mac_sum - 1.0) < 0.0001:
            st.success(f"✅ MAC Vector Sum: {mac_sum:.6f}")
        else:
            st.error(f"❌ MAC Vector Sum: {mac_sum:.6f} (must be 1.0)")
        
        # Rationales
        st.subheader("Rationale")
        
        family_rat = st.text_area("Family Rationale", value=std.rationale.family_rationale, height=80)
        group_rat = st.text_area("Group Rationale", value=std.rationale.group_rationale, height=80)
        reciprocity_rat = st.text_area("Reciprocity Rationale", value=std.rationale.reciprocity_rationale, height=80)
        heroism_rat = st.text_area("Heroism Rationale", value=std.rationale.heroism_rationale, height=80)
        deference_rat = st.text_area("Deference Rationale", value=std.rationale.deference_rationale, height=80)
        fairness_rat = st.text_area("Fairness Rationale", value=std.rationale.fairness_rationale, height=80)
        property_rat = st.text_area("Property Rationale", value=std.rationale.property_rationale, height=80)
        overall_rat = st.text_area("Overall Rationale", value=std.rationale.overall_rationale, height=150)
        
        # Form buttons
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            # Validate MAC sum
            if abs(mac_sum - 1.0) >= 0.0001:
                st.error("Cannot save: MAC vector must sum to 1.0")
            else:
                # Update standard
                std.name = name
                std.cluster = cluster
                std.description = description
                std.importance_weight = importance_weight
                std.primary_focus = primary_focus
                std.secondary_focus = secondary_focus
                std.impacted_emotions = impacted_emotions
                
                std.mac_vector = MACVector(
                    family=mac_family,
                    group=mac_group,
                    reciprocity=mac_reciprocity,
                    heroism=mac_heroism,
                    deference=mac_deference,
                    fairness=mac_fairness,
                    property=mac_property
                )
                
                std.rationale = MACRationale(
                    family_rationale=family_rat,
                    group_rationale=group_rat,
                    reciprocity_rationale=reciprocity_rat,
                    heroism_rationale=heroism_rat,
                    deference_rationale=deference_rat,
                    fairness_rationale=fairness_rat,
                    property_rationale=property_rat,
                    overall_rationale=overall_rat
                )
                
                std.date_modified = datetime.now().strftime("%Y-%m-%d")
                
                # Save library
                if st.session_state.file_manager.save_library(lib):
                    st.success("✅ Standard saved successfully!")
                    st.session_state.selected_standard = None
                    st.rerun()
                else:
                    st.error("❌ Error saving standard")
        
        if cancelled:
            st.session_state.selected_standard = None
            st.rerun()

# Screen 4: Create New Standard
def screen_create_standard():
    """Create a new standard"""
    st.title("➕ Create New Standard")
    
    lib = st.session_state.library
    
    # Suggest next ID based on cluster
    st.info("💡 Tip: Select cluster first to get suggested ID")
    
    with st.form("create_standard_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cluster_options = [c.id for c in lib.clusters]
            cluster = st.selectbox("Cluster", cluster_options)
            
            # Suggest next ID
            existing_ids = [s.id for s in lib.standards if s.cluster == cluster]
            if existing_ids:
                # Extract numbers from IDs like "ENH-1", "ENH-2"
                numbers = []
                for id_str in existing_ids:
                    parts = id_str.split('-')
                    if len(parts) == 2 and parts[1].isdigit():
                        numbers.append(int(parts[1]))
                next_num = max(numbers) + 1 if numbers else 1
                suggested_id = f"{cluster}-{next_num}"
            else:
                suggested_id = f"{cluster}-1"
            
            std_id = st.text_input("Standard ID", value=suggested_id)
            name = st.text_input("Name", value="")
            importance_weight = st.slider("Importance Weight (wbase)", 0.0, 1.0, 0.5, 0.05)
        
        with col2:
            primary_focus = st.selectbox("Primary Focus", FOCUS_OPTIONS)
            secondary_focus = st.selectbox("Secondary Focus", FOCUS_OPTIONS)
            impacted_emotions = st.multiselect("Impacted Emotions", EMOTION_OPTIONS)
        
        description = st.text_area("Description", value="", height=100)
        
        # MAC Vector
        st.subheader("MAC Vector")
        st.caption("Values must sum to exactly 1.0")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            mac_family = st.number_input("Family", 0.0, 1.0, 0.0, 0.01, format="%.3f", key="new_family")
            mac_group = st.number_input("Group", 0.0, 1.0, 0.0, 0.01, format="%.3f", key="new_group")
        
        with col2:
            mac_reciprocity = st.number_input("Reciprocity", 0.0, 1.0, 0.0, 0.01, format="%.3f", key="new_recip")
            mac_heroism = st.number_input("Heroism", -1.0, 1.0, 0.0, 0.01, format="%.3f", key="new_hero")
        
        with col3:
            mac_deference = st.number_input("Deference", -1.0, 1.0, 0.0, 0.01, format="%.3f", key="new_defer")
            mac_fairness = st.number_input("Fairness", -1.0, 1.0, 0.0, 0.01, format="%.3f", key="new_fair")
        
        with col4:
            mac_property = st.number_input("Property", 0.0, 1.0, 0.0, 0.01, format="%.3f", key="new_prop")
        
        # Calculate and display sum
        mac_sum = mac_family + mac_group + mac_reciprocity + mac_heroism + mac_deference + mac_fairness + mac_property
        
        if abs(mac_sum - 1.0) < 0.0001:
            st.success(f"✅ MAC Vector Sum: {mac_sum:.6f}")
        else:
            st.error(f"❌ MAC Vector Sum: {mac_sum:.6f} (must be 1.0)")
        
        # Rationales
        st.subheader("Rationale")
        
        family_rat = st.text_area("Family Rationale", value="", height=80, key="new_fam_rat")
        group_rat = st.text_area("Group Rationale", value="", height=80, key="new_grp_rat")
        reciprocity_rat = st.text_area("Reciprocity Rationale", value="", height=80, key="new_rec_rat")
        heroism_rat = st.text_area("Heroism Rationale", value="", height=80, key="new_her_rat")
        deference_rat = st.text_area("Deference Rationale", value="", height=80, key="new_def_rat")
        fairness_rat = st.text_area("Fairness Rationale", value="", height=80, key="new_fai_rat")
        property_rat = st.text_area("Property Rationale", value="", height=80, key="new_pro_rat")
        overall_rat = st.text_area("Overall Rationale", value="", height=150, key="new_ovr_rat")
        
        # Form buttons
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submitted = st.form_submit_button("💾 Create Standard", type="primary")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            # Validation
            errors = []
            
            if not std_id:
                errors.append("Standard ID is required")
            elif any(s.id == std_id for s in lib.standards):
                errors.append(f"Standard ID '{std_id}' already exists")
            
            if not name:
                errors.append("Name is required")
            
            if abs(mac_sum - 1.0) >= 0.0001:
                errors.append("MAC vector must sum to 1.0")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Create new standard
                new_standard = Standard(
                    id=std_id,
                    name=name,
                    cluster=cluster,
                    description=description,
                    importance_weight=importance_weight,
                    primary_focus=primary_focus,
                    secondary_focus=secondary_focus,
                    impacted_emotions=impacted_emotions,
                    mac_vector=MACVector(
                        family=mac_family,
                        group=mac_group,
                        reciprocity=mac_reciprocity,
                        heroism=mac_heroism,
                        deference=mac_deference,
                        fairness=mac_fairness,
                        property=mac_property
                    ),
                    rationale=MACRationale(
                        family_rationale=family_rat,
                        group_rationale=group_rat,
                        reciprocity_rationale=reciprocity_rat,
                        heroism_rationale=heroism_rat,
                        deference_rationale=deference_rat,
                        fairness_rationale=fairness_rat,
                        property_rationale=property_rat,
                        overall_rationale=overall_rat
                    )
                )
                
                # Add to library
                lib.standards.append(new_standard)
                
                # Save library
                if st.session_state.file_manager.save_library(lib):
                    st.success(f"✅ Standard '{std_id}' created successfully!")
                    st.balloons()
                else:
                    st.error("❌ Error saving standard")
        
        if cancelled:
            st.rerun()

# Screen 5: Manage Clusters
def screen_manage_clusters():
    """Manage clusters (CRUD operations)"""
    st.title("📂 Manage Clusters")
    
    lib = st.session_state.library
    
    # Display existing clusters
    st.subheader("Existing Clusters")
    
    if lib.clusters:
        cluster_data = []
        for c in sorted(lib.clusters, key=lambda x: x.order):
            cluster_data.append({
                "ID": c.id,
                "Name": c.name,
                "Order": c.order,
                "Standards": len([s for s in lib.standards if s.cluster == c.id])
            })
        
        df = pd.DataFrame(cluster_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No clusters defined")
    
    st.markdown("---")
    
    # Add/Edit cluster
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Add or Edit Cluster")
    
    with col2:
        mode = st.radio("Mode", ["Add New", "Edit Existing"], horizontal=True)
    
    with st.form("cluster_form"):
        if mode == "Edit Existing":
            if not lib.clusters:
                st.warning("No clusters to edit")
                st.form_submit_button("Submit", disabled=True)
            else:
                cluster_options = [c.id for c in lib.clusters]
                selected_cluster_id = st.selectbox("Select Cluster to Edit", cluster_options)
                
                # Find the cluster
                selected_cluster = next(c for c in lib.clusters if c.id == selected_cluster_id)
                
                cluster_id = st.text_input("Cluster ID", value=selected_cluster.id, disabled=True)
                cluster_name = st.text_input("Name", value=selected_cluster.name)
                cluster_desc = st.text_area("Description", value=selected_cluster.description, height=100)
                cluster_order = st.number_input("Order", min_value=1, value=selected_cluster.order)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    submitted = st.form_submit_button("💾 Update Cluster", type="primary")
                with col2:
                    deleted = st.form_submit_button("🗑️ Delete Cluster", type="secondary")
                with col3:
                    cancelled = st.form_submit_button("Cancel")
                
                if submitted:
                    selected_cluster.name = cluster_name
                    selected_cluster.description = cluster_desc
                    selected_cluster.order = cluster_order
                    
                    if st.session_state.file_manager.save_library(lib):
                        st.success("✅ Cluster updated!")
                        st.rerun()
                    else:
                        st.error("❌ Error saving cluster")
                
                if deleted:
                    # Check if cluster has standards
                    standards_in_cluster = [s for s in lib.standards if s.cluster == cluster_id]
                    if standards_in_cluster:
                        st.error(f"❌ Cannot delete cluster '{cluster_id}' - it has {len(standards_in_cluster)} standards")
                    else:
                        lib.clusters = [c for c in lib.clusters if c.id != cluster_id]
                        if st.session_state.file_manager.save_library(lib):
                            st.success("✅ Cluster deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Error deleting cluster")
                
                if cancelled:
                    st.rerun()
        
        else:  # Add New
            cluster_id = st.text_input("Cluster ID", value="")
            cluster_name = st.text_input("Name", value="")
            cluster_desc = st.text_area("Description", value="", height=100)
            
            # Suggest next order
            max_order = max([c.order for c in lib.clusters], default=0)
            cluster_order = st.number_input("Order", min_value=1, value=max_order + 1)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                submitted = st.form_submit_button("➕ Add Cluster", type="primary")
            with col2:
                cancelled = st.form_submit_button("Cancel")
            
            if submitted:
                errors = []
                
                if not cluster_id:
                    errors.append("Cluster ID is required")
                elif any(c.id == cluster_id for c in lib.clusters):
                    errors.append(f"Cluster ID '{cluster_id}' already exists")
                
                if not cluster_name:
                    errors.append("Cluster name is required")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    new_cluster = Cluster(
                        id=cluster_id,
                        name=cluster_name,
                        description=cluster_desc,
                        order=cluster_order
                    )
                    
                    lib.clusters.append(new_cluster)
                    
                    if st.session_state.file_manager.save_library(lib):
                        st.success(f"✅ Cluster '{cluster_id}' created!")
                        st.rerun()
                    else:
                        st.error("❌ Error saving cluster")
            
            if cancelled:
                st.rerun()

# Screen 6: Backup & Restore
def screen_backup_restore():
    """Backup and restore library"""
    st.title("💾 Backup & Restore")
    
    lib = st.session_state.library
    fm = st.session_state.file_manager
    
    # Current library info
    st.subheader("Current Library")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📄 **File:** library.json")
    with col2:
        st.info(f"🕐 **Last Modified:** {lib.last_modified}")
    
    # Create backup
    if st.button("💾 Create Backup Now", type="primary"):
        if fm.create_backup():
            st.success("✅ Backup created successfully!")
            st.rerun()
        else:
            st.error("❌ Error creating backup")
    
    st.markdown("---")
    
    # List existing backups
    st.subheader("Existing Backups")
    
    backups = fm.list_backups()
    
    if backups:
        st.write(f"**{len(backups)} backup(s) available** (maximum 5 kept)")
        
        for i, backup in enumerate(backups, 1):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.text(f"{i}. {backup['filename']}")
            with col2:
                st.text(backup['modified'])
            with col3:
                if st.button("🔄 Restore", key=f"restore_{backup['filename']}"):
                    if fm.restore_backup(backup['filename']):
                        # Reload library
                        st.session_state.library = fm.load_library()
                        st.success("✅ Backup restored successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Error restoring backup")
        
        st.markdown("---")
        
        if st.button("🗑️ Delete All Backups", type="secondary"):
            if fm.delete_all_backups():
                st.success("✅ All backups deleted")
                st.rerun()
            else:
                st.error("❌ Error deleting backups")
    else:
        st.info("No backups available")

# Screen 7: Export
def screen_export():
    """Export library or subset"""
    st.title("📤 Export")
    
    lib = st.session_state.library
    fm = st.session_state.file_manager
    
    st.write("Export library for runtime use or archival purposes")
    
    with st.form("export_form"):
        # Export scope
        st.subheader("Export Scope")
        export_mode = st.radio(
            "What to export:",
            ["Full Library (all standards)", 
             "Subset by Cluster", 
             "Subset by Standard IDs"]
        )
        
        selected_clusters = []
        selected_ids = []
        
        if export_mode == "Subset by Cluster":
            cluster_options = [c.id for c in lib.clusters]
            selected_clusters = st.multiselect(
                "Select clusters to include:",
                cluster_options,
                default=cluster_options[:3] if len(cluster_options) >= 3 else cluster_options
            )
        
        elif export_mode == "Subset by Standard IDs":
            all_ids = [s.id for s in lib.standards]
            ids_text = st.text_area(
                "Enter standard IDs (comma-separated):",
                value=", ".join(all_ids[:5]) if len(all_ids) >= 5 else ", ".join(all_ids),
                height=100
            )
            selected_ids = [id.strip() for id in ids_text.split(",") if id.strip()]
        
        st.markdown("---")
        
        # Export options
        st.subheader("Export Options")
        
        include_rationales = st.checkbox(
            "Include rationales",
            value=False,
            help="Uncheck for runtime exports (smaller file size)"
        )
        
        filename = st.text_input(
            "Export filename:",
            value="export.json"
        )
        
        # Preview
        st.markdown("---")
        st.subheader("Preview")
        
        if export_mode == "Full Library (all standards)":
            st.info(f"Will export all {len(lib.standards)} standards")
        elif export_mode == "Subset by Cluster":
            count = len([s for s in lib.standards if s.cluster in selected_clusters])
            st.info(f"Will export {count} standards from {len(selected_clusters)} cluster(s)")
        else:
            count = len([s for s in lib.standards if s.id in selected_ids])
            st.info(f"Will export {count} standards")
        
        # Submit
        submitted = st.form_submit_button("📤 Export", type="primary")
        
        if submitted:
            # Determine parameters
            cluster_filter = selected_clusters if export_mode == "Subset by Cluster" else None
            id_filter = selected_ids if export_mode == "Subset by Standard IDs" else None
            
            # Export
            if fm.export_library(
                library=lib,
                filename=filename,
                cluster_ids=cluster_filter,
                standard_ids=id_filter,
                include_rationales=include_rationales
            ):
                export_path = fm.exports_dir / filename
                st.success(f"✅ Exported to: {export_path}")
                st.info(f"💡 You can find the file at: {export_path.absolute()}")
            else:
                st.error("❌ Error exporting library")

# Screen 8: Validate Library
def screen_validate():
    """Validate library integrity"""
    st.title("✅ Validate Library")
    
    lib = st.session_state.library
    
    st.write("Check library for errors and inconsistencies")
    
    if st.button("🔍 Run Validation", type="primary"):
        validator = LibraryValidator(lib)
        all_errors = validator.validate_all()
        
        if not all_errors:
            st.success("🎉 Library is valid - no issues found!")
        else:
            errors, warnings = validator.get_errors_by_severity()
            
            # Show errors
            if errors:
                st.error(f"❌ Found {len(errors)} error(s)")
                with st.expander("Show Errors", expanded=True):
                    for error in errors:
                        st.write(str(error))
            else:
                st.success("✅ No errors found")
            
            # Show warnings
            if warnings:
                st.warning(f"⚠️ Found {len(warnings)} warning(s)")
                with st.expander("Show Warnings", expanded=True):
                    for warning in warnings:
                        st.write(str(warning))
            else:
                st.success("✅ No warnings")
            
            # Quick fix button
            if errors or warnings:
                st.markdown("---")
                st.subheader("Quick Actions")
                
                if st.button("📝 Go to Browse & Search to fix issues"):
                    st.session_state.current_screen = "Browse & Search"
                    st.rerun()

# Main application
def main():
    """Main application entry point"""
    
    # Initialize library
    if st.session_state.library is None:
        library_loaded = initialize_library()
        if library_loaded:
            st.success("✅ Library loaded successfully")
        else:
            st.info("📚 Created new empty library")
    
    # Render sidebar and get selected screen
    selected_screen = render_sidebar()
    
    # Check for navigation override (this overrides sidebar selection)
    if 'navigate_to' in st.session_state and st.session_state.navigate_to:
        selected_screen = st.session_state.navigate_to
        st.session_state.navigate_to = None  # Clear after use
    
    # Route to appropriate screen
    if selected_screen == "Library Overview":
        screen_library_overview()
    elif selected_screen == "Browse & Search":
        screen_browse_search()
    elif selected_screen == "Edit Standard":
        screen_edit_standard()
    elif selected_screen == "Create New Standard":
        screen_create_standard()
    elif selected_screen == "Manage Clusters":
        screen_manage_clusters()
    elif selected_screen == "Backup & Restore":
        screen_backup_restore()
    elif selected_screen == "Export":
        screen_export()
    elif selected_screen == "Validate Library":
        screen_validate()
# Run the app
if __name__ == "__main__":
    main()