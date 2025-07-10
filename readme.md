# MindTrack - Mental Health Companion

## Overview

MindTrack is a comprehensive mental health tracking application that combines AI-powered analysis with traditional clinical assessment tools. The system provides depression detection capabilities through PHQ-9 questionnaires and free-form journal analysis, utilizing machine learning models including BERT and VADER for sentiment analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Authentication**: Replit Auth integration with OAuth2
- **Database**: PostgreSQL with SQLAlchemy models
- **ML Service**: Standalone service for depression detection analysis
- **Session Management**: Flask sessions with ProxyFix middleware

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5
- **Styling**: Custom CSS with Apple-inspired design system
- **JavaScript**: Vanilla JS with modular class-based architecture
- **Charts**: Chart.js for data visualization
- **Responsive Design**: Mobile-first approach with progressive enhancement

## Key Components

### Authentication System
- **Provider**: Replit Auth OAuth2 integration
- **Storage**: Custom UserSessionStorage for token management
- **User Management**: Flask-Login for session handling
- **Security**: JWT tokens with browser session keys

### Machine Learning Service
- **BERT Model**: Fine-tuned BERT for contextual text analysis
- **VADER Sentiment**: Rule-based sentiment analysis
- **Feature Pipeline**: Combined BERT embeddings + VADER scores
- **Classification**: Logistic Regression for depression severity prediction
- **Fallback Mode**: Simplified analysis when ML dependencies unavailable

### Database Models
- **User**: Core user profile with Replit Auth integration
- **PHQ9Assessment**: Structured depression questionnaire results
- **JournalEntry**: Free-form text entries with ML analysis
- **OAuth**: Token storage for authentication
- **UserPreferences**: User-specific settings and preferences

### Core Features
- **PHQ-9 Assessment**: Clinical depression screening questionnaire
- **Journal Analysis**: AI-powered text analysis for mood detection
- **Progress Tracking**: Visual charts and historical data
- **Educational Content**: Mental health information and resources

## Data Flow

### Assessment Flow
1. User completes PHQ-9 questionnaire or journal entry
2. Data validated and stored in database
3. ML service processes text input (if journal)
4. Combined features sent to classification model
5. Results stored and displayed to user

### Analysis Pipeline
1. Text preprocessing (cleaning, tokenization)
2. BERT embedding generation
3. VADER sentiment score calculation
4. Feature combination and scaling
5. Logistic regression prediction
6. Severity classification (Minimal/Mild/Moderate/Severe)

## External Dependencies

### Required ML Models
- **BERT Model**: `fine_tuned_bert/` directory with model weights
- **Scaler**: `scaler.joblib` for feature normalization
- **Classifier**: `logistic_classifier.joblib` for final prediction

### Python Libraries
- **Core**: Flask, SQLAlchemy, Flask-Login, Flask-Dance
- **ML**: transformers, torch, scikit-learn, pandas, numpy
- **Analysis**: vaderSentiment, joblib
- **Utilities**: werkzeug, logging, datetime

### Frontend Dependencies
- **Bootstrap 5**: UI framework and components
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization
- **Google Fonts**: Typography (Inter font family)

## Deployment Strategy

### Environment Configuration
- **Database**: PostgreSQL via `DATABASE_URL` environment variable
- **Authentication**: Replit Auth with `SESSION_SECRET`
- **ML Models**: Expected in `/models/` directory
- **Static Assets**: Served via Flask static file handling

### Production Considerations
- **Model Loading**: Lazy loading with fallback mechanisms
- **Database**: Connection pooling with pre-ping enabled
- **Proxy**: ProxyFix middleware for deployment behind reverse proxy
- **Logging**: Configured for debug and production modes

### Scalability Notes
- ML service designed as standalone component for potential microservice extraction
- Database models optimized with proper relationships and indexing
- Frontend assets minified and cached for performance
- Progressive enhancement ensures functionality without JavaScript

The application follows a monolithic architecture with clear separation of concerns, making it suitable for both development and production deployment while maintaining the flexibility to extract components into microservices as needed.