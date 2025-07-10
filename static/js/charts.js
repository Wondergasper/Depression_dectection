// Charts functionality for MindTrack
class ChartsManager {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.setupDefaultConfig();
        this.loadChartData();
    }

    setupDefaultConfig() {
        // Set default Chart.js configuration
        Chart.defaults.font.family = 'Inter, sans-serif';
        Chart.defaults.color = '#6b7280';
        Chart.defaults.borderColor = '#e5e7eb';
        Chart.defaults.backgroundColor = '#f9fafb';
    }

    async loadChartData() {
        try {
            const response = await fetch('/api/chart-data');
            const data = await response.json();
            
            this.renderProgressChart(data.phq9_scores);
            this.renderMoodChart(data.journal_sentiment);
            this.renderTrendChart(data.phq9_scores, data.journal_sentiment);
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.showChartError();
        }
    }

    renderProgressChart(phq9Data) {
        const canvas = document.getElementById('progressChart');
        if (!canvas || !phq9Data) return;

        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.progressChart) {
            this.charts.progressChart.destroy();
        }

        const labels = phq9Data.map(item => this.formatDate(item.date));
        const scores = phq9Data.map(item => item.score);
        
        this.charts.progressChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'PHQ-9 Score',
                    data: scores,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#111827',
                        bodyColor: '#6b7280',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return `Date: ${context[0].label}`;
                            },
                            label: function(context) {
                                const severity = this.getSeverityLevel(context.parsed.y);
                                return `Score: ${context.parsed.y}/27 (${severity})`;
                            }.bind(this)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 27,
                        grid: {
                            color: '#f3f4f6'
                        },
                        ticks: {
                            stepSize: 3,
                            callback: function(value) {
                                return value + '/27';
                            }
                        },
                        title: {
                            display: true,
                            text: 'PHQ-9 Score'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    renderMoodChart(journalData) {
        const canvas = document.getElementById('moodChart');
        if (!canvas || !journalData) return;

        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.moodChart) {
            this.charts.moodChart.destroy();
        }

        // Calculate average sentiment scores
        const avgPositive = journalData.reduce((sum, item) => sum + item.positive, 0) / journalData.length || 0;
        const avgNegative = journalData.reduce((sum, item) => sum + item.negative, 0) / journalData.length || 0;
        const avgNeutral = journalData.reduce((sum, item) => sum + item.neutral, 0) / journalData.length || 0;

        this.charts.moodChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Negative', 'Neutral'],
                datasets: [{
                    data: [avgPositive, avgNegative, avgNeutral],
                    backgroundColor: [
                        '#10b981',
                        '#ef4444',
                        '#f59e0b'
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#111827',
                        bodyColor: '#6b7280',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const percentage = Math.round(context.parsed * 100);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    renderTrendChart(phq9Data, journalData) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.trendChart) {
            this.charts.trendChart.destroy();
        }

        // Combine and sort data by date
        const combinedData = this.combineDataByDate(phq9Data, journalData);
        
        const labels = combinedData.map(item => this.formatDate(item.date));
        const phq9Scores = combinedData.map(item => item.phq9Score);
        const sentimentScores = combinedData.map(item => item.sentiment * 100); // Convert to percentage

        this.charts.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'PHQ-9 Score',
                        data: phq9Scores,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Sentiment Score',
                        data: sentimentScores,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#111827',
                        bodyColor: '#6b7280',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        max: 27,
                        title: {
                            display: true,
                            text: 'PHQ-9 Score',
                            color: '#2563eb'
                        },
                        ticks: {
                            color: '#2563eb'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: -100,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Sentiment Score (%)',
                            color: '#10b981'
                        },
                        ticks: {
                            color: '#10b981'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    combineDataByDate(phq9Data, journalData) {
        const dateMap = new Map();
        
        // Add PHQ-9 data
        phq9Data.forEach(item => {
            dateMap.set(item.date, {
                date: item.date,
                phq9Score: item.score,
                sentiment: null
            });
        });
        
        // Add journal sentiment data
        journalData.forEach(item => {
            if (dateMap.has(item.date)) {
                dateMap.get(item.date).sentiment = item.compound;
            } else {
                dateMap.set(item.date, {
                    date: item.date,
                    phq9Score: null,
                    sentiment: item.compound
                });
            }
        });
        
        // Convert to array and sort by date
        return Array.from(dateMap.values())
            .sort((a, b) => new Date(a.date) - new Date(b.date));
    }

    getSeverityLevel(score) {
        if (score <= 4) return 'Minimal';
        if (score <= 9) return 'Mild';
        if (score <= 14) return 'Moderate';
        if (score <= 19) return 'Moderately Severe';
        return 'Severe';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    }

    showChartError() {
        const chartContainers = document.querySelectorAll('canvas');
        chartContainers.forEach(canvas => {
            const container = canvas.parentElement;
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-chart-line fa-3x mb-3"></i>
                    <p>Unable to load chart data</p>
                    <button class="btn btn-outline-primary btn-sm" onclick="location.reload()">
                        <i class="fas fa-refresh me-2"></i>Retry
                    </button>
                </div>
            `;
        });
    }

    // Public method to refresh all charts
    refreshCharts() {
        this.loadChartData();
    }

    // Public method to destroy all charts
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chartsManager = new ChartsManager();
});

// Global function to initialize charts (called from dashboard)
function initializeCharts() {
    if (window.chartsManager) {
        window.chartsManager.refreshCharts();
    }
}
