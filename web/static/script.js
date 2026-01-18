// IG Reports Bot - Frontend JavaScript

let allReports = [];
let filteredReports = [];

// Load reports on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('data/reports.json');
        const data = await response.json();
        allReports = data.reports;
        filteredReports = [...allReports];
        
        renderReports();
        setupEventListeners();
    } catch (error) {
        console.error('Error loading reports:', error);
        document.getElementById('reports-container').innerHTML = 
            '<div class="no-results">Error loading reports. Please try again later.</div>';
    }
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('search').addEventListener('input', filterReports);
    document.getElementById('agency-filter').addEventListener('change', filterReports);
    document.getElementById('newsworthy-filter').addEventListener('change', filterReports);
    document.getElementById('sort').addEventListener('change', filterReports);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
}

// Filter reports
function filterReports() {
    const searchTerm = document.getElementById('search').value.toLowerCase();
    const agencyFilter = document.getElementById('agency-filter').value;
    const newsworthyFilter = document.getElementById('newsworthy-filter').value;
    const sortBy = document.getElementById('sort').value;
    
    // Apply filters
    filteredReports = allReports.filter(report => {
        // Search filter
        const matchesSearch = !searchTerm || 
            report.title.toLowerCase().includes(searchTerm) ||
            report.agency_name.toLowerCase().includes(searchTerm) ||
            (report.reason && report.reason.toLowerCase().includes(searchTerm));
        
        // Agency filter
        const matchesAgency = !agencyFilter || report.agency_name === agencyFilter;
        
        // Newsworthy filter
        let matchesNewsworthy = true;
        if (newsworthyFilter === 'newsworthy') {
            matchesNewsworthy = report.newsworthy;
        } else if (newsworthyFilter === 'posted') {
            matchesNewsworthy = report.posted;
        }
        
        return matchesSearch && matchesAgency && matchesNewsworthy;
    });
    
    // Apply sorting
    filteredReports.sort((a, b) => {
        switch (sortBy) {
            case 'date-desc':
                return new Date(b.published_date) - new Date(a.published_date);
            case 'date-asc':
                return new Date(a.published_date) - new Date(b.published_date);
            case 'score-desc':
                return (b.score || 0) - (a.score || 0);
            case 'score-asc':
                return (a.score || 0) - (b.score || 0);
            default:
                return 0;
        }
    });
    
    renderReports();
}

// Reset filters
function resetFilters() {
    document.getElementById('search').value = '';
    document.getElementById('agency-filter').value = '';
    document.getElementById('newsworthy-filter').value = '';
    document.getElementById('sort').value = 'date-desc';
    filterReports();
}

// Render reports
function renderReports() {
    const container = document.getElementById('reports-container');
    const resultsCount = document.getElementById('results-count');
    
    // Update count
    resultsCount.textContent = `Showing ${filteredReports.length} of ${allReports.length} reports`;
    
    // Clear container
    container.innerHTML = '';
    
    // Check if no results
    if (filteredReports.length === 0) {
        container.innerHTML = '<div class="no-results">No reports found matching your filters.</div>';
        return;
    }
    
    // Render each report
    filteredReports.forEach(report => {
        const card = createReportCard(report);
        container.appendChild(card);
    });
}

// Create report card element
function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'report-card';
    
    if (report.newsworthy) card.classList.add('newsworthy');
    if (report.posted) card.classList.add('posted');
    
    // Format date
    const date = new Date(report.published_date);
    const formattedDate = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    // Build badges
    const badges = [];
    if (report.newsworthy) {
        badges.push(`<span class="badge newsworthy">Newsworthy</span>`);
    }
    if (report.is_summary) {
        badges.push(`<span class="badge summary">Summary Report</span>`);
    }
    if (report.posted) {
        badges.push(`<span class="badge posted">Posted to Bluesky</span>`);
    }
    if (report.score) {
        badges.push(`<span class="badge score">Score: ${report.score}/10</span>`);
    }
    if (report.criminal) {
        badges.push(`<span class="badge criminal">Criminal</span>`);
    }
    
    // Build topics
    let topicsHTML = '';
    if (report.topics && report.topics.length > 0) {
        topicsHTML = '<div class="topics">' + 
            report.topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('') +
            '</div>';
    }
    
    // Build details HTML
    let detailsHTML = '';
    if (report.newsworthy) {
        detailsHTML = `
            <div class="report-details">
                <div class="report-info">
                    <div class="info-item">
                        <span class="info-label">Agency:</span> ${report.agency_name}
                    </div>
                    <div class="info-item">
                        <span class="info-label">Type:</span> ${report.report_type || 'Report'}
                    </div>
                    ${report.dollar_amount ? `
                        <div class="info-item">
                            <span class="info-label">Amount:</span> $${formatNumber(report.dollar_amount)}
                        </div>
                    ` : ''}
                </div>
                ${report.reason ? `
                    <div class="report-reason">
                        <strong>Why Newsworthy:</strong>
                        ${report.reason}
                    </div>
                ` : ''}
                ${report.post_text ? `
                    <div class="report-post">
                        <strong>Bluesky Post:</strong>
                        ${report.post_text}
                    </div>
                ` : ''}
                ${topicsHTML}
            </div>
        `;
    }
    
    // Build card HTML
    const primaryLink = report.pdf_url || report.url;
    card.innerHTML = `
        <div class="report-header">
            <div class="report-title">
                <h3><a href="${primaryLink}" target="_blank">${report.title}</a></h3>
                <div class="report-meta">
                    <span>📅 ${formattedDate}</span>
                    <span>🏛️ ${report.agency_name}</span>
                    ${report.pdf_url ? 
                        `<span><a href="${report.pdf_url}" target="_blank" class="report-link">📄 View PDF →</a></span>
                         <span><a href="${report.url}" target="_blank" class="report-link secondary">🔗 Report Page</a></span>` :
                        `<span><a href="${report.url}" target="_blank" class="report-link">📄 Read Full Report →</a></span>`
                    }
                </div>
            </div>
            <div class="report-badges">
                ${badges.join('')}
            </div>
        </div>
        ${detailsHTML}
    `;
    
    return card;
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
