from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, Text, Float, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    phq9_assessments = relationship("PHQ9Assessment", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    
    def get_display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.email:
            return self.email.split('@')[0]
        return f"User {self.id[:8]}"

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class PHQ9Assessment(db.Model):
    __tablename__ = 'phq9_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # PHQ-9 responses (0-3 scale)
    q1_interest = db.Column(db.Integer, nullable=False)  # Little interest or pleasure
    q2_depression = db.Column(db.Integer, nullable=False)  # Feeling down, depressed
    q3_sleep = db.Column(db.Integer, nullable=False)  # Sleep problems
    q4_energy = db.Column(db.Integer, nullable=False)  # Feeling tired
    q5_appetite = db.Column(db.Integer, nullable=False)  # Poor appetite
    q6_selfworth = db.Column(db.Integer, nullable=False)  # Feeling bad about yourself
    q7_concentration = db.Column(db.Integer, nullable=False)  # Trouble concentrating
    q8_psychomotor = db.Column(db.Integer, nullable=False)  # Moving/speaking slowly
    q9_suicidal = db.Column(db.Integer, nullable=False)  # Thoughts of death
    
    # Calculated scores
    total_score = db.Column(db.Integer, nullable=False)
    severity_level = db.Column(db.String(50), nullable=False)
    
    # ML prediction results
    bert_prediction = db.Column(db.Float, nullable=True)
    vader_compound = db.Column(db.Float, nullable=True)
    ml_confidence = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="phq9_assessments")

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Journal content
    content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    
    # ML analysis results
    bert_embedding = db.Column(db.Text, nullable=True)  # Serialized embedding
    vader_positive = db.Column(db.Float, nullable=True)
    vader_negative = db.Column(db.Float, nullable=True)
    vader_neutral = db.Column(db.Float, nullable=True)
    vader_compound = db.Column(db.Float, nullable=True)
    
    # Depression prediction
    depression_probability = db.Column(db.Float, nullable=True)
    severity_prediction = db.Column(db.String(50), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="journal_entries")

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    reminder_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    
    # Privacy settings
    data_sharing = db.Column(db.Boolean, default=False)
    anonymous_analytics = db.Column(db.Boolean, default=True)
    
    # Display preferences
    theme = db.Column(db.String(20), default='light')
    timezone = db.Column(db.String(50), default='UTC')
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User")
