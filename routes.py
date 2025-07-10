from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import logging

from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import User, PHQ9Assessment, JournalEntry, UserPreferences
from ml_service import ml_service

# Register authentication blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page - shows login for anonymous users, dashboard for authenticated users"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard for authenticated users"""
    # Get recent assessments
    recent_phq9 = PHQ9Assessment.query.filter_by(user_id=current_user.id).order_by(PHQ9Assessment.created_at.desc()).limit(5).all()
    recent_journal = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(5).all()
    
    # Calculate statistics
    total_assessments = PHQ9Assessment.query.filter_by(user_id=current_user.id).count()
    total_journal_entries = JournalEntry.query.filter_by(user_id=current_user.id).count()
    
    # Get latest scores for trend
    latest_phq9 = PHQ9Assessment.query.filter_by(user_id=current_user.id).order_by(PHQ9Assessment.created_at.desc()).first()
    
    return render_template('dashboard.html', 
                         recent_phq9=recent_phq9,
                         recent_journal=recent_journal,
                         total_assessments=total_assessments,
                         total_journal_entries=total_journal_entries,
                         latest_phq9=latest_phq9)

@app.route('/analysis')
@require_login
def analysis():
    """Analysis page with PHQ-9 and journal tabs"""
    return render_template('analysis.html')

@app.route('/phq9', methods=['GET', 'POST'])
@require_login
def phq9_assessment():
    """PHQ-9 assessment handling"""
    if request.method == 'POST':
        try:
            # Extract responses
            responses = []
            for i in range(9):
                response = request.form.get(f'q{i}')
                if response is None:
                    flash('Please answer all questions', 'error')
                    return redirect(url_for('analysis'))
                responses.append(int(response))
            
            # Analyze responses
            analysis_result = ml_service.analyze_phq9(responses)
            
            # Create assessment record
            assessment = PHQ9Assessment(
                user_id=current_user.id,
                q1_interest=responses[0],
                q2_depression=responses[1],
                q3_sleep=responses[2],
                q4_energy=responses[3],
                q5_appetite=responses[4],
                q6_selfworth=responses[5],
                q7_concentration=responses[6],
                q8_psychomotor=responses[7],
                q9_suicidal=responses[8],
                total_score=analysis_result['total_score'],
                severity_level=analysis_result['severity']
            )
            
            db.session.add(assessment)
            db.session.commit()
            
            flash(f'Assessment completed. Score: {analysis_result["total_score"]}/27 - {analysis_result["severity"]}', 'success')
            return render_template('analysis.html', 
                                 phq9_result=analysis_result,
                                 assessment=assessment,
                                 active_tab='phq9')
            
        except Exception as e:
            logging.error(f"PHQ-9 analysis error: {e}")
            flash('Error processing assessment. Please try again.', 'error')
            return redirect(url_for('analysis'))
    
    return redirect(url_for('analysis'))

@app.route('/journal', methods=['GET', 'POST'])
@require_login
def journal_analysis():
    """Journal analysis handling"""
    if request.method == 'POST':
        try:
            journal_text = request.form.get('journal_text', '').strip()
            
            if len(journal_text) < 20:
                flash('Please write at least 20 characters for analysis', 'error')
                return redirect(url_for('analysis'))
            
            # Analyze journal text
            analysis_result = ml_service.analyze_journal_text(journal_text)
            
            if 'error' in analysis_result:
                flash(analysis_result['error'], 'error')
                return redirect(url_for('analysis'))
            
            # Create journal entry
            entry = JournalEntry(
                user_id=current_user.id,
                content=journal_text,
                word_count=analysis_result['word_count'],
                vader_positive=analysis_result['vader_scores']['positive'],
                vader_negative=analysis_result['vader_scores']['negative'],
                vader_neutral=analysis_result['vader_scores']['neutral'],
                vader_compound=analysis_result['vader_scores']['compound'],
                severity_prediction=analysis_result.get('predicted_severity', 'Unknown'),
                confidence_score=analysis_result.get('confidence', 0.0)
            )
            
            # Store BERT embedding if available
            if 'bert_embedding' in analysis_result:
                import json
                entry.bert_embedding = json.dumps(analysis_result['bert_embedding'])
            
            db.session.add(entry)
            db.session.commit()
            
            flash(f'Journal analyzed. Predicted severity: {analysis_result.get("predicted_severity", "Unknown")}', 'success')
            return render_template('analysis.html', 
                                 journal_result=analysis_result,
                                 entry=entry,
                                 active_tab='journal')
            
        except Exception as e:
            logging.error(f"Journal analysis error: {e}")
            flash('Error analyzing journal entry. Please try again.', 'error')
            return redirect(url_for('analysis'))
    
    return redirect(url_for('analysis'))

@app.route('/journal_history')
@require_login
def journal_history():
    """View journal history"""
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).all()
    return render_template('journal.html', entries=entries)

@app.route('/profile')
@require_login
def profile():
    """User profile page"""
    # Get user preferences
    preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        # Create default preferences
        preferences = UserPreferences(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    
    # Get user statistics
    stats = {
        'total_assessments': PHQ9Assessment.query.filter_by(user_id=current_user.id).count(),
        'total_journal_entries': JournalEntry.query.filter_by(user_id=current_user.id).count(),
        'member_since': current_user.created_at,
        'last_assessment': PHQ9Assessment.query.filter_by(user_id=current_user.id).order_by(PHQ9Assessment.created_at.desc()).first(),
        'last_journal': JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).first()
    }
    
    return render_template('profile.html', preferences=preferences, stats=stats)

@app.route('/education')
@require_login
def education():
    """Educational resources page"""
    return render_template('education.html')

@app.route('/api/chart-data')
@require_login
def chart_data():
    """API endpoint for chart data"""
    # Get PHQ-9 data for the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    phq9_data = PHQ9Assessment.query.filter(
        PHQ9Assessment.user_id == current_user.id,
        PHQ9Assessment.created_at >= thirty_days_ago
    ).order_by(PHQ9Assessment.created_at.asc()).all()
    
    # Get journal sentiment data
    journal_data = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= thirty_days_ago
    ).order_by(JournalEntry.created_at.asc()).all()
    
    # Format data for charts
    chart_data = {
        'phq9_scores': [
            {
                'date': assessment.created_at.strftime('%Y-%m-%d'),
                'score': assessment.total_score,
                'severity': assessment.severity_level
            } for assessment in phq9_data
        ],
        'journal_sentiment': [
            {
                'date': entry.created_at.strftime('%Y-%m-%d'),
                'compound': entry.vader_compound,
                'positive': entry.vader_positive,
                'negative': entry.vader_negative
            } for entry in journal_data
        ]
    }
    
    return jsonify(chart_data)

@app.route('/update_preferences', methods=['POST'])
@require_login
def update_preferences():
    """Update user preferences"""
    try:
        preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            preferences = UserPreferences(user_id=current_user.id)
            db.session.add(preferences)
        
        # Update preferences from form
        preferences.email_notifications = 'email_notifications' in request.form
        preferences.reminder_frequency = request.form.get('reminder_frequency', 'daily')
        preferences.data_sharing = 'data_sharing' in request.form
        preferences.anonymous_analytics = 'anonymous_analytics' in request.form
        preferences.theme = request.form.get('theme', 'light')
        preferences.timezone = request.form.get('timezone', 'UTC')
        
        db.session.commit()
        flash('Preferences updated successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error updating preferences: {e}")
        flash('Error updating preferences', 'error')
    
    return redirect(url_for('profile'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'ml_service': ml_service.model_loaded,
        'timestamp': datetime.now().isoformat()
    })
