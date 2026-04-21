// ═══════════════════════════════════════════════════════════
//  SOCIAX SYNC — Dashboard JS
// ═══════════════════════════════════════════════════════════

// ── Toast Notification ──
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => toast.classList.remove('show'), 3500);
}

// ── Loading Overlay ──
function showLoading(text = 'Processing…') {
    const overlay = document.getElementById('loading-overlay');
    document.getElementById('loading-text').textContent = text;
    overlay.classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// ── Trigger Sync ──
function triggerSync() {
    showLoading('Running sync across all 11 sources…');
    
    fetch('/api/trigger-sync/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.status === 'ok') {
            showToast(`✅ Sync complete! ${data.saved} new jobs added.`);
            addLogEntry(`Sync complete: ${data.scraped} scraped, ${data.saved} saved`, 'success');
            // Refresh page after short delay to show new data
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('⚠️ Sync finished with warnings: ' + (data.message || ''), 'error');
            addLogEntry('Sync error: ' + (data.message || 'Unknown'), 'error');
        }
    })
    .catch(err => {
        hideLoading();
        showToast('❌ Sync failed: ' + err.message, 'error');
        addLogEntry('Sync failed: ' + err.message, 'error');
    });
}

// ── Delete Job ──
function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    fetch(`/jobs/${jobId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            showToast('🗑️ Job deleted');
            // Remove row from table if it exists
            const row = document.querySelector(`tr[data-job-id="${jobId}"]`);
            if (row) row.remove();
            else location.reload();
        }
    });
}

// ── Clear All Jobs ──
function clearAllJobs() {
    if (!confirm('⚠️ Are you sure you want to delete ALL jobs? This cannot be undone.')) return;
    
    showLoading('Clearing all jobs…');
    fetch('/api/clear-all/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.status === 'ok') {
            showToast('🧹 All jobs cleared');
            setTimeout(() => location.reload(), 1000);
        }
    });
}

// ── Search ──
function handleNavbarSearch(event) {
    if (event) event.preventDefault();
    const query = document.getElementById('navbar-search-input').value;
    const params = new URLSearchParams(window.location.search);
    
    if (query) {
        params.set('q', query);
    } else {
        params.delete('q');
    }
    params.delete('page');
    
    window.location.href = '/jobs/?' + params.toString();
}



// ── Filters ──
function applyFilters() {
    const source = document.getElementById('filter-source')?.value || '';
    const visa = document.getElementById('filter-visa')?.value || '';
    const status = document.getElementById('filter-status')?.value || '';
    const search = document.getElementById('navbar-search-input')?.value || '';
    
    const params = new URLSearchParams();
    if (search) params.set('q', search);
    if (source) params.set('source', source);
    if (visa) params.set('visa', visa);
    if (status) params.set('status', status);
    
    window.location.href = window.location.pathname + '?' + params.toString();
}

// ── Log Entry ──
function addLogEntry(message, type = 'info') {
    const log = document.getElementById('sync-log');
    if (!log) return;
    
    const time = new Date().toLocaleTimeString();
    const colorClass = type === 'success' ? 'log-success' : type === 'error' ? 'log-error' : 'log-warn';
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">[${time}]</span> <span class="${colorClass}">${message}</span>`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// ── CSRF Cookie ──
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ── Auto-refresh sync status every 30s ──
setInterval(() => {
    fetch('/api/status/')
        .then(r => r.json())
        .then(data => {
            const statusEl = document.getElementById('sync-status');
            const labelEl = document.getElementById('sync-label');
            if (data.syncing) {
                statusEl.className = 'sync-status running';
                labelEl.textContent = 'Syncing…';
            } else {
                statusEl.className = 'sync-status idle';
                labelEl.textContent = 'Idle';
            }
        })
        .catch(() => {});
}, 30000);
