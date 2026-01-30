let currentWebSocket = null;
let visualizer = new RefinementVisualizer();
let currentSessionId = null;

// Helper to switch views
function switchView(viewId) {
    ['setupView', 'monitorView', 'resultsCard'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });
    const target = document.getElementById(viewId);
    if (target) target.classList.remove('hidden');
}

// File upload handler - Auto upload on selection
const fileInput = document.getElementById('fileUpload');
if (fileInput) {
    fileInput.addEventListener('change', async () => {
        const statusEl = document.getElementById('uploadStatus');
        const contentEl = document.getElementById('content');

        if (!fileInput.files || fileInput.files.length === 0) return;

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        statusEl.textContent = 'Uploading...';
        statusEl.className = 'text-xs text-brand-600 block animate-pulse';
        statusEl.classList.remove('hidden');

        try {
            const response = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const data = await response.json();

            // Populate content textarea
            contentEl.value = data.content;

            statusEl.innerHTML = '<i class="fa-solid fa-check"></i> ' + data.filename;
            statusEl.className = 'text-xs text-green-600 block';

        } catch (error) {
            console.error('Upload error:', error);
            statusEl.textContent = 'Upload failed';
            statusEl.className = 'text-xs text-red-600 block';
        }
    });
}

// Load sessions from API and populate sidebar
async function loadSessions() {
    const sessionList = document.getElementById('sessionList');
    if (!sessionList) return;

    try {
        const response = await fetch('/api/sessions/');
        if (!response.ok) throw new Error('Failed to load sessions');

        const data = await response.json();
        const sessions = data.sessions || [];

        if (sessions.length === 0) {
            sessionList.innerHTML = '<div class="px-4 py-2 text-xs text-slate-500 italic">No sessions yet</div>';
            return;
        }

        sessionList.innerHTML = sessions.map(session => `
            <div class="relative group">
                <button onclick="loadSession('${session.session_id}')"
                        class="w-full text-left px-4 py-2 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-900 transition text-xs">
                    <div class="font-medium text-slate-300 truncate pr-8">${session.title || 'Untitled'}</div>
                    <div class="text-slate-500 text-[10px] mt-0.5">${new Date(session.created_at).toLocaleDateString()}</div>
                </button>
                <button onclick="handleDeleteClick(event, '${session.session_id}')"
                        class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-red-500/20 rounded text-red-400 hover:text-red-300"
                        title="Delete session">
                    <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading sessions:', error);
        sessionList.innerHTML = '<div class="px-4 py-2 text-xs text-red-500">Failed to load</div>';
    }
}

// Load a specific session
async function loadSession(sessionId) {
    try {
        // Get session metadata
        const sessionResponse = await fetch(`/api/sessions/${sessionId}`);
        if (!sessionResponse.ok) throw new Error('Failed to load session');
        const sessionData = await sessionResponse.json();

        // Try to get convergence report (might not exist if still running)
        const reportResponse = await fetch(`/api/sessions/${sessionId}/report`);

        if (!reportResponse.ok) {
            // Session is still running or failed - switch to monitor view instead
            if (reportResponse.status === 404) {
                alert('This session is still in progress. Use "Monitor Session" to view live progress.');
                return;
            }
            throw new Error('Failed to load report');
        }

        const report = await reportResponse.json();

        // Get final PRD
        const finalVersion = report.final_version || sessionData.final_version || 1;
        const prdResponse = await fetch(`/api/sessions/${sessionId}/prd/${finalVersion}`);
        if (!prdResponse.ok) throw new Error('Failed to load PRD');
        const prd = await prdResponse.json();

        // Update results view
        const prdContent = document.getElementById('prdContent');
        if (prdContent && marked) {
            prdContent.innerHTML = marked.parse(prd.content);
        }

        // Store current session for report/review buttons
        currentSessionId = sessionId;

        // Check if continue button should be shown
        showContinueButtonIfNeeded(report);

        // Switch to results view
        switchView('resultsCard');

    } catch (error) {
        console.error('Error loading session:', error);
        alert('Failed to load session: ' + error.message);
    }
}

// Make loadSession globally available
window.loadSession = loadSession;

// Handle delete button click with proper event stopping
function handleDeleteClick(event, sessionId) {
    event.stopPropagation();
    event.preventDefault();
    deleteSession(sessionId);
}

// Make handleDeleteClick globally available
window.handleDeleteClick = handleDeleteClick;

// Delete a session
async function deleteSession(sessionId) {
    // Confirm deletion
    if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
        return;
    }

    try {
        console.log('Deleting session:', sessionId);

        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });

        console.log('Delete response status:', response.status);

        if (!response.ok) {
            let errorMessage = 'Failed to delete session';
            try {
                const data = await response.json();
                errorMessage = data.detail || errorMessage;
            } catch (e) {
                errorMessage = `Server error (${response.status})`;
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();
        console.log('Delete result:', result);

        // Reload sessions list
        await loadSessions();

        // If we deleted the currently viewed session, go back to start view
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            switchView('setupView');
        }

        // Show success message
        console.log('Session deleted successfully:', sessionId);

    } catch (error) {
        console.error('Error deleting session:', error);
        alert('Failed to delete session: ' + error.message);
    }
}

// Make deleteSession globally available
window.deleteSession = deleteSession;

// Start monitoring a refinement session via WebSocket
function startMonitoring(sessionId, maxIterations) {
    // Create WebSocket connection
    currentWebSocket = new RefinementWebSocket(sessionId);

    // Update max iterations display
    const maxIterDisplay = document.getElementById('maxIterationDisplay');
    if (maxIterDisplay) maxIterDisplay.textContent = maxIterations;

    // Set initial state to "Preparing..."
    const statusBadge = document.getElementById('statusBadge');
    if (statusBadge) {
        statusBadge.textContent = 'Preparing...';
        statusBadge.className = 'px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800';
    }

    // Set up event handlers
    currentWebSocket.on('session_created', (data) => {
        console.log('Session created:', data);
        visualizer.handleEvent('session_created', data);

        // Update status to "Running"
        if (statusBadge) {
            statusBadge.textContent = 'Running';
            statusBadge.className = 'px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800';
        }
    });

    currentWebSocket.on('iteration_start', (data) => {
        console.log('Iteration started:', data);
        const currentIterEl = document.getElementById('currentIteration');
        if (currentIterEl) currentIterEl.textContent = data.iteration;

        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        if (progressBar && progressPercent) {
            const progress = Math.round((data.iteration / maxIterations) * 100);
            progressBar.style.width = `${progress}%`;
            progressPercent.textContent = `${progress}%`;
        }

        visualizer.handleEvent('iteration_start', data);
    });

    currentWebSocket.on('critic_review_start', (data) => {
        console.log('Critic review started:', data);
        visualizer.handleEvent('critic_review_start', data);
    });

    currentWebSocket.on('critic_review_complete', (data) => {
        console.log('Critic review completed:', data);
        visualizer.handleEvent('critic_review_complete', data);
    });

    currentWebSocket.on('convergence_check', (data) => {
        console.log('Convergence check:', data);
        const highIssuesEl = document.getElementById('highIssues');
        const mediumIssuesEl = document.getElementById('mediumIssues');

        // Access nested issue_counts object
        const issueCounts = data.issue_counts || {};
        if (highIssuesEl) highIssuesEl.textContent = issueCounts.high || 0;
        if (mediumIssuesEl) mediumIssuesEl.textContent = issueCounts.medium || 0;

        visualizer.handleEvent('convergence_check', data);
    });

    currentWebSocket.on('moderator_start', (data) => {
        console.log('Moderator started:', data);
        visualizer.handleEvent('moderator_start', data);
    });

    currentWebSocket.on('moderator_complete', (data) => {
        console.log('Moderator completed:', data);
        visualizer.handleEvent('moderator_complete', data);
    });

    currentWebSocket.on('refinement_complete', async (data) => {
        console.log('Refinement completed:', data);
        visualizer.handleEvent('refinement_complete', data);

        // Update status badge to completed
        const statusBadge = document.getElementById('statusBadge');
        if (statusBadge) {
            statusBadge.textContent = data.converged ? 'Converged' : 'Complete';
            statusBadge.className = data.converged
                ? 'px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800'
                : 'px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800';
        }

        // Update progress to 100%
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        if (progressBar && progressPercent) {
            progressBar.style.width = '100%';
            progressPercent.textContent = '100%';
        }

        // Load final document
        try {
            const prdResponse = await fetch(`/api/sessions/${sessionId}/prd/${data.final_version}`);
            if (prdResponse.ok) {
                const prd = await prdResponse.json();
                const prdContent = document.getElementById('prdContent');
                if (prdContent && marked) {
                    prdContent.innerHTML = marked.parse(prd.content);
                }
            }

            // Check if we should show continue button
            const report = await fetch(`/api/sessions/${sessionId}/report`);
            if (report.ok) {
                const reportData = await report.json();
                showContinueButtonIfNeeded(reportData);
            }

            // Switch to results view
            setTimeout(() => {
                switchView('resultsCard');
            }, 2000);

        } catch (error) {
            console.error('Error loading final document:', error);
        }
    });

    // Connect WebSocket
    currentWebSocket.connect();
}

// Show continue button if max iterations reached with high issues
function showContinueButtonIfNeeded(report) {
    const resultsCard = document.getElementById('resultsCard');
    if (!resultsCard) return;

    const highIssues = report.final_issue_count?.high || 0;
    const convergenceReason = report.convergence_reason || '';
    const isMaxIterations = convergenceReason.includes('Max iterations');

    if (isMaxIterations && highIssues > 0) {
        // Find the action buttons container
        const actionsContainer = resultsCard.querySelector('.flex.gap-3');
        if (!actionsContainer) return;

        // Check if continue button already exists
        if (document.getElementById('continueRefinementBtn')) return;

        // Add continue button
        const continueBtn = document.createElement('button');
        continueBtn.id = 'continueRefinementBtn';
        continueBtn.className = 'px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 transition shadow-sm';
        continueBtn.innerHTML = `<i class="fa-solid fa-rotate-right mr-1"></i> Continue Refinement (${highIssues} high issues)`;

        continueBtn.onclick = () => showContinueDialog(report);

        // Insert before export button
        actionsContainer.insertBefore(continueBtn, actionsContainer.lastElementChild);
    }
}

// Show dialog to continue refinement
function showContinueDialog(report) {
    const highIssues = report.final_issue_count?.high || 0;
    const currentIterations = report.iterations || 0;

    const dialogHtml = `
        <div class="space-y-4">
            <div class="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
                <div class="flex items-start gap-3">
                    <i class="fa-solid fa-triangle-exclamation text-orange-600 mt-0.5"></i>
                    <div>
                        <div class="font-semibold text-orange-900 dark:text-orange-200">Refinement stopped at max iterations</div>
                        <div class="text-sm text-orange-700 dark:text-orange-300 mt-1">
                            ${highIssues} high severity issue${highIssues !== 1 ? 's' : ''} remain${highIssues !== 1 ? '' : 's'} unresolved.
                            You can continue refinement with additional iterations to address these issues.
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Additional Iterations
                </label>
                <input type="number" id="additionalIterations" value="3" min="1" max="10"
                       class="w-full border-gray-200 dark:border-slate-700 rounded-lg px-4 py-2 text-sm bg-gray-50 dark:bg-slate-800 dark:text-white">
                <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Current: ${currentIterations} iteration${currentIterations !== 1 ? 's' : ''}
                </div>
            </div>

            <div class="flex gap-3 justify-end pt-4 border-t border-gray-200 dark:border-slate-700">
                <button onclick="closeModal()" class="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-slate-700 transition">
                    Cancel
                </button>
                <button id="confirmContinueBtn" class="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 transition">
                    <i class="fa-solid fa-play mr-1"></i> Continue Refinement
                </button>
            </div>
        </div>
    `;

    showModal('Continue Refinement', `Session: ${report.session_id}`, dialogHtml);

    // Add confirm handler
    setTimeout(() => {
        const confirmBtn = document.getElementById('confirmContinueBtn');
        if (confirmBtn) {
            confirmBtn.onclick = async () => {
                const additionalIterations = parseInt(document.getElementById('additionalIterations').value);
                await continueRefinement(report.session_id, additionalIterations);
                closeModal();
            };
        }
    }, 100);
}

// Continue refinement with additional iterations
async function continueRefinement(sessionId, additionalIterations) {
    try {
        const response = await fetch(`/api/refinement/continue/${sessionId}?additional_iterations=${additionalIterations}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Continuation started:', data);

        // Switch to monitor view
        visualizer.reset();
        switchView('monitorView');

        // Update max iterations display
        const maxIterDisplay = document.getElementById('maxIterationDisplay');
        if (maxIterDisplay) maxIterDisplay.textContent = data.new_max_iterations;

        // Update current iteration
        const currentIterEl = document.getElementById('currentIteration');
        if (currentIterEl) currentIterEl.textContent = data.previous_iterations;

        // Store session ID
        currentSessionId = sessionId;

        // Start monitoring the continuation
        startMonitoring(sessionId, data.new_max_iterations);

        alert(`Refinement continued with ${additionalIterations} additional iterations`);

    } catch (error) {
        console.error('Error continuing refinement:', error);
        alert('Failed to continue refinement: ' + error.message);
    }
}

// Load sessions on page load
window.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    initDarkMode();
    
    // Custom Style Toggle Logic
    const styleSelect = document.getElementById('participantStyle');
    const customStyleInput = document.getElementById('customStyleInput');
    if (styleSelect && customStyleInput) {
        styleSelect.addEventListener('change', () => {
            if (styleSelect.value === 'custom') {
                customStyleInput.classList.remove('hidden');
                customStyleInput.focus();
            } else {
                customStyleInput.classList.add('hidden');
            }
        });
    }
});

// --- Dark Mode Logic ---

function initDarkMode() {
    const isDark = localStorage.getItem('theme') === 'dark' || 
                   (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    if (isDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function toggleDarkMode() {
    if (document.documentElement.classList.contains('dark')) {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    } else {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }
}

// Make globally available
window.toggleDarkMode = toggleDarkMode;

// Start refinement form handler
const startForm = document.getElementById('startForm');
if (startForm) {
    startForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const title = document.getElementById('title').value;
        const goal = document.getElementById('goal').value;
        const content = document.getElementById('content').value;
        const maxIterations = parseInt(document.getElementById('maxIterations').value);
        const documentType = document.getElementById('documentType').value;
        const numParticipants = parseInt(document.getElementById('numParticipants').value);
        const usePreset = document.getElementById('usePreset').value;
        let participantStyle = document.getElementById('participantStyle').value;
        
        // Handle custom style
        if (participantStyle === 'custom') {
            const customVal = document.getElementById('customStyleInput').value.trim();
            if (customVal) {
                participantStyle = customVal;
            }
        }

        const aiModel = document.getElementById('aiModel').value;
        const modelStrategy = document.getElementById('modelStrategy').value;
        const forceMaxIterations = document.getElementById('forceMaxIterations').checked;

        const startButton = document.getElementById('startButton');
        const originalBtnContent = startButton.innerHTML;
        
        startButton.disabled = true;
        startButton.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Initializing...';

        try {
            const requestBody = {
                title,
                content,
                max_iterations: maxIterations,
                document_type: documentType,
                num_participants: numParticipants,
                force_max_iterations: forceMaxIterations
            };

            if (goal) requestBody.goal = goal;
            if (usePreset) requestBody.use_preset = usePreset;
            if (participantStyle) requestBody.participant_style = participantStyle;
            if (aiModel) requestBody.model = aiModel;
            if (modelStrategy) requestBody.model_strategy = modelStrategy;

            const response = await fetch('/api/refinement/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            currentSessionId = data.session_id;

            // Update Monitor Title
            const monitorTitle = document.getElementById('monitorTitle');
            if (monitorTitle) monitorTitle.textContent = title;

            // Reset visualizer & Switch View
            visualizer.reset();
            switchView('monitorView');

            // Start monitoring
            startMonitoring(data.session_id, maxIterations);

        } catch (error) {
            console.error('Error starting refinement:', error);
            alert('Failed to start refinement: ' + error.message);
        } finally {
            startButton.disabled = false;
            startButton.innerHTML = originalBtnContent;
        }
    });
}

// Modal functions
function showModal(title, subtitle, content) {
    const modal = document.getElementById('detailsModal');
    const modalContent = document.getElementById('detailsModalContent');
    const modalTitle = document.getElementById('modalTitle');
    const modalSubtitle = document.getElementById('modalSubtitle');
    const modalBody = document.getElementById('modalBody');

    if (!modal || !modalContent || !modalTitle || !modalBody) return;

    modalTitle.textContent = title;
    if (modalSubtitle) modalSubtitle.textContent = subtitle;
    modalBody.innerHTML = content;

    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        modalContent.classList.remove('scale-95');
    }, 10);
}

function closeModal() {
    const modal = document.getElementById('detailsModal');
    const modalContent = document.getElementById('detailsModalContent');

    if (!modal || !modalContent) return;

    modal.classList.add('opacity-0');
    modalContent.classList.add('scale-95');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

// Make closeModal globally available
window.closeModal = closeModal;

// Report and review button handlers
document.addEventListener('DOMContentLoaded', () => {
    const viewReportBtn = document.getElementById('viewReportBtn');
    const viewReviewsBtn = document.getElementById('viewReviewsBtn');

    if (viewReportBtn) {
        viewReportBtn.addEventListener('click', async () => {
            if (!currentSessionId) {
                alert('No session loaded');
                return;
            }

            try {
                const response = await fetch(`/api/sessions/${currentSessionId}/report`);
                if (!response.ok) throw new Error('Failed to load report');
                const report = await response.json();

                const reportHtml = `
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
                                <div class="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Iterations</div>
                                <div class="text-2xl font-bold">${report.iterations}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
                                <div class="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Status</div>
                                <div class="text-2xl font-bold ${report.converged ? 'text-green-600' : 'text-yellow-600'}">
                                    ${report.converged ? 'Converged' : 'Max Iterations'}
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
                            <div class="text-xs text-slate-500 dark:text-slate-400 uppercase mb-2">Convergence Reason</div>
                            <div class="text-sm">${report.convergence_reason}</div>
                        </div>
                        <div class="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
                            <div class="text-xs text-slate-500 dark:text-slate-400 uppercase mb-2">Final Issue Count</div>
                            <div class="flex gap-4 text-sm">
                                <span><strong>High:</strong> ${report.final_issue_count?.high || 0}</span>
                                <span><strong>Medium:</strong> ${report.final_issue_count?.medium || 0}</span>
                                <span><strong>Low:</strong> ${report.final_issue_count?.low || 0}</span>
                            </div>
                        </div>
                        ${report.token_usage ? `
                            <div class="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
                                <div class="text-xs text-slate-500 dark:text-slate-400 uppercase mb-2">Token Usage</div>
                                <div class="text-sm"><strong>Total:</strong> ${report.token_usage.total?.toLocaleString() || 'N/A'}</div>
                            </div>
                        ` : ''}
                    </div>
                `;

                showModal('Convergence Report', report.session_id, reportHtml);

            } catch (error) {
                console.error('Error loading report:', error);
                alert('Failed to load convergence report: ' + error.message);
            }
        });
    }

    if (viewReviewsBtn) {
        viewReviewsBtn.addEventListener('click', async () => {
            if (!currentSessionId) {
                alert('No session loaded');
                return;
            }

            try {
                const sessionResponse = await fetch(`/api/sessions/${currentSessionId}`);
                if (!sessionResponse.ok) throw new Error('Failed to load session');
                const sessionData = await sessionResponse.json();

                const reviewsResponse = await fetch(`/api/sessions/${currentSessionId}/reviews/${sessionData.final_version}`);
                if (!reviewsResponse.ok) throw new Error('Failed to load reviews');
                const reviewsData = await reviewsResponse.json();

                const reviews = reviewsData.reviews || [];

                const reviewsHtml = reviews.map(review => `
                    <div class="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg mb-4">
                        <div class="font-semibold text-lg mb-2">${review.reviewer_name || 'Reviewer'}</div>
                        <div class="text-sm mb-3">${review.overall_assessment || 'No assessment'}</div>
                        ${review.issues && review.issues.length > 0 ? `
                            <div class="space-y-2">
                                ${review.issues.map(issue => `
                                    <div class="border-l-4 ${
                                        issue.severity === 'High' ? 'border-red-500' :
                                        issue.severity === 'Medium' ? 'border-yellow-500' :
                                        'border-blue-500'
                                    } pl-3 py-1">
                                        <div class="text-xs uppercase font-semibold ${
                                            issue.severity === 'High' ? 'text-red-600' :
                                            issue.severity === 'Medium' ? 'text-yellow-600' :
                                            'text-blue-600'
                                        }">${issue.severity} - ${issue.category}</div>
                                        <div class="text-sm mt-1">${issue.description}</div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<div class="text-sm text-slate-500 italic">No issues found</div>'}
                    </div>
                `).join('');

                showModal('Critic Reviews', `Version ${sessionData.final_version}`, reviewsHtml || '<p class="text-slate-500">No reviews available</p>');

            } catch (error) {
                console.error('Error loading reviews:', error);
                alert('Failed to load reviews: ' + error.message);
            }
        });
    }
});