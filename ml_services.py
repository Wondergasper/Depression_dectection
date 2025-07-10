import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# ML Libraries
try:
    import joblib
    from transformers import BertTokenizer, BertForSequenceClassification
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    import torch
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
except ImportError as e:
    logging.error(f"ML dependencies not installed: {e}")
    # Fallback mode - will use simplified analysis
    joblib = None
    BertTokenizer = None
    BertForSequenceClassification = None
    SentimentIntensityAnalyzer = None
    torch = None
    StandardScaler = None
    LogisticRegression = None

class MLService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bert_model = None
        self.bert_tokenizer = None
        self.vader_analyzer = None
        self.scaler = None
        self.classifier = None
        self.model_loaded = False
        
        # PHQ-9 question mapping
        self.phq9_questions = [
            "Little interest or pleasure in doing things",
            "Feeling down, depressed, or hopeless",
            "Trouble falling or staying asleep, or sleeping too much",
            "Feeling tired or having little energy",
            "Poor appetite or overeating",
            "Feeling bad about yourself or that you are a failure or have let yourself or your family down",
            "Trouble concentrating on things, such as reading the newspaper or watching television",
            "Moving or speaking so slowly that other people could have noticed, or the opposite being so fidgety or restless that you have been moving around a lot more than usual",
            "Thoughts that you would be better off dead, or of hurting yourself",
        ]
        
        # Load models if available
        self._load_models()
    
    def _load_models(self):
        """Load ML models if available"""
        try:
            # Try to load BERT model
            if BertTokenizer and BertForSequenceClassification:
                model_path = os.path.join('models', 'fine_tuned_bert')
                if os.path.exists(model_path):
                    self.bert_tokenizer = BertTokenizer.from_pretrained(model_path)
                    self.bert_model = BertForSequenceClassification.from_pretrained(model_path)
                    self.bert_model.eval()
                    self.logger.info("BERT model loaded successfully")
                else:
                    self.logger.warning("BERT model directory not found. Create 'models/fine_tuned_bert' and upload model files.")
                
            # Initialize VADER
            if SentimentIntensityAnalyzer:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.logger.info("VADER analyzer initialized")
            
            # Load scaler and classifier
            if joblib:
                scaler_path = os.path.join('models', 'scaler.joblib')
                classifier_path = os.path.join('models', 'logistic_classifier.joblib')
                
                if os.path.exists(scaler_path):
                    self.scaler = joblib.load(scaler_path)
                    self.logger.info("Scaler loaded successfully")
                else:
                    self.logger.warning("Scaler file not found. Upload scaler.joblib to models/ directory.")
                
                if os.path.exists(classifier_path):
                    self.classifier = joblib.load(classifier_path)
                    self.logger.info("Classifier loaded successfully")
                else:
                    self.logger.warning("Classifier file not found. Upload logistic_classifier.joblib to models/ directory.")
            
            self.model_loaded = all([
                self.bert_model is not None,
                self.vader_analyzer is not None,
                self.scaler is not None,
                self.classifier is not None
            ])
            
            if self.model_loaded:
                self.logger.info("All ML models loaded successfully")
            else:
                self.logger.warning("Some ML models are missing. Using fallback analysis.")
                
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            self.model_loaded = False
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
        
        # Basic text cleaning
        text = text.lower().strip()
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text
    
    def get_bert_embedding(self, text: str) -> Optional[np.ndarray]:
        """Extract BERT embeddings from text"""
        if not self.bert_model or not self.bert_tokenizer:
            return None
        
        try:
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            # Tokenize
            inputs = self.bert_tokenizer(
                processed_text,
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.bert_model(**inputs, output_hidden_states=True)
                # Extract [CLS] token embedding from last hidden state
                cls_embedding = outputs.hidden_states[-1][:, 0, :].squeeze()
                return cls_embedding.numpy()
                
        except Exception as e:
            self.logger.error(f"Error getting BERT embedding: {e}")
            return None
    
    def get_vader_scores(self, text: str) -> Dict[str, float]:
        """Get VADER sentiment scores"""
        if not self.vader_analyzer:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0, "compound": 0.0}
        
        try:
            processed_text = self.preprocess_text(text)
            scores = self.vader_analyzer.polarity_scores(processed_text)
            return {
                "positive": scores["pos"],
                "negative": scores["neg"],
                "neutral": scores["neu"],
                "compound": scores["compound"]
            }
        except Exception as e:
            self.logger.error(f"Error getting VADER scores: {e}")
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0, "compound": 0.0}
    
    def analyze_phq9(self, responses: List[int]) -> Dict:
        """Analyze PHQ-9 responses"""
        if len(responses) != 9:
            raise ValueError("PHQ-9 requires exactly 9 responses")
        
        # Calculate total score
        total_score = sum(responses)
        
        # Determine severity level
        if total_score <= 4:
            severity = "Minimal"
            description = "Minimal or no depression"
        elif total_score <= 9:
            severity = "Mild"
            description = "Mild depression"
        elif total_score <= 14:
            severity = "Moderate"
            description = "Moderate depression"
        elif total_score <= 19:
            severity = "Moderately Severe"
            description = "Moderately severe depression"
        else:
            severity = "Severe"
            description = "Severe depression"
        
        # Generate recommendations
        recommendations = self._get_phq9_recommendations(severity, total_score)
        
        return {
            "total_score": total_score,
            "max_score": 27,
            "severity": severity,
            "description": description,
            "recommendations": recommendations,
            "analysis_type": "PHQ-9"
        }
    
    def analyze_journal_text(self, text: str) -> Dict:
        """Analyze journal text using ML models"""
        if not text or len(text.strip()) < 10:
            return {
                "error": "Text too short for analysis",
                "analysis_type": "Journal"
            }
        
        # Get VADER scores
        vader_scores = self.get_vader_scores(text)
        
        # Initialize results
        results = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "vader_scores": vader_scores,
            "analysis_type": "Journal"
        }
        
        # If ML models are available, use them
        if self.model_loaded:
            try:
                # Get BERT embedding
                bert_embedding = self.get_bert_embedding(text)
                
                if bert_embedding is not None:
                    # Combine features
                    vader_features = np.array([
                        vader_scores["positive"],
                        vader_scores["negative"],
                        vader_scores["neutral"],
                        vader_scores["compound"]
                    ])
                    
                    # Combine BERT embedding with VADER scores
                    combined_features = np.concatenate([bert_embedding, vader_features])
                    combined_features = combined_features.reshape(1, -1)
                    
                    # Scale features
                    scaled_features = self.scaler.transform(combined_features)
                    
                    # Make prediction
                    prediction = self.classifier.predict(scaled_features)[0]
                    confidence = self.classifier.predict_proba(scaled_features)[0].max()
                    
                    # Map prediction to severity
                    severity_map = {0: "Minimal", 1: "Mild", 2: "Moderate", 3: "Severe"}
                    predicted_severity = severity_map.get(prediction, "Unknown")
                    
                    results.update({
                        "ml_prediction": prediction,
                        "predicted_severity": predicted_severity,
                        "confidence": confidence,
                        "bert_embedding": bert_embedding.tolist(),  # For storage
                        "recommendations": self._get_journal_recommendations(predicted_severity, vader_scores)
                    })
                    
            except Exception as e:
                self.logger.error(f"Error in ML analysis: {e}")
                results["ml_error"] = str(e)
        
        # Fallback analysis based on VADER scores
        if "predicted_severity" not in results:
            results.update(self._fallback_analysis(vader_scores))
        
        return results
    
    def _fallback_analysis(self, vader_scores: Dict[str, float]) -> Dict:
        """Fallback analysis when ML models are not available"""
        compound = vader_scores["compound"]
        negative = vader_scores["negative"]
        
        # Simple rule-based classification
        if compound <= -0.5 or negative >= 0.4:
            severity = "Moderate"
        elif compound <= -0.2 or negative >= 0.2:
            severity = "Mild"
        else:
            severity = "Minimal"
        
        return {
            "predicted_severity": severity,
            "confidence": 0.7,  # Lower confidence for rule-based
            "method": "rule_based",
            "recommendations": self._get_journal_recommendations(severity, vader_scores)
        }
    
    def _get_phq9_recommendations(self, severity: str, score: int) -> List[str]:
        """Get recommendations based on PHQ-9 results"""
        recommendations = []
        
        if severity == "Minimal":
            recommendations = [
                "Continue maintaining good mental health habits",
                "Practice regular self-care activities",
                "Stay connected with supportive people",
                "Consider journaling to track your mood"
            ]
        elif severity == "Mild":
            recommendations = [
                "Consider talking to a counselor or therapist",
                "Engage in regular physical activity",
                "Practice stress management techniques",
                "Maintain a regular sleep schedule",
                "Connect with friends and family"
            ]
        elif severity == "Moderate":
            recommendations = [
                "Strongly consider professional counseling",
                "Discuss your symptoms with a healthcare provider",
                "Consider mindfulness or meditation practices",
                "Maintain social connections",
                "Avoid alcohol and substance use"
            ]
        else:  # Moderately Severe or Severe
            recommendations = [
                "Seek immediate professional help",
                "Contact your healthcare provider",
                "Consider medication evaluation",
                "Inform trusted friends or family about your situation",
                "Remove access to means of self-harm"
            ]
        
        if score >= 15:
            recommendations.insert(0, "⚠️ Consider immediate professional support")
        
        return recommendations
    
    def _get_journal_recommendations(self, severity: str, vader_scores: Dict[str, float]) -> List[str]:
        """Get recommendations based on journal analysis"""
        recommendations = []
        
        if severity == "Minimal":
            recommendations = [
                "Continue expressing your thoughts through writing",
                "Practice gratitude journaling",
                "Celebrate small victories",
                "Maintain healthy routines"
            ]
        elif severity == "Mild":
            recommendations = [
                "Continue regular journaling",
                "Focus on positive coping strategies",
                "Consider talking to someone you trust",
                "Practice self-compassion"
            ]
        elif severity == "Moderate":
            recommendations = [
                "Consider professional support",
                "Use journaling to identify patterns",
                "Practice mindfulness techniques",
                "Maintain social connections"
            ]
        else:  # Severe
            recommendations = [
                "Seek professional help immediately",
                "Share your concerns with trusted people",
                "Use journaling as a tool with professional guidance",
                "Focus on safety and self-care"
            ]
        
        # Add specific recommendations based on VADER scores
        if vader_scores["negative"] > 0.3:
            recommendations.append("Consider challenging negative thought patterns")
        if vader_scores["positive"] < 0.1:
            recommendations.append("Try to identify and engage in pleasant activities")
        
        return recommendations

# Global ML service instance
ml_service = MLService()
