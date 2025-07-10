// Analysis page functionality
class AnalysisHandler {
    constructor() {
        this.init();
    }

    init() {
        this.setupPHQ9Form();
        this.setupJournalForm();
        this.setupTabSwitching();
        this.setupResultsActions();
    }

    setupPHQ9Form() {
        const form = document.getElementById('phq9Form');
        if (!form) return;

        // Add interactive feedback for radio buttons
        const radioButtons = form.querySelectorAll('input[type="radio"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', (e) => {
                const questionItem = e.target.closest('.question-item');
                questionItem.classList.add('answered');

                // Remove answered class from siblings
                const allOptions = questionItem.querySelectorAll('input[type="radio"]');
                allOptions.forEach(option => {
                    option.parentElement.classList.remove('selected');
                });

                // Add selected class to current option
                e.target.parentElement.classList.add('selected');

                this.updateProgressIndicator();
            });
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitPHQ9Form(form);
        });
    }

    setupJournalForm() {
        const form = document.getElementById('journalForm');
        const textarea = document.getElementById('journal_text');
        const charCount = document.getElementById('charCount');
        const submitBtn = document.getElementById('journalSubmit');

        if (!form || !textarea) return;

        // Character count and validation
        textarea.addEventListener('input', (e) => {
            const length = e.target.value.length;

            if (charCount) {
                charCount.textContent = `${length} characters`;

                // Update color based on length
                if (length < 20) {
                    charCount.style.color = 'var(--danger-color)';
                } else if (length < 100) {
                    charCount.style.color = 'var(--warning-color)';
                } else {
                    charCount.style.color = 'var(--success-color)';
                }
            }

            // Enable/disable submit button
            if (submitBtn) {
                submitBtn.disabled = length < 20;
            }

            // Auto-resize textarea
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitJournalForm(form);
        });
    }

    setupTabSwitching() {
        const tabs = document.querySelectorAll('#analysisTabs button');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = e.target.getAttribute('data-bs-target');

                // Update URL without page reload
                const url = new URL(window.location);
                url.searchParams.set('tab', tabId.replace('#', ''));
                window.history.pushState({}, '', url);
            });
        });
    }

    setupResultsActions() {
        // Reset buttons
        const resetButtons = document.querySelectorAll('[onclick*="reset"]');
        resetButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const action = e.target.getAttribute('onclick');
                if (action.includes('resetAnalysis')) {
                    this.resetPHQ9Form();
                } else if (action.includes('resetJournal')) {
                    this.resetJournalForm();
                }
            });
        });
    }

    submitPHQ9Form(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        // Show loading state
        this.showButtonLoading(submitBtn);

        // Validate all questions are answered
        const questions = form.querySelectorAll('.question-item');
        let allAnswered = true;

        questions.forEach((question, index) => {
            const radios = question.querySelectorAll('input[type="radio"]');
            const answered = Array.from(radios).some(radio => radio.checked);

            if (!answered) {
                allAnswered = false;
                question.classList.add('error');
                setTimeout(() => question.classList.remove('error'), 3000);
            }
        });

        if (!allAnswered) {
            this.hideButtonLoading(submitBtn, originalText);
            this.showNotification('Please answer all questions before submitting.', 'warning');
            return;
        }

        // Simulate processing time (remove this in production)
        setTimeout(() => {
            form.submit();
        }, 1000);
    }

    submitJournalForm(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const textarea = form.querySelector('#journal_text');
        const originalText = submitBtn.textContent;

        // Show loading state
        this.showButtonLoading(submitBtn);

        // Validate minimum length
        if (textarea.value.length < 20) {
            this.hideButtonLoading(submitBtn, originalText);
            this.showNotification('Please write at least 20 characters for analysis.', 'warning');
            return;
        }

        // Simulate processing time (remove this in production)
        setTimeout(() => {
            form.submit();
        }, 1500);
    }

    resetPHQ9Form() {
        const form = document.getElementById('phq9Form');
        if (!form) return;

        // Reset all radio buttons
        const radios = form.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.checked = false;
            radio.parentElement.classList.remove('selected');
        });

        // Reset question items
        const questions = form.querySelectorAll('.question-item');
        questions.forEach(question => {
            question.classList.remove('answered', 'error');
        });

        // Reset progress
        this.updateProgressIndicator();

        // Scroll to top of form
        form.scrollIntoView({ behavior: 'smooth' });
    }

    resetJournalForm() {
        const form = document.getElementById('journalForm');
        const textarea = document.getElementById('journal_text');
        const charCount = document.getElementById('charCount');
        const submitBtn = document.getElementById('journalSubmit');

        if (!form || !textarea) return;

        // Reset form
        textarea.value = '';
        textarea.style.height = 'auto';

        if (charCount) {
            charCount.textContent = '0 characters';
            charCount.style.color = 'var(--danger-color)';
        }

        if (submitBtn) {
            submitBtn.disabled = true;
        }

        // Focus on textarea
        textarea.focus();
    }

    updateProgressIndicator() {
        const form = document.getElementById('phq9Form');
        if (!form) return;

        const questions = form.querySelectorAll('.question-item');
        const answeredQuestions = form.querySelectorAll('.question-item.answered');
        const progress = (answeredQuestions.length / questions.length) * 100;

        // Update progress bar if it exists
        const progressBar = document.querySelector('.phq9-progress');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }

        // Show completion message
        if (progress === 100) {
            this.showNotification('All questions answered! You can now submit the form.', 'success');
        }
    }

    showButtonLoading(button) {
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Analyzing...
        `;
    }

    hideButtonLoading(button, originalText) {
        button.disabled = false;
        button.innerHTML = originalText;
    }

    showNotification(message, type = 'info') {
        // Use the main app's notification system
        if (window.mindTrackApp) {
            window.mindTrackApp.showNotification(message, type);
        } else {
            // Fallback notification
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            const container = document.querySelector('.container');
            if (container) {
                container.insertBefore(alert, container.firstChild);
                setTimeout(() => alert.remove(), 5000);
            }
        }
    }

    // Sentiment analysis visualization
    renderSentimentChart(scores) {
        const canvas = document.getElementById('sentimentChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Negative', 'Neutral'],
                datasets: [{
                    data: [scores.positive, scores.negative, scores.neutral],
                    backgroundColor: [
                        'var(--success-color)',
                        'var(--danger-color)',
                        'var(--warning-color)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.analysisHandler = new AnalysisHandler();
});

// Global functions for onclick handlers
function resetAnalysis() {
    if (window.analysisHandler) {
        window.analysisHandler.resetPHQ9Form();
    }
}

function resetJournal() {
    if (window.analysisHandler) {
        window.analysisHandler.resetJournalForm();
    }
}