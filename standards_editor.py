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

# --- Session State Initialization ---
# Ensures that the app's state is preserved across user interactions.
if 'library' not in st.session_state:
    st.session_state.library = None
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = FileManager()
if 'selected_standard' not in st.session_state:
    st.session_state.selected_standard = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

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
    st.sidebar.title("📚 Moral Standards Catalog")
    if st.session_state.library:
        # Inject CSS to override the default grey color of the caption
        st.sidebar.markdown("""
            <style>
                div[data-testid="stSidebar"] div[data-testid="stCaption"] {
                    color: black !important;
                }
            </style>
        """, unsafe_allow_html=True)
        st.sidebar.caption(f"Version: {st.session_state.library.version}")
    st.sidebar.markdown("---")
    
    menu_options = [
        "Standards",
        "Clusters",
        "Create New Standard",
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

def render_browse_pane():
    """Browse and search standards"""
    st.header("📚 Moral Standards")
    
    lib = st.session_state.library
    
    if not lib or not lib.standards:
        st.info("No standards in library yet. Create one to get started!")
        return
    
    # Filters
    cluster_dict = {f"({c.id}) {c.name}": c.id for c in lib.clusters}
    cluster_options = ["All"] + list(cluster_dict.keys())
    
    selected_cluster_display = st.selectbox("Filter by Cluster", cluster_options)
    
    if selected_cluster_display == "All":
        selected_cluster = "All"
    else:
        selected_cluster = cluster_dict[selected_cluster_display]
    
    selected_focus = st.selectbox(
        "Focus Value",
        FOCUS_OPTIONS
    )
    
    focus_filter_mode = st.radio(
        "Filter by Appraisal Focus Type",
        ["None", "Primary", "Secondary", "Primary or Secondary"],
        horizontal=True,
        index=0
    )
    
    st.markdown("---")
    
    # Filter standards
    filtered_standards = lib.standards
    
    if selected_cluster != "All":
        filtered_standards = [s for s in filtered_standards if s.cluster == selected_cluster]
    
    if focus_filter_mode != "None":
        if focus_filter_mode == "Primary":
            filtered_standards = [s for s in filtered_standards if s.primary_focus == selected_focus]
        elif focus_filter_mode == "Secondary":
            filtered_standards = [s for s in filtered_standards if s.secondary_focus == selected_focus]
        elif focus_filter_mode == "Primary or Secondary":
            filtered_standards = [s for s in filtered_standards if s.primary_focus == selected_focus or s.secondary_focus == selected_focus]

    # Display as table
    if filtered_standards:
        # Create a mapping from a display format to the standard ID
        # This makes the radio button display text informative but gives us the ID back
        options_map = {f"`{s.id}` - {s.name}": s.id for s in filtered_standards}
        
        # Find the index of the currently selected standard to set the default
        current_selection_id = st.session_state.get('selected_standard')
        # Create a list of IDs in the order they appear in the map
        ids_list = list(options_map.values())
        index = ids_list.index(current_selection_id) if current_selection_id in ids_list else 0

        selected_display_name = st.radio(
            "Select a standard to view/edit:",
            options=options_map.keys(),
            index=index,
            key="standard_selector"
        )
        
        # When a new item is selected, update the session state and rerun
        if selected_display_name and options_map[selected_display_name] != current_selection_id:
            st.session_state.selected_standard = options_map[selected_display_name]
            st.session_state.edit_mode = False
            st.rerun()
    else:
        st.info("No standards match your filters")

# --- Form Component Refactoring ---
# The `render_standard_form_body` has been broken into smaller, more manageable functions.

def _render_form_tab_core(lib: Library, std: Standard, key_prefix: str, form_data: dict):
    """Renders the 'Core Details' tab for the standard form."""
    st.subheader("Core Details")
    cluster_dict = {f"({c.id}) {c.name}": c.id for c in lib.clusters}
    cluster_options = sorted(list(cluster_dict.keys()))
    current_cluster_formatted = next((k for k, v in cluster_dict.items() if v == std.cluster), None)
    cluster_index = cluster_options.index(current_cluster_formatted) if current_cluster_formatted else 0
    
    cluster_display = st.selectbox("Cluster", cluster_options, index=cluster_index, key=f"{key_prefix}cluster")
    form_data["cluster"] = cluster_dict[cluster_display]

    form_data["name"] = st.text_input("Name", value=st.session_state.get(f"{key_prefix}name", std.name), key=f"{key_prefix}name")
    form_data["importance_weight"] = st.number_input(
        "Importance Weight (wbase)",
        min_value=0.0,
        max_value=1.0,
        value=float(st.session_state.get(f"{key_prefix}weight", std.importance_weight)),
        step=0.05,
        format="%.2f",
        key=f"{key_prefix}weight"
    )

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

def _render_form_tab_mac(std: Standard, key_prefix: str, form_data: dict):
    """Renders the combined 'MAC Vector' tab for the standard form."""
    mac = std.mac_vector
    rat = std.rationale
    st.subheader("MAC Vector")

    # Display the non-editable vector string, just like in view mode
    vector_str = (f"[{mac.family:.2f}, {mac.group:.2f}, {mac.reciprocity:.2f}, "f"{mac.heroism:.2f}, {mac.deference:.2f}, {mac.fairness:.2f}, "
                  f"{mac.property:.2f}]")
    st.markdown(f'<h4>MAC Vector: <code>{vector_str}</code></h4>', unsafe_allow_html=True)


    # Define the fields to iterate over for both vector and rationale
    mac_fields = [
        # (Label, Vector Attr, Rationale Attr, Vector Key, Rationale Key, Min Val)
        ("Family", "family", "family_rationale", "mac_fam", "rat_fam", 0.0),
        ("Group", "group", "group_rationale", "mac_grp", "rat_grp", 0.0),
        ("Reciprocity", "reciprocity", "reciprocity_rationale", "mac_rec", "rat_rec", 0.0),
        ("Heroism", "heroism", "heroism_rationale", "mac_her", "rat_her", -1.0),
        ("Deference", "deference", "deference_rationale", "mac_def", "rat_def", -1.0),
        ("Fairness", "fairness", "fairness_rationale", "mac_fai", "rat_fai", -1.0),
        ("Property", "property", "property_rationale", "mac_pro", "rat_pro", 0.0),
    ]

    # Dictionaries to hold the form values
    vector_values = {}
    rationale_values = {}

    # Use a single HTML block with a bottom border to create the line, eliminating extra space.
    st.markdown("""
        <style>
            .header-with-border {
                display: grid;
                grid-template-columns: 1fr 1fr 4.5fr;
                font-weight: bold;
                border-bottom: 1px solid #cccccc; /* Use a border instead of <hr> */
            }
        </style>
        <div class="header-with-border">
            <div>Dimension</div>
            <div>Value</div>
            <div>Rationale</div>
        </div>
    """, unsafe_allow_html=True)

    for label, vec_attr, rat_attr, vec_key, rat_key, min_val in mac_fields:
        col1, col2, col3 = st.columns([1, 1, 4.5])
        with col1:
            # Display the label, vertically centered and right-aligned.
            st.markdown(f'<div style="height: 100px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px;"><b>{label}</b></div>', unsafe_allow_html=True)
        with col2:
            # Add top padding to the number input to vertically center it.
            st.markdown('<div style="padding-top: 29px;">', unsafe_allow_html=True)
            vector_values[vec_attr] = st.number_input(
                label, min_val, 1.0, getattr(mac, vec_attr), 0.01,
                format="%.2f", key=f"{key_prefix}{vec_key}", label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            rationale_values[rat_attr] = st.text_area(
                label, value=getattr(rat, rat_attr), height=100, 
                key=f"{key_prefix}{rat_key}", label_visibility="collapsed"
            )

    form_data["mac_vector"] = MACVector(**vector_values)
    form_data["rationale"] = MACRationale(**rationale_values)

def render_standard_form_body(lib: Library, standard: Optional[Standard] = None, key_prefix: str = "") -> dict:
    """
    Renders the main body of the standard create/edit form using tabs.
    Returns a dictionary of the entered values.
    """
    std = standard if standard else Standard(id="", name="", cluster="")
    form_data = {}

    tab1, tab2 = st.tabs(["Core Details", "MAC Vector"])
    with tab1:
        _render_form_tab_core(lib, std, key_prefix, form_data)
    with tab2:
        _render_form_tab_mac(std, key_prefix, form_data)

    return form_data

# --- Callback Functions ---

def exit_edit_mode():
    """Callback to set edit_mode to False."""
    st.session_state.edit_mode = False

def save_and_exit_edit_mode_callback():    
    """
    Callback to robustly save the standard by reading all values
    from session_state and then exiting edit mode.
    """    
    lib = st.session_state.library    
    std_id = st.session_state.selected_standard
    std = next((s for s in lib.standards if s.id == std_id), None)
    if not std:
        st.error(f"Could not find standard {std_id} to save.")
        return

    key_prefix = f"{std.id}_"

    # Importance Weight validation
    importance_weight = st.session_state.get(f"{key_prefix}weight", std.importance_weight)
    if not (0.0 <= importance_weight <= 1.0):
        st.error("Save failed: Importance Weight must be between 0.0 and 1.0.")
        # Remain in edit mode to allow correction
        return

    # MAC Vector validation and data retrieval
    mac_vector = MACVector(
        family=st.session_state.get(f"{key_prefix}mac_fam", std.mac_vector.family),
        group=st.session_state.get(f"{key_prefix}mac_grp", std.mac_vector.group),
        reciprocity=st.session_state.get(f"{key_prefix}mac_rec", std.mac_vector.reciprocity),
        heroism=st.session_state.get(f"{key_prefix}mac_her", std.mac_vector.heroism),
        deference=st.session_state.get(f"{key_prefix}mac_def", std.mac_vector.deference),
        fairness=st.session_state.get(f"{key_prefix}mac_fai", std.mac_vector.fairness),
        property=st.session_state.get(f"{key_prefix}mac_pro", std.mac_vector.property)
    )

    if not mac_vector.is_valid():
        st.error("Save failed: MAC vector must sum to 1.0. Please correct the values.")
        # By not setting edit_mode to False, the user remains in the form to correct the error.
        return

    # If valid, proceed with updating all fields
    std.name = st.session_state.get(f"{key_prefix}name", std.name)
    # Description is now read from the form_data dict, which gets it from the Core Details tab
    std.description = st.session_state.get(f"{key_prefix}desc", std.description)    
    std.importance_weight = importance_weight
    std.primary_focus = st.session_state.get(f"{key_prefix}p_focus", std.primary_focus)
    std.secondary_focus = st.session_state.get(f"{key_prefix}s_focus", std.secondary_focus)
    std.impacted_emotions = st.session_state.get(f"{key_prefix}emotions", std.impacted_emotions)
    
    cluster_display_val = st.session_state.get(f"{key_prefix}cluster")
    cluster_id_map = {f"({c.id}) {c.name}": c.id for c in lib.clusters}
    if cluster_display_val in cluster_id_map:
        std.cluster = cluster_id_map[cluster_display_val]

    std.mac_vector = mac_vector
    # Rationales are already updated via session_state in render_standard_form_body
    std.rationale = MACRationale( # Reconstruct rationale from session state
        family_rationale=st.session_state.get(f"{key_prefix}rat_fam", std.rationale.family_rationale),
        group_rationale=st.session_state.get(f"{key_prefix}rat_grp", std.rationale.group_rationale),
        reciprocity_rationale=st.session_state.get(f"{key_prefix}rat_rec", std.rationale.reciprocity_rationale),
        heroism_rationale=st.session_state.get(f"{key_prefix}rat_her", std.rationale.heroism_rationale),
        deference_rationale=st.session_state.get(f"{key_prefix}rat_def", std.rationale.deference_rationale),
        fairness_rationale=st.session_state.get(f"{key_prefix}rat_fai", std.rationale.fairness_rationale),
        property_rationale=st.session_state.get(f"{key_prefix}rat_pro", std.rationale.property_rationale),
    )

    std.date_modified = datetime.now().strftime("%Y-%m-%d")
    
    if st.session_state.file_manager.save_library(lib):
        st.success("✅ Standard saved successfully!")
        st.session_state.edit_mode = False # This is the crucial line that needs to be in the callback
    else:
        st.error("❌ Error saving standard")


def render_detail_pane():
    """
    Renders the right-hand pane for viewing or editing a standard.
    """
    lib = st.session_state.library
    selected_id = st.session_state.get('selected_standard')
    is_editing = st.session_state.get('edit_mode', False)

    if not selected_id:
        st.info("Select a standard from the list to view its details.")
        return

    # Find the selected standard object from the library
    try:
        std = next(s for s in lib.standards if s.id == selected_id)
    except StopIteration:
        st.error(f"Standard '{selected_id}' not found. It may have been deleted.")
        st.session_state.selected_standard = None
        st.rerun()
        return

    # --- Custom Tab Styling ---
    # Inject CSS to change the background color of the tabs.
    st.markdown("""
        <style>
            /* Target the tab container's bottom border */
            div[data-baseweb="tab-list"] {
                border-bottom: 2px solid #cccccc !important;
            }
            /* Style for inactive tabs */
            button[data-baseweb="tab"][aria-selected="false"] {
                background-color: #f0f2f6 !important;
                border-bottom-width: 0 !important;
            }
            /* Style for the active tab to make it blend with the content area */
            button[data-baseweb="tab"][aria-selected="true"] {
                background-color: white !important;
                border-bottom-width: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Detail Pane Header ---
    st.markdown("""
        <style>
        .centered-header { text-align: center; }
        </style>
        <h2 class="centered-header">Standard Detail</h2>
    """, unsafe_allow_html=True)
    st.markdown(f'<h2 style="color: black;">{std.name} ({std.id})</h2>', unsafe_allow_html=True)
    st.toggle("Edit Mode", key="edit_mode")    

    if is_editing:
        # --- EDIT MODE ---    
        # Inject CSS to change the background color of the text area
        st.markdown("""
            <style>
                /* Target all text, number, and select box inputs in edit mode */
                textarea,
                div[data-baseweb="input"] > div:first-child,
                div[data-testid="stSelectbox"] > div,
                div[data-testid="stMultiSelect"] > div:first-child > div:first-child
                {
                    background-color: #E6F3FF !important;
                }
            </style>
        """, unsafe_allow_html=True)
        # Use JavaScript to forcefully style the Cluster selectbox after rendering
        # This is a more robust method to overcome Streamlit's style overrides.
        # NOTE: Using standard string concatenation to avoid f-string issues with JS curly braces.
        js_code = """
        <script>
            const observer = new MutationObserver((mutations, obs) => {
                // Find the parent element of the "Cluster" label
                const labelElement = Array.from(document.querySelectorAll("label")).find(el => el.textContent === "Cluster");
                if (labelElement && labelElement.parentElement) {
                    // Find the selectbox input within that parent
                    const selectBox = labelElement.parentElement.querySelector('div[data-testid="stSelectbox"] > div');
                    if (selectBox) {
                        selectBox.style.backgroundColor = '#E6F3FF';
                        obs.disconnect(); // Stop observing once we've applied the style
                    }
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
        </script>
        """
        st.components.v1.html(js_code, height=0)
        # Use a negative top margin to remove the whitespace above the form
        st.markdown("""
            <style>
                div[data-testid="stForm"] { margin-top: -2rem; }
            </style>
        """, unsafe_allow_html=True)
        with st.form("edit_standard_form"):
            st.markdown("<b>Description</b>", unsafe_allow_html=True)
            st.text_area("Description", value=std.description, height=120, key=f"{std.id}_desc", label_visibility="collapsed")
            render_standard_form_body(lib, std, key_prefix=f"{std.id}_")
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                st.form_submit_button("💾 Save", type="primary", on_click=save_and_exit_edit_mode_callback)
            with col2:
                st.form_submit_button("Cancel", on_click=exit_edit_mode)
    else:
        # --- VIEW MODE ---        
        # Define a CSS class for our container. We target the container via its data-testid.
        st.markdown("""
            <style>
                div[data-testid="stVerticalBlock"]:has(div.view-mode-content) {
                    border: 1px solid #cccccc;
                    border-radius: 0.5rem;
                    padding: 1rem;
                }
            </style>
        """, unsafe_allow_html=True)

        # Use a native Streamlit container to wrap the content
        with st.container():
            # Add a marker div to identify this container for styling
            st.markdown('<div class="view-mode-content"></div>', unsafe_allow_html=True)

            st.markdown("<b>Description</b>", unsafe_allow_html=True)
            # Use custom CSS to match the background color of the edit mode's text_area
            st.markdown(f"""
                <div style="background-color: #E6F3FF; border-radius: 0.5rem; padding: 10px; border: 1px solid #E6F3FF;">
                    {std.description}
                </div>
                <br>
            """, unsafe_allow_html=True)
            
            # Use st.tabs for a clean, consistent view
            tab1, tab2 = st.tabs(["Core Details", "MAC Vector"])

            with tab1:
                cluster_dict = {c.id: f"({c.id}) {c.name}" for c in lib.clusters}
                cluster_display_value = cluster_dict.get(std.cluster, f"{std.cluster} (Unknown)")
                emotions_str = ", ".join(std.impacted_emotions) if std.impacted_emotions else "N/A"

                # Use an HTML table for precise alignment
                # Labels are in the right-aligned first column, values in the left-aligned second column
                details_html = f"""
                <style>
                    .details-table {{ width: 100%; border-collapse: collapse; }}
                    .details-table td {{ padding: 4px; vertical-align: top; }}
                    .details-label {{ text-align: right; font-weight: bold; padding-right: 10px; width: 30%; }}
                    .details-value {{ text-align: left; font-size: 1.1em; color: darkblue; font-weight: 600; }}
                </style>
                <table class="details-table">
                    <tr><td class="details-label">Cluster:</td><td class="details-value">{cluster_display_value}</td></tr>
                    <tr><td class="details-label">Importance Weight:</td><td class="details-value">{std.importance_weight}</td></tr>
                    <tr><td class="details-label">Name:</td><td class="details-value">{std.name}</td></tr>
                    <tr><td class="details-label">Primary Focus:</td><td class="details-value">{std.primary_focus}</td></tr>
                    <tr><td class="details-label">Secondary Focus:</td><td class="details-value">{std.secondary_focus}</td></tr>
                    <tr><td class="details-label">Impacted Emotions:</td><td class="details-value">{emotions_str}</td></tr>
                </table>
                """
                
                st.markdown(details_html, unsafe_allow_html=True)

            with tab2:
                st.subheader("MAC Vector")
                vec = std.mac_vector
                rat = std.rationale
                vector_str = (f"[{vec.family:.2f}, {vec.group:.2f}, {vec.reciprocity:.2f}, "f"{vec.heroism:.2f}, {vec.deference:.2f}, {vec.fairness:.2f}, "
                    f"{vec.property:.2f}]"
                )

                # Display vector string with reduced bottom margin
                st.markdown(f"""
                    <style>
                        .mac-vector-h4 {{ margin-bottom: 0.25rem; }}
                    </style>
                    <h4 class="mac-vector-h4">MAC Vector: <code>{vector_str}</code></h4>
                """, unsafe_allow_html=True)

                # Use a single HTML block with a bottom border to create the line, eliminating extra space.
                st.markdown("""
                    <style>
                        .header-with-border {
                            display: grid;
                            grid-template-columns: 1fr 0.5fr 5fr;
                            font-weight: bold;
                            border-bottom: 1px solid #cccccc; /* Use a border instead of <hr> */
                        }
                        /* Center the first column header ("Dimension") */
                        .header-with-border div:first-child {
                            text-align: center;
                        }
                        /* Style for the rationale column in view mode */
                        .rationale-view-column {
                            font-size: 1.1em; color: darkblue;
                        }
                        .vertically-centered {
                            /* Use flexbox for true vertical centering */
                            display: flex;
                            align-items: start; /* Changed to start to debug */
                            height: 100%; /* Ensure the container fills the column height */
                        }
                    </style>
                    <div class="header-with-border">
                        <div>Dimension</div>
                        <div>Value</div>
                        <div>Rationale</div>
                    </div>
                """, unsafe_allow_html=True)

                mac_fields = [
                    ("Family", vec.family, rat.family_rationale),
                    ("Reciprocity", vec.reciprocity, rat.reciprocity_rationale),
                    ("Heroism", vec.heroism, rat.heroism_rationale),
                    ("Deference", vec.deference, rat.deference_rationale),
                    ("Fairness", vec.fairness, rat.fairness_rationale),
                    ("Property", vec.property, rat.property_rationale),
                ]

                for label, value, rationale_text in mac_fields:
                    # Use a container for each row to apply bottom margin for spacing
                    with st.container():
                        col1, col2, col3 = st.columns([1, 0.5, 5])

                        # Column 1: Dimension (centered)
                        col1.markdown(f'<div style="text-align: center;"><b>{label}</b></div>', unsafe_allow_html=True)

                        # Column 2: Value (styled)
                        value_style = "font-size: 1.1em; color: darkblue; font-weight: 600;"
                        col2.markdown(f'<div style="{value_style}">{value:.2f}</div>', unsafe_allow_html=True)

                        # Column 3: Rationale (styled container with direct markdown rendering)
                        col3.markdown(rationale_text or "_N/A_") # This renders the markdown

# Screen 3: Manage Clusters
def screen_manage_clusters(): # Renamed from screen_create_standard
    """Manage clusters (CRUD operations)"""
    st.title("📂 Manage Clusters")
    
    lib = st.session_state.library

    # Use columns to constrain the width of the content on this page
    left_spacer, content_col, right_spacer = st.columns([1, 2, 1])

    with content_col:
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
            # Reorder columns to have "Order" first for better readability
            df = df[['Order', 'ID', 'Name', 'Standards']]

            st.dataframe(
                df, 
                hide_index=True,
                use_container_width=True,
                column_config={
                    "ID": st.column_config.TextColumn(width="small"),
                    "Name": st.column_config.TextColumn(width="large"),
                    "Order": st.column_config.NumberColumn(width="small"),
                    "Standards": st.column_config.TextColumn(
                        width="small", help="Number of standards in this cluster"
                    ),
                })
        else:
            st.info("No clusters defined")
        
        st.markdown("---")
        
        # Add/Edit cluster
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Add or Edit Cluster")
        
        with col2:
            mode = st.radio("Mode", ["Add New", "Edit Existing"], horizontal=True, key="cluster_mode")
        
        with st.form("cluster_form"):
            if mode == "Edit Existing":
                if not lib.clusters:
                    st.warning("No clusters to edit")
                    st.form_submit_button("Submit", disabled=True)
                else:
                    cluster_options = {c.id: f"({c.id}) {c.name}" for c in lib.clusters}
                    selected_cluster_id = st.selectbox(
                        "Select Cluster to Edit", 
                        cluster_options.keys(), 
                        format_func=lambda x: cluster_options[x]
                    )
                    
                    selected_cluster = next(c for c in lib.clusters if c.id == selected_cluster_id)
                    
                    cluster_id = st.text_input("Cluster ID", value=selected_cluster.id, disabled=True)
                    cluster_name = st.text_input("Name", value=selected_cluster.name)
                    cluster_desc = st.text_area("Description", value=selected_cluster.description, height=100)
                    cluster_order = st.number_input("Order", min_value=1, value=selected_cluster.order)
                    
                    col1, col2, col3 = st.columns([1,1,2])
                    with col1:
                        submitted = st.form_submit_button("💾 Update", type="primary")
                    with col2:
                        deleted = st.form_submit_button("🗑️ Delete")
                    
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
                        standards_in_cluster = [s for s in lib.standards if s.cluster == cluster_id]
                        if standards_in_cluster:
                            st.error(f"❌ Cannot delete cluster '{cluster_id}' - it still contains {len(standards_in_cluster)} standards.")
                        else:
                            lib.clusters = [c for c in lib.clusters if c.id != cluster_id]
                            if st.session_state.file_manager.save_library(lib):
                                st.success("✅ Cluster deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Error deleting cluster")
            
            else:  # Add New
                cluster_id = st.text_input("Cluster ID", placeholder="e.g., ABC")
                cluster_name = st.text_input("Name", placeholder="e.g., New Cluster Name")
                cluster_desc = st.text_area("Description", height=100)
                
                max_order = max([c.order for c in lib.clusters], default=0)
                cluster_order = st.number_input("Order", min_value=1, value=max_order + 1)
                
                submitted = st.form_submit_button("➕ Add Cluster", type="primary")
                
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
                        new_cluster = Cluster(id=cluster_id, name=cluster_name, description=cluster_desc, order=cluster_order)
                        lib.clusters.append(new_cluster)
                        
                        if st.session_state.file_manager.save_library(lib):
                            st.success(f"✅ Cluster '{cluster_id}' created!")
                            st.rerun()
                        else:
                            st.error("❌ Error saving cluster")

# Screen 4: Backup & Restore
def screen_backup_restore():
    """Backup and restore library"""
    st.title("💾 Backup & Restore")
    
    lib = st.session_state.library
    fm = st.session_state.file_manager
    
    st.subheader("Current Library")
    col1, col2 = st.columns(2)
    col1.info(f"📄 **File:** `{fm.library_file}`")
    col2.info(f"🕐 **Last Modified:** {lib.last_modified}")
    
    if st.button("💾 Create Backup Now", type="primary"):
        if fm.create_backup():
            st.success("✅ Backup created successfully!")
            st.rerun()
        else:
            st.error("❌ Error creating backup")
    
    st.markdown("---")
    
    st.subheader("Existing Backups")
    backups = fm.list_backups()
    
    if backups:
        st.write(f"**{len(backups)} backup(s) available** (maximum {fm.max_backups} kept)")
        
        for i, backup in enumerate(backups, 1):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.text(f"{i}. {backup['filename']}")
            with col2:
                st.text(backup['modified'])
            with col3:
                if st.button("🔄 Restore", key=f"restore_{backup['filename']}"):
                    if fm.restore_backup(backup['filename']):
                        st.session_state.library = fm.load_library()
                        st.success("✅ Backup restored successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Error restoring backup")
        
        st.markdown("---")
        if st.button("🗑️ Delete All Backups"):
            if fm.delete_all_backups():
                st.success("✅ All backups deleted")
                st.rerun()
            else:
                st.error("❌ Error deleting backups")
    else:
        st.info("No backups available")

# Screen 5: Export
def screen_export():
    """Export library or subset"""
    st.title("📤 Export")
    
    lib = st.session_state.library
    fm = st.session_state.file_manager
    
    st.write("Export the library for runtime use or archival purposes.")
    
    with st.form("export_form"):
        st.subheader("Export Scope")
        export_mode = st.radio("What to export:", ["Full Library", "Subset by Cluster", "Subset by Standard IDs"])
        
        selected_clusters, selected_ids = [], []
        
        if export_mode == "Subset by Cluster":
            cluster_options = [c.id for c in lib.clusters]
            selected_clusters = st.multiselect("Select clusters:", cluster_options, default=cluster_options[:1])
        elif export_mode == "Subset by Standard IDs":
            all_ids = [s.id for s in lib.standards]
            ids_text = st.text_area("Enter standard IDs (comma-separated):", value=", ".join(all_ids[:3]))
            selected_ids = [id.strip() for id in ids_text.split(",") if id.strip()]
        
        st.subheader("Export Options")
        include_rationales = st.checkbox("Include rationales", value=False, help="Uncheck for smaller runtime exports.")
        filename = st.text_input("Export filename:", value="export.json")
        
        submitted = st.form_submit_button("📤 Export", type="primary")
        
        if submitted:
            cluster_filter = selected_clusters if export_mode == "Subset by Cluster" else None
            id_filter = selected_ids if export_mode == "Subset by Standard IDs" else None
            
            if fm.export_library(lib, filename, cluster_filter, id_filter, include_rationales):
                export_path = fm.exports_dir / filename
                st.success(f"✅ Exported to: `{export_path}`")
                with open(export_path, "rb") as fp:
                    st.download_button("Download Export", data=fp, file_name=filename, mime="application/json")
            else:
                st.error("❌ Error exporting library")

# Screen 6: Validate Library
def screen_validate():
    """Validate library integrity"""
    st.title("✅ Validate Library")
    
    lib = st.session_state.library
    
    st.write("Check the library for errors and inconsistencies.")
    
    if st.button("🔍 Run Validation", type="primary"):
        validator = LibraryValidator(lib)
        all_errors = validator.validate_all()
        
        if not all_errors:
            st.success("🎉 Library is valid - no issues found!")
        else:
            errors, warnings = validator.get_errors_by_severity()
            
            if errors:
                st.error(f"❌ Found {len(errors)} error(s)")
                with st.expander("Show Errors", expanded=True):
                    for error in errors:
                        st.write(str(error))
            
            if warnings:
                st.warning(f"⚠️ Found {len(warnings)} warning(s)")
                with st.expander("Show Warnings", expanded=True):
                    for warning in warnings:
                        st.write(str(warning))
            
            st.markdown("---")
            st.subheader("Data Cleanup Utility")
            st.warning("This will permanently modify your `library.json` file. It's recommended to create a backup first.")
            
            if st.button("🧹 Clean Data Issues"):
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
    
    cleanup_map = {"Praiseworthy": "Praiseworthiness"}
    valid_emotions = set(EMOTION_OPTIONS)

    for std in lib.standards:
        original_emotions = std.impacted_emotions
        cleaned_emotions = {cleanup_map.get(e, e) for e in original_emotions}
        cleaned_emotions = {e for e in cleaned_emotions if e in valid_emotions}
        
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
    
    # --- Main Content Routing based on sidebar selection ---
    if selected_screen == "Standards":
        # Use the new two-column layout for the primary workflow
        left_col, right_col = st.columns([1, 3])
        with left_col:
            render_browse_pane()
        with right_col:
            render_detail_pane()
    else:
        # For all other screens, use the traditional full-page layout
        screen_map = {
            "Create New Standard": screen_create_new_standard,
            "Clusters": screen_manage_clusters,
            "Backup & Restore": screen_backup_restore,
            "Export": screen_export,
            "Validate Library": screen_validate,
        }
        # The default screen is now "Standards", which is handled by the `if` block.
        screen_function = screen_map[selected_screen]
        screen_function()

# Run the app
if __name__ == "__main__":
    main()
