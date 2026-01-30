class RefinementVisualizer {
    constructor() {
        this.currentIteration = 0;
        this.maxIterations = 3;
        this.totalTokens = 0;
        this.highIssues = 0;
        this.mediumIssues = 0;
        this.activities = [];
        this.participants = new Map(); // Store participant data/elements
        this.moderator = null;
    }

    // --- Core Visualization (Progress & Metrics) ---

    updateProgress(iteration, maxIterations) {
        this.currentIteration = iteration;
        this.maxIterations = maxIterations;

        const total = maxIterations || 1;
        const percent = Math.min(100, Math.max(0, (iteration / total) * 100));
        
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const currentIterEl = document.getElementById('currentIteration');
        const maxIterEl = document.getElementById('maxIterationDisplay');

        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressPercent) progressPercent.textContent = `${Math.round(percent)}%`;
        if (currentIterEl) currentIterEl.textContent = iteration;
        if (maxIterEl) maxIterEl.textContent = maxIterations;
    }

    addActivity(message, type = 'info') {
        const log = document.getElementById('activityLog');
        if (!log) return;

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let bubbleClass = 'bubble-info';
        let icon = '';
        
        if (type === 'success') {
            bubbleClass = 'bubble-success';
            icon = '<i class="fa-solid fa-check-circle mr-2"></i>';
        } else if (type === 'warning') {
            bubbleClass = 'bubble-warning';
            icon = '<i class="fa-solid fa-exclamation-triangle mr-2"></i>';
        } else if (type === 'error') {
            bubbleClass = 'bubble-error';
            icon = '<i class="fa-solid fa-circle-xmark mr-2"></i>';
        } else if (message.includes('reviewing')) {
            icon = '<i class="fa-solid fa-glasses mr-2"></i>';
        } else if (message.includes('Moderator')) {
            icon = '<i class="fa-solid fa-gavel mr-2"></i>';
            bubbleClass = 'bubble-user'; 
        }

        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-bubble ${bubbleClass}">
                ${icon}${message}
            </div>
            <div class="activity-meta text-right pr-2">${timestamp}</div>
        `;

        log.appendChild(item);
        while (log.children.length > 100) {
            log.removeChild(log.firstChild);
        }
        log.scrollTop = log.scrollHeight;

        this.activities.push({ timestamp, message, type });
    }

    updateMetrics(issues, tokens) {
        if (issues) {
            this.highIssues = issues.high || 0;
            this.mediumIssues = issues.medium || 0;
            const highEl = document.getElementById('highIssues');
            const medEl = document.getElementById('mediumIssues');
            
            if (highEl) highEl.textContent = this.highIssues;
            if (medEl) medEl.textContent = this.mediumIssues;

            if (this.highIssues > 0 && highEl) {
                highEl.parentElement.classList.add('text-red-600');
            }
        }
        if (tokens) {
            const tokenCount = tokens.total_tokens || 0;
            this.totalTokens += tokenCount;
            const tokenEl = document.getElementById('totalTokens');
            if (tokenEl) tokenEl.textContent = this.totalTokens.toLocaleString();
        }
    }

    showStatus(status, variant = 'blue') {
        const badge = document.getElementById('statusBadge');
        if (!badge) return;
        badge.textContent = status;
        badge.className = `px-2 py-0.5 rounded-full text-xs font-medium bg-${variant}-100 text-${variant}-800 transition-colors`;
    }

    // --- Roundtable Visualization Methods ---

    initRoundtable(participants, moderatorFocus) {
        const container = document.getElementById('roundtableContainer');
        const criticsArc = document.getElementById('critics-arc');
        const moderatorSeat = document.getElementById('moderator-seat');

        if (container) container.classList.remove('hidden');
        if (criticsArc) criticsArc.innerHTML = '';

        // 1. Setup Moderator
        if (moderatorSeat) {
            moderatorSeat.innerHTML = `
                <div class="participant-avatar">
                    <i class="fa-solid fa-user-tie"></i>
                    <div class="status-dot status-idle"></div>
                </div>
                <div class="thought-bubble">Moderating session...</div>
                <div class="participant-info">
                    <div class="participant-name">Moderator</div>
                    <div class="participant-role">Focus: ${moderatorFocus.substring(0, 30)}...</div>
                </div>
            `;
            moderatorSeat.classList.remove('opacity-0');
            this.moderator = { element: moderatorSeat, name: 'Moderator' };
        }

        // 2. Setup Critics
        participants.forEach((p, index) => {
            const card = document.createElement('div');
            card.className = 'participant-card opacity-0';
            card.style.animation = `fadeIn 0.5s ease-out forwards ${index * 0.2}s`; // Staggered entry
            
            // Assign random icon based on role/expertise
            let icon = 'fa-robot';
            if (p.role.toLowerCase().includes('security')) icon = 'fa-shield-halved';
            else if (p.role.toLowerCase().includes('product')) icon = 'fa-bullseye';
            else if (p.role.toLowerCase().includes('engineer')) icon = 'fa-code';
            else if (p.role.toLowerCase().includes('architect')) icon = 'fa-sitemap';
            else if (p.role.toLowerCase().includes('business')) icon = 'fa-briefcase';

            card.innerHTML = `
                <div class="participant-avatar">
                    <i class="fa-solid ${icon}"></i>
                    <div class="status-dot status-idle" id="status-${p.name}"></div>
                </div>
                <div class="thought-bubble" id="thought-${p.name}">Ready to review</div>
                <div class="participant-info">
                    <div class="participant-name">${p.name}</div>
                    <div class="participant-role">${p.role}</div>
                    ${p.model ? `<div class="text-[9px] bg-slate-200 dark:bg-slate-800 text-slate-500 rounded px-1.5 py-0.5 mt-1 font-mono inline-block opacity-75">${p.model}</div>` : ''}
                </div>
            `;
            
            criticsArc.appendChild(card);
            this.participants.set(p.name, { element: card, data: p });
        });
    }

    updateParticipantStatus(name, status, thought = null) {
        let participant = this.participants.get(name);
        if (name === 'Moderator' && this.moderator) participant = this.moderator;

        if (!participant) return;

        const card = participant.element;
        const statusDot = card.querySelector('.status-dot');
        const thoughtBubble = card.querySelector('.thought-bubble');

        // Reset classes
        card.classList.remove('active');
        if (statusDot) {
            statusDot.classList.remove('status-idle', 'status-thinking', 'status-done');
        
            if (status === 'thinking') {
                card.classList.add('active');
                statusDot.classList.add('status-thinking');
            } else if (status === 'done') {
                statusDot.classList.add('status-done');
            } else {
                statusDot.classList.add('status-idle');
            }
        }

        if (thought && thoughtBubble) {
            thoughtBubble.textContent = thought;
        }
    }

    speak(name, summary, issues = []) {
        let participant = this.participants.get(name);
        if (name === 'Moderator' && this.moderator) participant = this.moderator;
        if (!participant) return;

        const card = participant.element;
        
        // Remove existing bubbles
        const existing = card.querySelector('.speech-bubble');
        if (existing) existing.remove();

        const bubble = document.createElement('div');
        bubble.className = 'speech-bubble absolute z-50 bg-white p-4 rounded-2xl shadow-xl border border-gray-200 text-xs w-72 -mt-4 text-slate-700 transform transition-all duration-300 scale-0 origin-bottom left-1/2 -translate-x-1/2 bottom-[110%]';
        
        let content = `<div class="font-bold mb-2 text-slate-900 text-sm">"${summary}"</div>`;
        
        if (issues && issues.length > 0) {
            content += `<div class="space-y-2 border-t border-gray-100 pt-2 bg-gray-50 rounded p-2 mt-2">`;
            issues.forEach(issue => {
                const color = issue.severity === 'High' ? 'text-red-600' : 'text-amber-600';
                content += `
                <div class="flex gap-2 items-start">
                    <span class="mt-0.5 ${color}"><i class="fa-solid fa-circle-exclamation"></i></span>
                    <div>
                        <span class="font-semibold text-[10px] uppercase text-gray-500">${issue.category}</span>
                        <p class="leading-tight text-slate-600">${issue.description.substring(0, 80)}${issue.description.length > 80 ? '...' : ''}</p>
                    </div>
                </div>`;
            });
            content += `</div>`;
        }
        
        bubble.innerHTML = content;
        
        // Add Triangle
        const triangle = document.createElement('div');
        triangle.className = 'absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white border-b border-r border-gray-200 transform rotate-45';
        bubble.appendChild(triangle);

        card.appendChild(bubble);

        // Animate in
        requestAnimationFrame(() => {
            bubble.classList.remove('scale-0');
        });

        // Auto remove after 15 seconds or when next iteration starts
        setTimeout(() => {
            if (bubble && bubble.parentElement) {
                bubble.classList.add('scale-0', 'opacity-0');
                setTimeout(() => bubble.remove(), 300);
            }
        }, 15000);
    }

    reset() {
        this.currentIteration = 0;
        this.totalTokens = 0;
        this.highIssues = 0;
        this.mediumIssues = 0;
        this.activities = [];
        this.participants.clear();
        this.moderator = null;

        this.updateProgress(0, this.maxIterations);

        ['highIssues', 'mediumIssues', 'totalTokens'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '0';
        });

        const log = document.getElementById('activityLog');
        if (log) log.innerHTML = '';

        const container = document.getElementById('roundtableContainer');
        if (container) container.classList.add('hidden');
    }

    // --- Event Handler Router ---

    handleEvent(eventType, data) {
        switch(eventType) {
            case 'session_created':
                this.addActivity(`Session created: ${data.title}`, 'success');
                this.showStatus('Running', 'green');
                break;

            case 'roundtable_generated':
                if (data.participants && data.moderator_focus) {
                    this.initRoundtable(data.participants, data.moderator_focus);
                    this.addActivity(`Roundtable assembled with ${data.participants.length} participants`);
                }
                break;

            case 'iteration_start':
                this.addActivity(`Starting iteration ${data.iteration}/${data.max_iterations}`, 'info');
                this.updateProgress(data.iteration, data.max_iterations);
                break;

            case 'critic_review_start':
                this.addActivity(`${data.critic} reviewing...`);
                this.updateParticipantStatus(data.critic, 'thinking', 'Analyzing document...');
                break;

            case 'critic_review_complete':
                this.addActivity(`${data.critic} completed review (${data.high_count} high issues)`,
                    data.high_count > 0 ? 'warning' : 'success');
                this.updateParticipantStatus(data.critic, 'done', `Found ${data.issues_count} issues`);

                // Show speech bubble with top issues
                if (data.top_issues && data.top_issues.length > 0) {
                    const summary = data.summary || `Found ${data.issues_count} issues`;
                    this.speak(data.critic, summary, data.top_issues);
                }
                break;

            case 'convergence_check':
                const issueCounts = data.issue_counts || {};
                this.updateMetrics(issueCounts, null);

                if (data.converged) {
                    this.addActivity(`Converged: ${data.reason}`, 'success');
                } else {
                    this.addActivity(`Status: ${data.reason}`, 'warning');
                }
                break;

            case 'moderator_start':
                this.addActivity('Moderator refining document...');
                this.updateParticipantStatus('Moderator', 'thinking', 'Synthesizing feedback...');
                break;

            case 'moderator_complete':
                this.addActivity(`Document refined to v${data.new_version}`, 'success');
                this.updateParticipantStatus('Moderator', 'done', 'Refinement complete');
                if (data.tokens) {
                    this.updateMetrics(null, data.tokens);
                }
                break;

            case 'refinement_complete':
                this.addActivity('Refinement complete!', 'success');
                this.showStatus(data.converged ? 'Converged' : 'Complete',
                    data.converged ? 'green' : 'yellow');
                this.updateProgress(data.final_version, data.final_version);
                break;

            case 'log':
                // Browser console logs from backend
                if (data.level === 'error') {
                    console.error(`[${data.critic || 'Server'}]`, data.message);
                } else if (data.level === 'warn') {
                    console.warn(`[${data.critic || 'Server'}]`, data.message);
                } else if (data.level === 'info') {
                    console.info(`[${data.critic || 'Server'}]`, data.message);
                } else {
                    console.log(`[${data.critic || 'Server'}]`, data.message);
                }
                break;

            default:
                console.log('Unknown event type:', eventType, data);
        }
    }
}