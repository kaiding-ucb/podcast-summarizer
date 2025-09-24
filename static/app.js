// Main application JavaScript

// Handle URL parameters on page load
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const videoUrl = urlParams.get('video_url');
    
    if (videoUrl) {
        const videoInput = document.getElementById('video_url');
        if (videoInput) {
            videoInput.value = decodeURIComponent(videoUrl);
            // Auto-focus the analyze button
            const analyzeBtn = document.querySelector('button[type="submit"]');
            if (analyzeBtn) {
                analyzeBtn.focus();
            }
        }
    }
});

// HTMX response handlers
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.xhr.responseURL.includes('/api/analyze')) {
        try {
            const data = JSON.parse(event.detail.xhr.responseText);
            renderAnalysisResult(data);
        } catch (e) {
            console.error('Error parsing analysis response:', e);
        }
    }
});

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', function(event) {
    const resultsDiv = document.getElementById('results');
    if (resultsDiv) {
        resultsDiv.innerHTML = `
            <div class="error-state">
                <h3>❌ Analysis Failed</h3>
                <p>Sorry, we couldn't analyze this video. Please try again or check the URL.</p>
                <p class="error-detail">Error: ${event.detail.xhr.statusText}</p>
            </div>
        `;
    }
});

function renderAnalysisResult(data) {
    const resultsDiv = document.getElementById('results');
    if (!resultsDiv) return;

    // Create formatted analysis display
    const analysisHTML = `
        <div class="analysis-result">
            <div class="analysis-header">
                <h3>📊 Analysis Results</h3>
                <div class="video-meta">
                    <p><strong>📹 Video:</strong> ${data.title}</p>
                    <p><strong>⏱️ Duration:</strong> ${formatDuration(data.video_duration)}</p>
                    <p><strong>✅ Timestamps Valid:</strong> ${data.timestamps_valid ? 'Yes' : 'No'}</p>
                    <p><strong>🚫 VanEck Excluded:</strong> ${data.vaneck_excluded ? 'Yes' : 'No'}</p>
                </div>
            </div>
            
            <div class="analysis-content">
                ${formatAnalysisText(data.analysis)}
            </div>
            
            <div class="analysis-actions">
                <a href="${data.video_url}" target="_blank" class="btn btn-secondary">
                    ▶️ Watch Video
                </a>
                <button onclick="copyAnalysis()" class="btn btn-secondary">
                    📋 Copy Analysis
                </button>
            </div>
        </div>
    `;

    resultsDiv.innerHTML = analysisHTML;
    
    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatAnalysisText(text) {
    // Convert markdown-style formatting to HTML
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
        .replace(/\n/g, '<br>') // Line breaks
        .replace(/\((\d+:\d+)\)/g, '<span class="timestamp">($1)</span>'); // Highlight timestamps
}

function formatDuration(seconds) {
    if (!seconds) return 'Unknown';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

function copyAnalysis() {
    const analysisContent = document.querySelector('.analysis-content');
    if (analysisContent) {
        // Get text content without HTML tags
        const text = analysisContent.innerText || analysisContent.textContent;
        
        navigator.clipboard.writeText(text).then(function() {
            // Show temporary success message
            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '✅ Copied!';
            setTimeout(() => {
                btn.innerHTML = originalText;
            }, 2000);
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
        });
    }
}

// Form validation
document.addEventListener('submit', function(event) {
    const form = event.target;
    if (form.id === 'analyzeForm') {
        const videoUrl = form.video_url.value;
        
        // Basic YouTube URL validation
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
        if (!youtubeRegex.test(videoUrl)) {
            event.preventDefault();
            alert('Please enter a valid YouTube URL');
            return false;
        }
        
        // Clear previous results
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '';
        }
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to submit analysis form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const analyzeForm = document.getElementById('analyzeForm');
        if (analyzeForm && document.activeElement === document.getElementById('video_url')) {
            analyzeForm.dispatchEvent(new Event('submit'));
        }
    }
});