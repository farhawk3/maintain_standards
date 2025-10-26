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
    
    # --- New Focus Filters ---
    
    focus_filter_mode = st.radio(
        "Filter by Focus Type",
        ["None", "Primary", "Secondary", "Primary or Secondary"],
        horizontal=True,
        index=0
    )
    
    selected_focus = st.selectbox(
        "Focus Value",
        FOCUS_OPTIONS,
        disabled=(focus_filter_mode == "None")
    )
    
    st.markdown("---")
    
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
    
    # Apply new focus filter
    if focus_filter_mode != "None":
        if focus_filter_mode == "Primary":
            filtered_standards = [s for s in filtered_standards if s.primary_focus == selected_focus]
        elif focus_filter_mode == "Secondary":
            filtered_standards = [s for s in filtered_standards if s.secondary_focus == selected_focus]
        elif focus_filter_mode == "Primary or Secondary":
            filtered_standards = [s for s in filtered_standards if s.primary_focus == selected_focus or s.secondary_focus == selected_focus]

    
# Display as table
    if filtered_standards:
        st.write(f"**Showing {len(filtered_standards)} standards**")
        
        # Create cluster name lookup
        cluster_names = {c.id: c.name for c in lib.clusters}
        
        data = []
        for idx, std in enumerate(filtered_standards, start=1):
            data.append({
                "#": str(idx),
                "ID": std.id,
                "Name": std.name,
                "Cluster": cluster_names.get(std.cluster, std.cluster),  # Use name instead of ID
                "Weight": f"{std.importance_weight:.2f}"
            })
        
        df = pd.DataFrame(data)
        original_columns = list(df.columns)
        
        # Add the "Edit" column to the dataframe before passing it to the editor
        df["Edit"] = False
        
        # --- Edit Button and Selection Logic ---
        # Add the button above the table
        edit_button = st.button("✏️ Edit Selected Standard", type="primary")

        # The edited_df will contain the state of the checkboxes after user interaction
        edited_df = st.data_editor(
            df, 
            hide_index=True,
            width='stretch',
            # Disable all original columns to make them read-only
            disabled=original_columns,
            key="standards_table", # Add a key to preserve state on button click
            column_config={
                "#": st.column_config.TextColumn("#", width=40, help="Row number"),
                "ID": st.column_config.TextColumn(width=80),
                "Name": st.column_config.TextColumn(width=300),
                "Cluster": st.column_config.TextColumn(width=200),
                "Weight": st.column_config.TextColumn(width=70),
                "Edit": st.column_config.CheckboxColumn("Edit", help="Select a standard to edit", default=False)
            }
        )
        
        if edit_button:
            selected_indices = edited_df.index[edited_df['Edit']].tolist()
            
            if selected_indices:
                selected_index = selected_indices[0]
                selected_standard = filtered_standards[selected_index]
                st.session_state.selected_standard = selected_standard
                st.rerun()
            else:
                st.warning("Please select a standard from the table first.")
    else:
        st.info("No standards match your filters")

# --- Refactored Form Component ---

def render_standard_form_body(
    lib: Library, 
    standard: Optional[Standard] = None, 
    key_prefix: str = ""
) -> dict:
    """
    Renders the main body of the standard create/edit form using tabs.
    Returns a dictionary of the entered values.
    """
    is_new = standard is None
    
    # Use provided standard or create empty objects for the form
    std = standard if standard else Standard(id="", name="", cluster="")
    mac = std.mac_vector
    rat = std.rationale

    form_data = {}

    # --- TABS FOR FORM ORGANIZATION ---
    tab1, tab2, tab3 = st.tabs(["Core Details", "MAC Vector", "Rationales"])

    with tab1:
        st.subheader("Core Details")
        col1, col2 = st.columns(2)
        with col1:
            # Cluster selection
            cluster_dict = {f"({c.id}) {c.name}": c.id for c in lib.clusters}
            cluster_options = list(cluster_dict.keys())
            current_cluster_formatted = next((k for k, v in cluster_dict.items() if v == std.cluster), None)
            cluster_index = cluster_options.index(current_cluster_formatted) if current_cluster_formatted else 0
            
            cluster_display = st.selectbox(
                "Cluster", cluster_options, index=cluster_index, key=f"{key_prefix}cluster"
            )
            form_data["cluster"] = cluster_dict[cluster_display]

            form_data["name"] = st.text_input("Name", value=std.name, key=f"{key_prefix}name")
            form_data["importance_weight"] = st.slider(
                "Importance Weight (wbase)", 0.0, 1.0, float(std.importance_weight), 0.05, key=f"{key_prefix}weight"
            )

        with col2:
            # Clean the data before finding the index to prevent crashes on dirty data
            p_focus_clean = std.primary_focus.strip()
            form_data["primary_focus"] = st.selectbox(
                "Primary Focus", FOCUS_OPTIONS, 
                index=FOCUS_OPTIONS.index(p_focus_clean) if p_focus_clean in FOCUS_OPTIONS else 0,
                key=f"{key_prefix}p_focus"
            )
            s_focus_clean = std.secondary_focus.strip()
            form_data["secondary_focus"] = st.selectbox(
                "Secondary Focus", FOCUS_OPTIONS,
                index=FOCUS_OPTIONS.index(s_focus_clean) if s_focus_clean in FOCUS_OPTIONS else 0,
                key=f"{key_prefix}s_focus"
            )
            # Filter default emotions to only include valid options, preventing crashes on dirty data
            valid_default_emotions = [e for e in std.impacted_emotions if e in EMOTION_OPTIONS]
            form_data["impacted_emotions"] = st.multiselect(
                "Impacted Emotion Dimensions", EMOTION_OPTIONS, default=valid_default_emotions, key=f"{key_prefix}emotions"
            )

        form_data["description"] = st.text_area("Description", value=std.description, height=120, key=f"{key_prefix}desc")

    with tab2:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            family = st.number_input("Family", 0.0, 1.0, float(mac.family), 0.01, format="%.2f", key=f"{key_prefix}mac_fam")
            group = st.number_input("Group", 0.0, 1.0, float(mac.group), 0.01, format="%.2f", key=f"{key_prefix}mac_grp")
        with col2:
            reciprocity = st.number_input("Reciprocity", 0.0, 1.0, float(mac.reciprocity), 0.01, format="%.2f", key=f"{key_prefix}mac_rec")
            heroism = st.number_input("Heroism", -1.0, 1.0, float(mac.heroism), 0.01, format="%.2f", key=f"{key_prefix}mac_her")
        with col3:
            deference = st.number_input("Deference", -1.0, 1.0, float(mac.deference), 0.01, format="%.2f", key=f"{key_prefix}mac_def")
            fairness = st.number_input("Fairness", -1.0, 1.0, float(mac.fairness), 0.01, format="%.2f", key=f"{key_prefix}mac_fai")
        with col4:
            property_val = st.number_input("Property", 0.0, 1.0, float(mac.property), 0.01, format="%.2f", key=f"{key_prefix}mac_pro")

        form_data["mac_vector"] = MACVector(family, group, reciprocity, heroism, deference, fairness, property_val)

        # --- Header and Sum Validation (rendered after inputs) ---
        vec = form_data["mac_vector"]
        vector_str = (
            f"[{vec.family:.2f}, {vec.group:.2f}, {vec.reciprocity:.2f}, "
            f"{vec.heroism:.2f}, {vec.deference:.2f}, {vec.fairness:.2f}, "
            f"{vec.property:.2f}]"
        )
        
        header_col, sum_col = st.columns([3, 1])
        with header_col:
            # Use markdown with HTML for better control over color and alignment
            st.markdown(f'<h3>MAC Vector = <code style="color: black; font-weight: normal;">{vector_str}</code></h3>', unsafe_allow_html=True)
        with sum_col:
            mac_sum = vec.sum()
            if abs(mac_sum - 1.0) < 0.001: # Loosen tolerance for 2-digit precision
                st.success(f"Sum: {mac_sum:.2f}")
            else:
                st.error(f"Sum: {mac_sum:.2f}")

    with tab3:
        st.subheader("Rationale")
        family_rat = st.text_area("Family Rationale", value=rat.family_rationale, height=80, key=f"{key_prefix}rat_fam")
        group_rat = st.text_area("Group Rationale", value=rat.group_rationale, height=80, key=f"{key_prefix}rat_grp")
        reciprocity_rat = st.text_area("Reciprocity Rationale", value=rat.reciprocity_rationale, height=80, key=f"{key_prefix}rat_rec")
        heroism_rat = st.text_area("Heroism Rationale", value=rat.heroism_rationale, height=80, key=f"{key_prefix}rat_her")
        deference_rat = st.text_area("Deference Rationale", value=rat.deference_rationale, height=80, key=f"{key_prefix}rat_def")
        fairness_rat = st.text_area("Fairness Rationale", value=rat.fairness_rationale, height=80, key=f"{key_prefix}rat_fai")
        property_rat = st.text_area("Property Rationale", value=rat.property_rationale, height=80, key=f"{key_prefix}rat_pro")
        overall_rat = st.text_area("Overall Rationale", value=rat.overall_rationale, height=150, key=f"{key_prefix}rat_ovr")

        form_data["rationale"] = MACRationale(
            family_rat, group_rat, reciprocity_rat, heroism_rat, 
            deference_rat, fairness_rat, property_rat, overall_rat
        )

    return form_data

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
            # This button is now redundant as there's no selected_standard
            pass
        return
    
    # Now we know selected is not None, safe to access its properties
    st.markdown(f"### Editing: ({selected.id}) {selected.name}")
    
    # Find the actual standard in library (in case it's been modified)
    try:
        std_index = next(i for i, s in enumerate(lib.standards) if s.id == selected.id)
        std = lib.standards[std_index]
    except StopIteration:
        st.error(f"Standard '{selected.id}' not found in library")
        if st.button("← Back to Browse"):
            st.session_state.selected_standard = None # Clear selection
            st.rerun()
        return
    
    # Create form
    with st.form("edit_standard_form"):
        st.text_input("Standard ID", value=std.id, disabled=True)
        
        # Render the main form body using the refactored function
        form_data = render_standard_form_body(lib, std, key_prefix=f"{std.id}_")
        
        # Form buttons
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            # Validate MAC sum
            if not form_data["mac_vector"].is_valid():
                st.error("Cannot save: MAC vector must sum to 1.0")
            else:
                # Update standard
                std.name = form_data["name"]
                std.cluster = form_data["cluster"]
                std.description = form_data["description"]
                std.importance_weight = form_data["importance_weight"]
                std.primary_focus = form_data["primary_focus"]
                std.secondary_focus = form_data["secondary_focus"]
                std.impacted_emotions = form_data["impacted_emotions"]
                std.mac_vector = form_data["mac_vector"]
                std.rationale = form_data["rationale"]
                std.date_modified = datetime.now().strftime("%Y-%m-%d")
                
                # Save library
                if st.session_state.file_manager.save_library(lib):
                    st.success("✅ Standard saved successfully!")
                    st.session_state.selected_standard = None # Clear selection to navigate back
                    st.rerun()
                else:
                    st.error("❌ Error saving standard")
        
        if cancelled:
            st.session_state.selected_standard = None # Clear selection to navigate back
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

        # Render the main form body using the refactored function
        form_data = render_standard_form_body(lib, standard=None, key_prefix="new_")
        
        # ID suggestion logic (can't be inside the general form function)
        cluster = form_data["cluster"]
        existing_ids = [s.id for s in lib.standards if s.cluster == cluster]
        if existing_ids:
            numbers = [int(p[1]) for id_str in existing_ids if (p := id_str.split('-')) and len(p) == 2 and p[1].isdigit()]
            next_num = max(numbers) + 1 if numbers else 1
            suggested_id = f"{cluster}-{next_num}"
        else:
            suggested_id = f"{cluster}-1"
        
        std_id = st.text_input("Standard ID", value=suggested_id)
        
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
            
            if not form_data["name"]:
                errors.append("Name is required")
            
            if not form_data["mac_vector"].is_valid():
                errors.append("MAC vector must sum to 1.0")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Create new standard from form data
                new_standard = Standard(
                    id=std_id,
                    name=form_data["name"],
                    cluster=form_data["cluster"],
                    description=form_data["description"],
                    importance_weight=form_data["importance_weight"],
                    primary_focus=form_data["primary_focus"],
                    secondary_focus=form_data["secondary_focus"],
                    impacted_emotions=form_data["impacted_emotions"],
                    mac_vector=form_data["mac_vector"],
                    rationale=form_data["rationale"]
                )
                
                # Add to library
                lib.standards.append(new_standard)
                
                # Save library
                if st.session_state.file_manager.save_library(lib):
                    st.success(f"✅ Standard '{std_id}' created successfully!")
                    st.balloons()
                    # Rerun to clear form
                    st.rerun()
                else:
                    st.error("❌ Error saving standard")
        
        if cancelled:
            # Rerun to clear form
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
        st.dataframe(
            df, 
            width='stretch',
            column_config={
                "ID": st.column_config.TextColumn(width="small"),
                "Name": st.column_config.TextColumn(width="large"),
                "Order": st.column_config.NumberColumn(width="small"),
                "Standards": st.column_config.NumberColumn(width="medium", help="Number of standards in this cluster"),
            })
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
        
        st.markdown("---")
        st.subheader("Data Cleanup Utility")
        st.warning("This will permanently modify your `library.json` file. It's recommended to create a backup first.")
        
        if st.button("🧹 Clean Data Issues", type="secondary"):
            run_data_cleanup(lib)

def run_data_cleanup(lib: Library):
    """
    Scans the library for known data issues and corrects them.
    - Corrects "Praiseworthy" to "Praiseworthiness".
    - Removes invalid emotions like "Consequence".
    """
    st.write("Starting data cleanup...")
    
    modified_count = 0
    messages = []
    
    # Define the mapping for known corrections
    cleanup_map = {"Praiseworthy": "Praiseworthiness"}
    valid_emotions = set(EMOTION_OPTIONS)

    for std in lib.standards:
        original_emotions = std.impacted_emotions
        cleaned_emotions = set()
        
        for emotion in original_emotions:
            if emotion in cleanup_map:
                cleaned_emotions.add(cleanup_map[emotion])
            elif emotion in valid_emotions:
                cleaned_emotions.add(emotion)
        
        # Check if changes were made
        if set(original_emotions) != cleaned_emotions:
            modified_count += 1
            messages.append(f"**{std.id}**: Corrected emotions from `{original_emotions}` to `{sorted(list(cleaned_emotions))}`")
            std.impacted_emotions = sorted(list(cleaned_emotions))

    if modified_count > 0:
        if st.session_state.file_manager.save_library(lib):
            st.success(f"✅ Cleanup complete! Modified {modified_count} standard(s).")
            with st.expander("Show Details", expanded=True):
                for msg in messages:
                    st.markdown(f"- {msg}")
            st.info("Reloading the app to reflect changes...")
            st.rerun()
        else:
            st.error("❌ Error saving the cleaned library file.")
    else:
        st.success("✅ No data issues found to clean.")

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
    
    # --- Main Content Routing ---
    # If a standard is selected, ALWAYS show the edit screen.
    # This is the core of the new, simplified navigation.
    if st.session_state.selected_standard:
        screen_edit_standard()
    else:
        # Otherwise, show the screen selected in the sidebar.
        screen_map = {
            "Library Overview": screen_library_overview,
            "Browse & Search": screen_browse_search,
            "Create New Standard": screen_create_standard,
            "Manage Clusters": screen_manage_clusters,
            "Backup & Restore": screen_backup_restore,
            "Export": screen_export,
            "Validate Library": screen_validate,
        }
        screen_function = screen_map.get(selected_screen, screen_library_overview)
        screen_function()
# Run the app
if __name__ == "__main__":
    main()