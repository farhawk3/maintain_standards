// frontend/app.js
document.addEventListener("DOMContentLoaded", () => {
    const standardsListElement = document.getElementById("standards-list"); const detailViewPlaceholder = document.getElementById("detail-view-placeholder"); const detailViewContent = document.getElementById("detail-view-content");
    const tabCore = document.getElementById("tab-core");
    const tabVector = document.getElementById("tab-vector");
    const tabEmotion = document.getElementById("tab-emotion");
    const detailTitle = document.getElementById("detail-title");
    const detailDescription = document.getElementById("detail-description");
    const editBtn = document.getElementById("edit-btn");
    const saveBtn = document.getElementById("save-btn");
    const cancelBtn = document.getElementById("cancel-btn");
    const deleteBtn = document.getElementById("delete-btn");
    const createModal = document.getElementById("create-modal");
    const createBtn = document.getElementById("create-btn");
    const cancelCreateBtn = document.getElementById("cancel-create-btn");
    const createForm = document.getElementById("create-standard-form");
    const systemMenuBtn = document.getElementById("system-menu-btn");
    const systemMenuDropdown = document.getElementById("system-menu-dropdown");
    const menuCreateStandard = document.getElementById("menu-create-standard");
    const menuEditClusters = document.getElementById("menu-edit-clusters");
    const menuBackupRestore = document.getElementById("menu-backup-restore");
    const backupModal = document.getElementById("backup-modal");
    const closeBackupModalBtn = document.getElementById("close-backup-modal-btn");
    const backupList = document.getElementById("backup-list");
    const confirmModal = document.getElementById("confirm-modal");
    const confirmModalMessage = document.getElementById("confirm-modal-message");
    const confirmModalConfirmBtn = document.getElementById("confirm-modal-confirm-btn");
    const confirmModalCancelBtn = document.getElementById("confirm-modal-cancel-btn");
    const alertModal = document.getElementById("alert-modal");
    const alertModalMessage = document.getElementById("alert-modal-message");
    const alertModalOkBtn = document.getElementById("alert-modal-ok-btn");
    const menuImportExport = document.getElementById("menu-import-export");
    const exportModal = document.getElementById("export-modal");
    const closeExportModalBtn = document.getElementById("close-export-modal-btn");
    const exportBtn = document.getElementById("export-btn");
    const importFileInput = document.getElementById("import-file-input");
    const importBtn = document.getElementById("import-btn");
    const clusterCountElement = document.getElementById("cluster-count");
    const standardCountElement = document.getElementById("standard-count");
    const clusterMainModal = document.getElementById("cluster-main-modal");
    const closeClusterMainModalBtn = document.getElementById("close-cluster-main-modal-btn");
    const clusterMaintenanceList = document.getElementById("cluster-maintenance-list");
    const showCreateClusterFormBtn = document.getElementById("show-create-cluster-form-btn");
    const clusterEditModal = document.getElementById("cluster-edit-modal");
    const clusterFormTitle = document.getElementById("cluster-form-title");
    const clusterEditForm = document.getElementById("cluster-edit-form");
    const clusterFormCancelBtn = document.getElementById("cluster-form-cancel-btn");
    const clusterFormSaveBtn = document.getElementById("cluster-form-save-btn");
    const filterModal = document.getElementById("filter-modal");
    const filterModalTitle = document.getElementById("filter-modal-title");
    const filterModalOptions = document.getElementById("filter-modal-options");
    const filterModalCancelBtn = document.getElementById("filter-modal-cancel-btn");
    const filterModalConfirmBtn = document.getElementById("filter-modal-confirm-btn");
    const activeFilterDisplay = document.getElementById("active-filter-display");
    const searchInput = document.getElementById("search-input");
    const userActions = document.getElementById("user-actions");

    // =================================================================================
    // --- State Management ---
    // =================================================================================
    let allStandards = []; // Store all fetched standards
    let allClusters = []; // Store all fetched clusters
    let currentlySelectedStandard = null;
    let currentMode = 'view'; // 'view' or 'edit'
    let activeFilter = {
        type: 'none', // 'none', 'cluster', 'focus', 'dimension'
        values: []
    };

    // --- Static Data for Dropdowns ---
    const focusOptions = ["Object/Concept", "Action", "Person/Group"];
    const emotionOptions = [
        "Valence",
        "Arousal",
        "Dominance",
        "Belonging",
        "Goal Relevance",
        "Social Impact",
        "Prospect",
        "Agency-Self",
        "Agency-Other",
        "Agency-Circumstance",
        "Intentionality",
        "Expectation",
        "Praiseworthiness",
        "Familiarity"
    ];

    // =================================================================================
    // --- UI Rendering ---
    // =================================================================================

    /**
     * Main function to display a standard's details in either view or edit mode.
     * @param {string} standardId - The ID of the standard to display.
     * @param {string} [mode='view'] - The mode to display ('view' or 'edit').
     * @returns {void}
     */
    function displayStandardDetails(standardId, mode = 'view') {
        currentlySelectedStandard = allStandards.find(s => s.id === standardId);
        if (!currentlySelectedStandard) return;

        currentMode = mode;
        updateActionButtons();

        // Render based on the current mode
        if (currentMode === 'view') {
            renderViewMode(currentlySelectedStandard);
        } else {
            renderEditMode(currentlySelectedStandard);
        }

        // Highlight the selected item in the list
        document.querySelectorAll('#standards-list li').forEach(li => {
            li.classList.toggle('selected', li.dataset.id === standardId);
        });

        detailViewPlaceholder.classList.add("hidden");
        detailViewContent.classList.remove("hidden");
    }

    /**
     * Renders the detail panel in read-only "view" mode.
     * @param {object} standard - The standard object to render.
     * @returns {void}
     */
    function renderViewMode(standard) {
        // Find the full cluster name
        const cluster = allClusters.find(c => c.id === standard.cluster);
        const clusterDisplayName = cluster ? `${cluster.name} (${cluster.id})` : standard.cluster;

        // --- Construct the MAC Vector string ---
        const vectorOrder = ['family', 'group', 'reciprocity', 'heroism', 'deference', 'fairness', 'property'];
        const vectorValues = vectorOrder.map(key => standard.mac_vector[key] || 0.0);
        const vectorString = `[ ${vectorValues.map(v => v.toFixed(2)).join(', ')} ]`;

        // --- Render static title and description ---
        detailTitle.innerHTML = `<span class="view-field">${standard.name}</span>`;
        detailDescription.innerHTML = `<span class="view-field">${standard.description}</span>`;
        detailTitle.dataset.prefix = "Standard: ";

        // --- Populate Core Attributes Tab ---
        tabCore.innerHTML = `
            <div class="detail-section">
                <h3>Core Attributes:</h3>
                <div class="detail-grid">
                    <strong>Standard ID:</strong>     <span class="view-field">${standard.id}</span>
                    <strong>Cluster:</strong>         <span class="view-field">${clusterDisplayName}</span>
                    <strong>Importance:</strong>      <span class="view-field">${standard.importance_weight}</span>
                    <strong>Primary Focus:</strong>   <span class="view-field">${standard.primary_focus}</span>
                    <strong>Secondary Focus:</strong> <span class="view-field">${standard.secondary_focus}</span>
                    <strong>Date Created:</strong>    <span class="view-field">${standard.date_created}</span>
                    <strong>Date Modified:</strong>   <span class="view-field">${standard.date_modified}</span>
                </div>
            </div>
        `;

        // --- Populate Vector & Rationale Tab ---
        tabVector.innerHTML = `
            <div class="detail-section">
                <h3>MAC Vector:</h3>
                <p><strong>Vector:</strong> <span class="view-field">${vectorString}</span></p>
            </div>
            <div class="detail-section">
                <div class="detail-grid rationale-grid grid-header">
                    <strong>Dimension</strong>
                    <strong>Rationale</strong>
                </div>
                <div class="detail-grid rationale-grid" style="padding-top: 10px;">
                    <strong>Family (<span class="mac-value-inline">${(standard.mac_vector.family || 0.0).toFixed(2)}</span>):</strong>      <div class="view-field">${marked.parse(standard.rationale.family_rationale.trim())}</div>
                    <strong>Group (<span class="mac-value-inline">${(standard.mac_vector.group || 0.0).toFixed(2)}</span>):</strong>       <div class="view-field">${marked.parse(standard.rationale.group_rationale.trim())}</div>
                    <strong>Reciprocity (<span class="mac-value-inline">${(standard.mac_vector.reciprocity || 0.0).toFixed(2)}</span>):</strong> <div class="view-field">${marked.parse(standard.rationale.reciprocity_rationale.trim())}</div>
                    <strong>Heroism (<span class="mac-value-inline">${(standard.mac_vector.heroism || 0.0).toFixed(2)}</span>):</strong>     <div class="view-field">${marked.parse(standard.rationale.heroism_rationale.trim())}</div>
                    <strong>Deference (<span class="mac-value-inline">${(standard.mac_vector.deference || 0.0).toFixed(2)}</span>):</strong>   <div class="view-field">${marked.parse(standard.rationale.deference_rationale.trim())}</div>
                    <strong>Fairness (<span class="mac-value-inline">${(standard.mac_vector.fairness || 0.0).toFixed(2)}</span>):</strong>    <div class="view-field">${marked.parse(standard.rationale.fairness_rationale.trim())}</div>
                    <strong>Property (<span class="mac-value-inline">${(standard.mac_vector.property || 0.0).toFixed(2)}</span>):</strong>    <div class="view-field">${marked.parse(standard.rationale.property_rationale.trim())}</div>
                </div>
            </div>
        `;

        // --- Populate Emotion Dimensions Tab ---
        tabEmotion.innerHTML = `
            <div class="detail-section">
                <h3>Impacted Appraisal Dimensions:</h3>
                <div class="view-field emotion-chips">${standard.impacted_emotions.map(e => `<span class="chip">${e}</span>`).join('') || '<p>No impacted appraisal dimensions specified.</p>'}</div>
            </div>
        `;
    }

    /**
     * Renders the detail panel with input fields for "edit" mode.
     * @param {object} standard - The standard object to populate the form with.
     * @returns {void}
     */
    function renderEditMode(standard) {
        const vectorOrder = ['family', 'group', 'reciprocity', 'heroism', 'deference', 'fairness', 'property'];

        // --- Render editable title and description ---
        detailTitle.innerHTML = `<input type="text" id="edit-name" value="${standard.name}" />`;
        detailTitle.dataset.prefix = "Standard: ";
        detailDescription.innerHTML = `<textarea id="edit-description" rows="3">${standard.description}</textarea>`;

        // --- Populate Core Attributes Tab ---
        tabCore.innerHTML = `
            <div class="detail-section">
                <h3>Core Attributes:</h3>
                <div class="detail-grid">
                    <strong>Standard ID:</strong>     <span>${standard.id}</span>
                    <strong>Cluster:</strong>         <select id="edit-cluster">${allClusters.map(c => `<option value="${c.id}" ${c.id === standard.cluster ? 'selected' : ''}>${c.name} (${c.id})</option>`).join('')}</select>
                    <strong>Importance:</strong>      <input type="number" id="edit-importance" value="${standard.importance_weight}" step="0.01" min="0" max="1" />
                    <strong>Primary Focus:</strong>   <select id="edit-primary-focus">${focusOptions.map(f => `<option value="${f}" ${f === standard.primary_focus ? 'selected' : ''}>${f}</option>`).join('')}</select>
                    <strong>Secondary Focus:</strong> <select id="edit-secondary-focus">${focusOptions.map(f => `<option value="${f}" ${f === standard.secondary_focus ? 'selected' : ''}>${f}</option>`).join('')}</select>
                    <strong>Date Created:</strong>    <span>${standard.date_created}</span>
                    <strong>Date Modified:</strong>   <span>${standard.date_modified}</span>
                </div>
            </div>
        `;

        // --- Populate Vector & Rationale Tab ---
        tabVector.innerHTML = `
            <div class="detail-section">
                <h3>MAC Vector: <span id="mac-sum-display">(Sum: 1.00)</span></h3>
                <div class="detail-grid indented-grid" id="mac-vector-inputs">
                    ${vectorOrder.map(key => `
                        <strong>${key.charAt(0).toUpperCase() + key.slice(1)}:</strong>
                        <input type="number" class="mac-input" data-key="${key}" value="${standard.mac_vector[key] || 0.0}" step="0.01" />
                    `).join('')}
                </div>
            </div>
            <div class="detail-section">
                <div class="detail-grid rationale-grid grid-header">
                    <strong>Dimension</strong>
                    <strong>Rationale</strong>
                </div>
                <div class="detail-grid rationale-grid" style="padding-top: 10px;">
                    ${vectorOrder.map(key => `
                        <strong>${key.charAt(0).toUpperCase() + key.slice(1)}:</strong>
                        <textarea class="rationale-input" data-key="${key}_rationale" rows="4">${standard.rationale[`${key}_rationale`] || ''}</textarea>
                    `).join('')}
                </div>
            </div>
        `;

        // --- Populate Emotion Dimensions Tab ---
        tabEmotion.innerHTML = `
            <div class="detail-section">
                <h3>Impacted Appraisal Dimensions:</h3>
                <div id="edit-emotions-container"></div>
            </div>
        `;

        // --- Post-render logic for complex fields ---
        setupMacVectorSum();
    }

    /**
     * Attaches event listeners to MAC vector inputs to calculate and display their sum.
     * @returns {void}
     */
    function setupMacVectorSum() {
        const sumDisplay = document.getElementById('mac-sum-display');
        const inputs = document.querySelectorAll('.mac-input');

        function calculateSum() {
            let sum = 0;
            inputs.forEach(input => {
                sum += parseFloat(input.value) || 0;
            });
            sumDisplay.textContent = `(Sum: ${sum.toFixed(2)})`;
            sumDisplay.style.color = Math.abs(sum - 1.0) < 0.001 ? 'green' : 'red';
        }

        inputs.forEach(input => input.addEventListener('input', calculateSum));
        calculateSum(); // Initial calculation
    }

    // =================================================================================
    // --- API Service / Data Fetching ---
    // =================================================================================

    /**
     * Sets up the emotion editor in the "Appraisal Dimensions" tab.
     * @param {string[]} currentEmotions - An array of emotions currently assigned to the standard.
     * @returns {void}
     */
    function setupEmotionEditor(currentEmotions) {
        const container = document.getElementById('edit-emotions-container');

        container.innerHTML = `
            <div class="emotion-chips" id="emotion-chips-list">
                ${currentEmotions.map(e => `<span class="chip dismissable" data-emotion="${e}">${e} <span class="dismiss-x">x</span></span>`).join('')}
            </div>
            <select id="add-emotion-select">
                <option value="">Add an appraisal dimension...</option>
            </select>
        `;

        const select = document.getElementById('add-emotion-select');
        const chipsList = document.getElementById('emotion-chips-list');

        function updateDropdownOptions() {
            const currentlyUsedEmotions = Array.from(chipsList.querySelectorAll('.chip')).map(chip => chip.dataset.emotion);
            const availableOptions = emotionOptions.filter(opt => !currentlyUsedEmotions.includes(opt));

            // Clear existing options (except the placeholder)
            select.innerHTML = '<option value="">Add an appraisal dimension...</option>';

            // Add the new options in their original order
            availableOptions.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt;
                select.appendChild(option);
            });
        }

        // Initial population
        updateDropdownOptions();

        container.addEventListener('click', (e) => {
            if (e.target.classList.contains('dismiss-x')) {
                const chip = e.target.parentElement;
                chip.remove();
                updateDropdownOptions(); // Re-render dropdown to add the option back
            }
        });

        select.addEventListener('change', (e) => {
            const selectedEmotion = e.target.value;
            if (selectedEmotion) {
                const newChip = document.createElement('span');
                newChip.className = 'chip dismissable';
                newChip.dataset.emotion = selectedEmotion;
                newChip.innerHTML = `${selectedEmotion} <span class="dismiss-x">x</span>`;
                document.getElementById('emotion-chips-list').appendChild(newChip);
                updateDropdownOptions(); // Re-render dropdown to remove the option
            }
        });
    }

    /**
     * Renders the list of standards in the left panel.
     * @param {object[]} standardsToRender - The array of standard objects to display.
     * @returns {void}
     */
    function renderStandardsList(standardsToRender) {
        standardsListElement.innerHTML = ""; // Clear previous list

        // Get the ID of the currently selected standard to preserve selection
        const selectedId = currentlySelectedStandard ? currentlySelectedStandard.id : null;

        if (standardsToRender.length === 0) {
            standardsListElement.innerHTML = "<li>No standards match the current filter.</li>";
            return;
        }

        standardsToRender.forEach((standard) => {
            const listItem = document.createElement("li");
            listItem.textContent = `[${standard.id}] ${standard.name}`;
            listItem.dataset.id = standard.id;

            // Re-apply the 'selected' class if this item was selected
            if (standard.id === selectedId) {
                listItem.classList.add('selected');
            }

            listItem.addEventListener("click", () => {
                displayStandardDetails(standard.id);
            });

            standardsListElement.appendChild(listItem);
        });
    }

    /**
     * Fetches the complete list of standards from the API and populates the left-panel list.
     * @returns {Promise<void>}
     */
    async function fetchAndDisplayStandards() {
        try {
            const response = await fetch("/api/standards");
            const fetchedStandards = await response.json();
            allStandards = fetchedStandards.sort((a, b) => a.id.localeCompare(b.id)); // Sort once

            standardCountElement.textContent = `Standards: ${allStandards.length}`;
            console.log("Successfully fetched standards:", allStandards);

            // Initial render of the full list
            renderStandardsList(allStandards);

        } catch (error) {
            console.error("Failed to fetch standards:", error);
            standardsListElement.innerHTML =
                "<li>Error loading standards. Please check the console.</li>";
        }
    }

    /**
     * Fetches the complete list of clusters from the API.
     * @returns {Promise<void>}
     */
    async function fetchClusters() {
        try {
            const response = await fetch("/api/clusters");
            allClusters = await response.json();
            allClusters.sort((a, b) => a.order - b.order); // Sort clusters by order
            clusterCountElement.textContent = `Clusters: ${allClusters.length}`;
        } catch (error) {
            console.error("Failed to fetch clusters:", error);
        }
    }

    // =================================================================================
    // --- Event Listeners & UI Actions ---
    // =================================================================================

    function handleFilterSelection(filterType) {
        if (filterType === 'none') {
            activeFilter = { type: 'none', values: [] };
            applyCurrentFilter();
        } else {
            openFilterModal(filterType);
        }
    }

    function openFilterModal(filterType) {
        let title = '';
        let optionsHTML = '';
        const isMultiSelect = (filterType === 'cluster' || filterType === 'dimension');
        const inputType = isMultiSelect ? 'checkbox' : 'radio';

        switch (filterType) {
            case 'cluster':
                title = 'Filter by Cluster';
                optionsHTML = allClusters.map(c => `
                    <div class="checkbox-group">
                        <input type="${inputType}" id="modal-opt-${c.id}" name="filter-option" value="${c.id}">
                        <label for="modal-opt-${c.id}">${c.name}</label>
                    </div>
                `).join('');
                break;
            case 'focus':
                title = 'Filter by Focus';
                optionsHTML = focusOptions.map(f => `
                    <div class="checkbox-group">
                        <input type="${inputType}" id="modal-opt-${f}" name="filter-option" value="${f}">
                        <label for="modal-opt-${f}">${f}</label>
                    </div>
                `).join('');
                break;
            case 'dimension':
                title = 'Filter by Appraisal Dimension';
                optionsHTML = emotionOptions.map(e => `
                     <div class="checkbox-group">
                        <input type="${inputType}" id="modal-opt-${e}" name="filter-option" value="${e}">
                        <label for="modal-opt-${e}">${e}</label>
                    </div>
                `).join('');
                break;
        }

        filterModalTitle.textContent = title;
        filterModalOptions.innerHTML = optionsHTML;

        // Set up modal confirmation
        filterModalConfirmBtn.onclick = () => {
            const selectedOptions = Array.from(document.querySelectorAll('#filter-modal-options input:checked')).map(input => input.value);
            if (selectedOptions.length > 0) {
                activeFilter = { type: filterType, values: selectedOptions };
            } else {
                // If user confirms with no selection, treat it as 'none'
                activeFilter = { type: 'none', values: [] };
                document.getElementById('filter-none').checked = true;
            }
            applyCurrentFilter();
            filterModal.classList.add('hidden');
        };

        filterModal.classList.remove('hidden');
    }

    filterModalCancelBtn.addEventListener('click', () => {
        // Revert radio button to match the currently active filter
        document.getElementById(`filter-${activeFilter.type}`).checked = true;
        filterModal.classList.add('hidden');
    });

    function applyCurrentFilter() {
        let filteredStandards = allStandards;

        // 1. Apply search filter first
        const searchTerm = searchInput.value.toLowerCase().trim();
        if (searchTerm) {
            filteredStandards = allStandards.filter(standard => standard.name.toLowerCase().includes(searchTerm) || standard.id.toLowerCase().includes(searchTerm));
        }

        // Update the active filter display text
        if (activeFilter.type === 'none' || activeFilter.values.length === 0) {
            activeFilterDisplay.classList.add('hidden');
            activeFilterDisplay.textContent = '';
        } else {
            const filterName = activeFilter.type;
            const filterValues = activeFilter.values.join(', ');
            activeFilterDisplay.textContent = `${filterName} filter: ${filterValues}`;
            activeFilterDisplay.classList.remove('hidden');
        }

        // 2. Apply categorical filter on the result of the search filter
        switch (activeFilter.type) {
            case 'cluster':
                filteredStandards = filteredStandards.filter(standard =>
                    activeFilter.values.includes(standard.cluster)
                );
                break;
            case 'focus':
                const focusValue = activeFilter.values[0];
                filteredStandards = filteredStandards.filter(standard =>
                    standard.primary_focus === focusValue || standard.secondary_focus === focusValue
                );
                break;
            case 'dimension':
                filteredStandards = filteredStandards.filter(standard =>
                    standard.impacted_emotions.some(emotion => activeFilter.values.includes(emotion))
                );
                break;
            case 'none':
            default:
                // No filter applied, use all standards
                break;
        }

        renderStandardsList(filteredStandards);
    }

    // --- Filter Event Listeners (Moved here to be after function definitions) ---

    // Use 'click' instead of 'change' to allow re-opening the modal for an active filter.
    document.getElementById('filter-control-panel').addEventListener('click', (e) => {
        // Check if the click was on a radio button or its associated label.
        const radio = e.target.closest('.radio-item')?.querySelector('input[name="filter-type"]');

        if (radio) {
            radio.checked = true; // Ensure the radio button is visually selected
            handleFilterSelection(radio.value);
        }
    });

    searchInput.addEventListener('input', () => {
        applyCurrentFilter();
    });


    /**
     * Toggles the visibility of the main action buttons (Edit, Save, Cancel, Delete) based on the current mode.
     * @returns {void}
     */
    function updateActionButtons() {
        if (currentMode === 'view') {
            editBtn.classList.remove('hidden');
            saveBtn.classList.add('hidden');
            cancelBtn.classList.add('hidden');
            deleteBtn.classList.add('hidden');
        } else { // edit mode
            editBtn.classList.add('hidden');
            saveBtn.classList.remove('hidden');
            cancelBtn.classList.remove('hidden');
            deleteBtn.classList.remove('hidden');
        }
    }

    editBtn.addEventListener('click', () => {
        if (currentlySelectedStandard) {
            displayStandardDetails(currentlySelectedStandard.id, 'edit');

            // --- FIX for Appraisal Dimensions tab blanking on edit ---
            // If the emotion tab is already active when we enter edit mode,
            // we need to manually trigger its setup function.
            if (document.getElementById('tab-emotion').classList.contains('active')) {
                setupEmotionEditor(currentlySelectedStandard.impacted_emotions);
            }
        }
    });

    cancelBtn.addEventListener('click', () => {
        if (currentlySelectedStandard) {
            displayStandardDetails(currentlySelectedStandard.id, 'view');
        }
    });

    deleteBtn.addEventListener('click', async () => {
        if (!currentlySelectedStandard) return;

        const isConfirmed = await showConfirmation(`Are you sure you want to permanently delete the standard "${currentlySelectedStandard.name}" (${currentlySelectedStandard.id})?`);

        if (isConfirmed) {
            try {
                const response = await fetch(`/api/standards/${currentlySelectedStandard.id}`, {
                    method: 'DELETE',
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'An unknown error occurred.');
                }

                // --- Update UI on successful deletion ---
                // Reset detail panel
                detailViewContent.classList.add("hidden");
                detailViewPlaceholder.classList.remove("hidden");
                currentlySelectedStandard = null;

                // Re-fetch the standards list to ensure UI is perfectly in sync
                await fetchAndDisplayStandards();

            } catch (error) {
                await showAlert(`Delete failed: ${error.message}`, "Error");
            }
        }
    });

    /**
     * Displays a modal dialog to confirm a destructive action.
     * @param {string} message - The confirmation message to display.
     * @returns {Promise<boolean>} A Promise that resolves to true if confirmed, false otherwise.
     */
    function showConfirmation(message) {
        return new Promise((resolve) => {
            confirmModalMessage.textContent = message;
            confirmModal.classList.remove('hidden');

            const confirmHandler = () => {
                confirmModal.classList.add('hidden');
                resolve(true);
            };

            const cancelHandler = () => {
                confirmModal.classList.add('hidden');
                resolve(false);
            };

            confirmModalConfirmBtn.onclick = confirmHandler;
            confirmModalCancelBtn.onclick = cancelHandler;
        });
    }

    /**
     * Displays a modal alert with a message.
     * @param {string} message - The message to display.
     * @param {string} [title="Alert"] - The title of the alert.
     * @returns {Promise<void>}
     */
    function showAlert(message, title = "Alert") {
        return new Promise((resolve) => {
            // Check if title element exists, if not just skip title update
            const titleEl = document.getElementById('alert-modal-title');
            if (titleEl) titleEl.textContent = title;

            alertModalMessage.innerHTML = message;
            alertModal.classList.remove('hidden');

            alertModalOkBtn.onclick = () => {
                alertModal.classList.add('hidden');
                resolve();
            };
        });
    }

    saveBtn.addEventListener('click', async () => {
        if (!currentlySelectedStandard) return;

        // --- Gather all data from the edit form ---
        const updatedStandardData = {
            id: currentlySelectedStandard.id, // ID is not editable
            name: document.getElementById('edit-name').value,
            description: document.getElementById('edit-description').value,
            cluster: document.getElementById('edit-cluster').value,
            importance_weight: parseFloat(document.getElementById('edit-importance').value),
            primary_focus: document.getElementById('edit-primary-focus').value,
            secondary_focus: document.getElementById('edit-secondary-focus').value,
            impacted_emotions: Array.from(document.querySelectorAll('#emotion-chips-list .chip')).map(chip => chip.dataset.emotion),
            mac_vector: {},
            rationale: {},
            // Dates are handled by the backend
            date_created: currentlySelectedStandard.date_created,
        };

        document.querySelectorAll('.mac-input').forEach(input => {
            updatedStandardData.mac_vector[input.dataset.key] = parseFloat(input.value) || 0;
        });

        document.querySelectorAll('.rationale-input').forEach(textarea => {
            updatedStandardData.rationale[textarea.dataset.key] = textarea.value;
        });

        // --- Send the data to the backend ---
        try {
            const response = await fetch(`/api/standards/${currentlySelectedStandard.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedStandardData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'An unknown error occurred.');
            }

            const savedStandard = await response.json();

            // --- Update the local data and UI ---
            const index = allStandards.findIndex(s => s.id === savedStandard.id);
            if (index !== -1) {
                allStandards[index] = savedStandard;
            }

            // Update the name in the left panel list
            const listItem = standardsListElement.querySelector(`li[data-id="${savedStandard.id}"]`);
            if (listItem) {
                listItem.textContent = `[${savedStandard.id}] ${savedStandard.name}`;
            }

            // Switch back to view mode, which will re-render with the new data
            displayStandardDetails(savedStandard.id, 'view');

        } catch (error) {
            await showAlert(`Save failed: ${error.message}`, "Error");
        }
    });

    systemMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent window listener from closing it immediately
        systemMenuDropdown.classList.toggle('hidden');
    });

    window.addEventListener('click', (e) => {
        // Close the dropdown if user clicks outside of it
        if (!systemMenuDropdown.classList.contains('hidden') && !e.target.matches('.kebab-btn')) {
            systemMenuDropdown.classList.add('hidden');
        }
    });

    menuCreateStandard.addEventListener('click', () => {
        systemMenuDropdown.classList.add('hidden'); // Close the menu

        // Populate the cluster dropdown in the modal
        const createClusterSelect = document.getElementById('create-cluster');
        createClusterSelect.innerHTML = allClusters.map(c => `<option value="${c.id}">${c.name} (${c.id})</option>`).join('');

        createForm.reset(); // Clear any previous input
        createModal.classList.remove('hidden');
    });

    // Close modal if backdrop is clicked
    createModal.addEventListener('click', (e) => {
        if (e.target === createModal) {
            createModal.classList.add('hidden');
        }
    });

    cancelCreateBtn.addEventListener('click', () => {
        createModal.classList.add('hidden');
    });

    createBtn.addEventListener('click', async () => {
        const formData = new FormData(createForm);
        const newStandardData = {
            id: formData.get('id'),
            name: formData.get('name'),
            description: formData.get('description'),
            cluster: formData.get('cluster'),
            // Backend will provide defaults for other fields
        };

        // Basic validation
        if (!newStandardData.id.trim() || !newStandardData.name.trim()) {
            await showAlert("Standard ID and Name are required fields.", "Validation Error");
            return;
        }

        try {
            const response = await fetch(`/api/standards`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newStandardData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'An unknown error occurred.');
            }

            const createdStandard = await response.json();

            // --- Update UI on successful creation ---
            createModal.classList.add('hidden');

            // Add to local array and re-sort
            allStandards.push(createdStandard);
            allStandards.sort((a, b) => a.id.localeCompare(b.id));

            renderStandardsList(allStandards);
            displayStandardDetails(createdStandard.id, 'view');

        } catch (error) {
            await showAlert(`Create failed: ${error.message}`, "Error");
        }
    });

    /**
     * Fetches the list of available backup files from the server and renders them.
     * @returns {Promise<void>}
     */
    async function refreshBackupList() {
        try {
            const response = await fetch('/api/backups');
            const files = await response.json();
            backupList.innerHTML = '';
            if (files.length === 0) {
                backupList.innerHTML = '<li>No backups found.</li>';
            } else {
                files.forEach(file => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <span>${file}</span>
                        <div class="backup-actions">
                            <a href="/api/backups/${file}" download title="Download backup" class="backup-action-btn download-btn">⬇️</a>
                            <button title="Restore from this backup" class="backup-action-btn restore-backup-btn" data-filename="${file}">↩️</button>
                            <button title="Delete backup" class="backup-action-btn delete-backup-btn" data-filename="${file}">🗑️</button>
                        </div>
                    `;
                    backupList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Failed to fetch backup list:', error);
            backupList.innerHTML = '<li>Error loading backups.</li>';
        }
    }

    menuBackupRestore.addEventListener('click', () => {
        systemMenuDropdown.classList.add('hidden');
        refreshBackupList();
        backupModal.classList.remove('hidden');
    });

    closeBackupModalBtn.addEventListener('click', () => backupModal.classList.add('hidden'));

    document.getElementById('create-backup-btn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/backup', { method: 'POST' });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message);
            await showAlert(`Backup created successfully: ${data.filename}`, "Backup Complete");
            refreshBackupList();
        } catch (error) {
            await showAlert(`Backup failed: ${error.message}`, "Error");
        }
    });

    backupList.addEventListener('click', async (e) => {
        if (e.target.matches('.delete-backup-btn')) { // Handle Delete
            const filename = e.target.dataset.filename;
            const isConfirmed = await showConfirmation(`Are you sure you want to permanently delete the backup file "${filename}"?`);

            if (isConfirmed) {
                try {
                    const response = await fetch(`/api/backups/${filename}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error('Failed to delete backup.');
                    refreshBackupList();
                } catch (error) {
                    await showAlert(error.message, "Error");
                }
            }
        }
        if (e.target.matches('.restore-backup-btn')) { // Handle Restore
            const filename = e.target.dataset.filename;
            const isConfirmed = await showConfirmation(`WARNING: This will overwrite the entire current library with the contents of the backup "${filename}". This action cannot be undone. Are you absolutely sure?`);
            if (isConfirmed) {
                try {
                    const response = await fetch(`/api/restore/${filename}`, { method: 'POST' });
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.message || 'Restore failed.');
                    }
                    await showAlert('Library restored successfully. The application will now reload.', "Restore Complete");
                    backupModal.classList.add('hidden');
                    detailViewContent.classList.add("hidden");
                    detailViewPlaceholder.classList.remove("hidden");
                    currentlySelectedStandard = null;
                    initializeApp();
                } catch (error) {
                    await showAlert(`Restore failed: ${error.message}`, "Error");
                }
            }
        }
    });

    menuImportExport.addEventListener('click', () => {
        systemMenuDropdown.classList.add('hidden');

        // Populate filter lists
        const clusterListContainer = document.getElementById('export-cluster-list-container');
        clusterListContainer.innerHTML = allClusters.map(c => `
            <div class="checkbox-group">
                <input type="checkbox" id="cluster-export-${c.id}" value="${c.id}" class="export-cluster-check" checked>
                <label for="cluster-export-${c.id}">${c.name}</label>
            </div>
        `).join('');

        const standardListContainer = document.getElementById('export-standard-list-container');
        standardListContainer.innerHTML = allStandards.map(s => `
            <div class="checkbox-group">
                <input type="checkbox" id="standard-export-${s.id}" value="${s.id}" class="export-standard-check">
                <label for="standard-export-${s.id}">[${s.id}] ${s.name}</label>
            </div>
        `).join('');

        exportModal.classList.remove('hidden');
    });

    closeExportModalBtn.addEventListener('click', () => exportModal.classList.add('hidden'));

    document.querySelectorAll('input[name="export-method"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const clusterContainer = document.getElementById('export-cluster-list-container');
            const standardContainer = document.getElementById('export-standard-list-container');
            if (e.target.value === 'cluster') {
                clusterContainer.classList.remove('hidden');
                standardContainer.classList.add('hidden');
            } else {
                clusterContainer.classList.add('hidden');
                standardContainer.classList.remove('hidden');
            }
        });
    });

    exportBtn.addEventListener('click', async () => {
        const filename = document.getElementById('export-filename').value.trim() + '.json';
        if (!filename || filename === '.json') {
            await showAlert("Please provide a valid filename for the export.", "Error");
            return;
        }

        const exportOptions = {
            filename: filename,
            include_rationales: !document.getElementById('export-exclude-rationales').checked,
        };

        const exportMethod = document.querySelector('input[name="export-method"]:checked').value;

        if (exportMethod === 'cluster') {
            exportOptions.cluster_ids = Array.from(document.querySelectorAll('.export-cluster-check:checked')).map(cb => cb.value);
            if (exportOptions.cluster_ids.length === 0) {
                await showAlert("Please select at least one cluster to export.", "Error");
                return;
            }
        } else { // by standard
            exportOptions.standard_ids = Array.from(document.querySelectorAll('.export-standard-check:checked')).map(cb => cb.value);
            if (exportOptions.standard_ids.length === 0) {
                await showAlert("Please select at least one standard to export.", "Error");
                return;
            }
        }

        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(exportOptions),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'An unknown error occurred during export.');
            }

            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            exportModal.classList.add('hidden');

        } catch (error) {
            await showAlert(`Export failed: ${error.message}`, "Error");
        }
    });

    importFileInput.addEventListener('change', () => {
        if (importFileInput.files.length > 0) {
            importBtn.classList.remove('hidden');
        } else {
            importBtn.classList.add('hidden');
        }
    });

    importBtn.addEventListener('click', async () => {
        const file = importFileInput.files[0];
        if (!file) return;

        const isConfirmed = await showConfirmation(`Are you sure you want to import from "${file.name}"? This will merge the file's contents with your current library and may overwrite existing data.`);
        if (!isConfirmed) return;

        const formData = new FormData();
        formData.append('import_file', file);

        try {
            const response = await fetch('/api/import', {
                method: 'POST',
                body: formData,
            });

            const report = await response.json();
            if (!response.ok) throw new Error(report.message);

            // Build a detailed report message
            let reportMessage = `
                <p><strong>Import Complete!</strong></p>
                <ul>
                    <li>Clusters Added: ${report.clusters_added}</li>
                    <li>Clusters Updated: ${report.clusters_updated}</li>
                    <li>Standards Added: ${report.standards_added}</li>
                    <li>Standards Updated: ${report.standards_updated}</li>
                    <li>Standards Skipped: ${report.standards_skipped}</li>
                </ul>
            `;
            if (report.skipped_reasons && report.skipped_reasons.length > 0) {
                reportMessage += `<p><strong>Skipped Reasons:</strong></p><ul>${report.skipped_reasons.map(r => `<li>${r}</li>`).join('')}</ul>`;
            }

            exportModal.classList.add('hidden');
            await showAlert(reportMessage, "Import Report");

            // Re-initialize the app to show all changes
            initializeApp();

        } catch (error) {
            await showAlert(`Import failed: ${error.message}`, "Error");
        }
    });

    /**
     * Fetches the latest cluster data and renders the list in the cluster maintenance modal.
     * @returns {Promise<void>}
     */
    async function renderClusterMaintenanceList() {
        // Re-fetch clusters to ensure the list is up-to-date
        await fetchClusters();
        clusterMaintenanceList.innerHTML = '';
        allClusters.sort((a, b) => a.order - b.order); // Ensure sorted by order

        allClusters.forEach(cluster => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div class="cluster-info">
                    <strong>${cluster.order}. ${cluster.name}</strong>
                    <small>ID: ${cluster.id}</small>
                </div>
                <div class="cluster-actions">
                    <button class="edit-cluster-btn" data-id="${cluster.id}">Edit</button>
                    <button class="delete-cluster-btn" data-id="${cluster.id}">Delete</button>
                </div>
            `;
            clusterMaintenanceList.appendChild(li);
        });
    }

    closeClusterMainModalBtn.addEventListener('click', () => clusterMainModal.classList.add('hidden'));

    /**
     * Opens the cluster editor form, either for creating a new cluster or editing an existing one.
     * @param {object|null} cluster - The cluster object to edit, or null to create a new one.
     * @returns {void}
     */
    function openClusterForm(cluster = null) {
        clusterEditForm.reset();
        const idInput = document.getElementById('cluster-edit-id');
        if (cluster) { // Edit mode
            clusterFormTitle.textContent = "Edit Cluster";
            idInput.value = cluster.id;
            idInput.disabled = true; // Prevent editing ID
            document.getElementById('cluster-edit-name').value = cluster.name;
            document.getElementById('cluster-edit-description').value = cluster.description;
            document.getElementById('cluster-edit-order').value = cluster.order;
            clusterFormSaveBtn.dataset.mode = 'edit';
            clusterFormSaveBtn.dataset.id = cluster.id;
        } else { // Create mode
            clusterFormTitle.textContent = "Create New Cluster";
            idInput.disabled = false;
            clusterFormSaveBtn.dataset.mode = 'create';
            clusterFormSaveBtn.dataset.id = '';
        }
        clusterEditModal.classList.remove('hidden');
    }

    showCreateClusterFormBtn.addEventListener('click', () => openClusterForm());
    clusterFormCancelBtn.addEventListener('click', () => clusterEditModal.classList.add('hidden'));

    clusterMaintenanceList.addEventListener('click', (e) => {
        const target = e.target;
        const clusterId = target.dataset.id;

        if (target.matches('.edit-cluster-btn')) {
            const cluster = allClusters.find(c => c.id === clusterId);
            if (cluster) openClusterForm(cluster);
        }

        if (target.matches('.delete-cluster-btn')) {
            deleteCluster(clusterId);
        }
    });

    clusterFormSaveBtn.addEventListener('click', async () => {
        const mode = clusterFormSaveBtn.dataset.mode;
        const id = (mode === 'edit') ? clusterFormSaveBtn.dataset.id : document.getElementById('cluster-edit-id').value;

        const clusterData = {
            id: id,
            name: document.getElementById('cluster-edit-name').value,
            description: document.getElementById('cluster-edit-description').value,
            order: parseInt(document.getElementById('cluster-edit-order').value, 10)
        };

        const url = (mode === 'create') ? '/api/clusters' : `/api/clusters/${id}`;
        const method = (mode === 'create') ? 'POST' : 'PUT';

        try {
            const response = await fetch(`${url}`, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(clusterData)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message);

            clusterEditModal.classList.add('hidden');
            await renderClusterMaintenanceList(); // Refresh the list
        } catch (error) {
            await showAlert(`Save failed: ${error.message}`, "Error");
        }
    });

    /**
     * Handles the deletion of a cluster after user confirmation.
     * @param {string} clusterId - The ID of the cluster to delete.
     * @returns {Promise<void>}
     */
    async function deleteCluster(clusterId) {
        const isConfirmed = await showConfirmation(`Are you sure you want to delete cluster "${clusterId}"? This cannot be undone.`);
        if (isConfirmed) {
            try {
                const response = await fetch(`/api/clusters/${clusterId}`, { method: 'DELETE' });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message);
                await renderClusterMaintenanceList(); // Refresh the list
            } catch (error) {
                await showAlert(`Delete failed: ${error.message}`, "Error");
            }
        }
    }

    menuEditClusters.addEventListener('click', () => {
        systemMenuDropdown.classList.add('hidden');
        renderClusterMaintenanceList();
        clusterMainModal.classList.remove('hidden');
    });

    // =================================================================================
    // --- App Initialization ---
    // =================================================================================

    /**
     * Checks if the user is logged in and updates the UI accordingly.
     */
    async function checkUserStatus() {
        try {
            const response = await fetch('/api/user');
            const data = await response.json();
            if (data.user) {
                userActions.innerHTML = `
                    <span style="margin-right: 10px;">Welcome, ${data.user.email} (${data.role || 'User'})</span>
                    <a href="/logout" class="btn">Logout</a>
                `;
                // Load data only if logged in
                await fetchClusters();
                await fetchAndDisplayStandards();
                // After data is loaded, select the first standard in the list by default
                if (allStandards.length > 0) {
                    displayStandardDetails(allStandards[0].id);
                }
            } else {
                userActions.innerHTML = `<a href="/login" class="btn">Login with Google</a>`;
                standardsListElement.innerHTML = "<li>Please login to view standards.</li>";
                clusterCountElement.textContent = "Clusters: 0";
                standardCountElement.textContent = "Standards: 0";
            }
        } catch (error) {
            console.error("Failed to check user status:", error);
            userActions.innerHTML = `<a href="/login" class="btn">Login with Google</a>`;
        }
    }

    /**
     * Initializes the application by fetching all necessary data and rendering the initial view.
     * @returns {Promise<void>}
     */
    async function initializeApp() {
        await checkUserStatus();
    }

    // --- Set up global event listeners that only need to be attached once ---
    document.querySelector('.tab-nav').addEventListener('click', (e) => {
        if (e.target.matches('.tab-link')) {
            const tabId = e.target.dataset.tab;
            document.querySelectorAll('.tab-link').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById(tabId).classList.add('active');

            // If switching to the emotion tab in edit mode, ensure the editor is built.
            if (tabId === 'tab-emotion' && currentMode === 'edit' && currentlySelectedStandard) {
                setupEmotionEditor(currentlySelectedStandard.impacted_emotions);
            }
        }
    });

    // --- Start the application ---
    initializeApp();
});