"""
Predictive Analytics for Medicine Adherence
Uses ML to predict patient behavior and optimize reminders
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

# Fixed imports - use main database system
from ..database_models import MedicineSchedule, MedicineReminder, get_db_dependency
from sqlalchemy.orm import Session
from fastapi import Depends

logger = logging.getLogger(__name__)

class PredictiveAnalytics:
    """AI-powered predictive analytics for medicine adherence"""
    
    def __init__(self):
        self.models_initialized = False
        self.adherence_patterns = {}
        
    def analyze_patient_adherence(self, db_session: Session, patient_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Analyze patient's adherence patterns and predict future behavior"""
        try:
                # Get patient's reminder history
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                reminders = db_session.query(MedicineReminder).join(MedicineSchedule).filter(
                    and_(
                        MedicineSchedule.patient_id == patient_id,
                        MedicineReminder.scheduled_time >= start_date,
                        MedicineReminder.scheduled_time <= end_date
                    )
                ).all()
                
                if not reminders:
                    return {'error': 'No reminder data found for patient'}
                
                # Calculate adherence metrics
                total_reminders = len(reminders)
                taken_reminders = len([r for r in reminders if r.status == 'taken'])
                skipped_reminders = len([r for r in reminders if r.status == 'skipped'])
                missed_reminders = len([r for r in reminders if r.status == 'missed'])
                
                adherence_rate = (taken_reminders / total_reminders) * 100 if total_reminders > 0 else 0
                
                # Analyze patterns
                patterns = self._analyze_adherence_patterns(reminders)
                
                # Predict future adherence
                prediction = self._predict_adherence_risk(patterns, adherence_rate)
                
                return {
                    'patient_id': patient_id,
                    'analysis_period_days': days_back,
                    'total_reminders': total_reminders,
                    'taken_reminders': taken_reminders,
                    'skipped_reminders': skipped_reminders,
                    'missed_reminders': missed_reminders,
                    'adherence_rate': round(adherence_rate, 2),
                    'patterns': patterns,
                    'prediction': prediction,
                    'recommendations': self._generate_recommendations(patterns, adherence_rate)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing patient adherence: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_adherence_patterns(self, reminders: List) -> Dict[str, Any]:
        """Analyze patterns in patient's adherence behavior"""
        patterns = {
            'time_patterns': {},
            'day_patterns': {},
            'medicine_patterns': {},
            'escalation_patterns': {}
        }
        
        try:
            # Time-based patterns
            time_adherence = {}
            for reminder in reminders:
                hour = reminder.scheduled_time.hour
                time_slot = self._get_time_slot(hour)
                
                if time_slot not in time_adherence:
                    time_adherence[time_slot] = {'total': 0, 'taken': 0}
                
                time_adherence[time_slot]['total'] += 1
                if reminder.status == 'taken':
                    time_adherence[time_slot]['taken'] += 1
            
            # Calculate adherence rates for each time slot
            for slot in time_adherence:
                total = time_adherence[slot]['total']
                taken = time_adherence[slot]['taken']
                time_adherence[slot]['adherence_rate'] = (taken / total * 100) if total > 0 else 0
            
            patterns['time_patterns'] = time_adherence
            
            # Day-of-week patterns
            day_adherence = {}
            for reminder in reminders:
                day = reminder.scheduled_time.strftime('%A')
                
                if day not in day_adherence:
                    day_adherence[day] = {'total': 0, 'taken': 0}
                
                day_adherence[day]['total'] += 1
                if reminder.status == 'taken':
                    day_adherence[day]['taken'] += 1
            
            # Calculate day-wise adherence rates
            for day in day_adherence:
                total = day_adherence[day]['total']
                taken = day_adherence[day]['taken']
                day_adherence[day]['adherence_rate'] = (taken / total * 100) if total > 0 else 0
            
            patterns['day_patterns'] = day_adherence
            
            # Medicine-specific patterns (if available)
            medicine_adherence = {}
            for reminder in reminders:
                # Note: This requires joining with schedule data
                medicine_name = getattr(reminder, 'medicine_name', 'Unknown')
                
                if medicine_name not in medicine_adherence:
                    medicine_adherence[medicine_name] = {'total': 0, 'taken': 0}
                
                medicine_adherence[medicine_name]['total'] += 1
                if reminder.status == 'taken':
                    medicine_adherence[medicine_name]['taken'] += 1
            
            patterns['medicine_patterns'] = medicine_adherence
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return patterns
    
    def _get_time_slot(self, hour: int) -> str:
        """Convert hour to time slot"""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _predict_adherence_risk(self, patterns: Dict, current_adherence: float) -> Dict[str, Any]:
        """Predict adherence risk based on patterns"""
        try:
            # Simple ML-like prediction based on patterns
            risk_factors = []
            risk_score = 0
            
            # Low overall adherence
            if current_adherence < 70:
                risk_factors.append("Low overall adherence rate")
                risk_score += 30
            elif current_adherence < 85:
                risk_factors.append("Moderate adherence concerns")
                risk_score += 15
            
            # Time-based risk factors
            time_patterns = patterns.get('time_patterns', {})
            for time_slot, data in time_patterns.items():
                if data.get('adherence_rate', 0) < 60:
                    risk_factors.append(f"Poor adherence during {time_slot}")
                    risk_score += 10
            
            # Day-based risk factors
            day_patterns = patterns.get('day_patterns', {})
            weekend_adherence = []
            weekday_adherence = []
            
            for day, data in day_patterns.items():
                rate = data.get('adherence_rate', 0)
                if day in ['Saturday', 'Sunday']:
                    weekend_adherence.append(rate)
                else:
                    weekday_adherence.append(rate)
            
            if weekend_adherence and np.mean(weekend_adherence) < 60:
                risk_factors.append("Poor weekend adherence")
                risk_score += 15
            
            # Determine risk level
            if risk_score >= 40:
                risk_level = 'high'
            elif risk_score >= 20:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'risk_level': risk_level,
                'risk_score': min(risk_score, 100),
                'risk_factors': risk_factors,
                'predicted_adherence_7d': self._predict_short_term_adherence(current_adherence, risk_score),
                'confidence': 0.75  # Model confidence (would be calculated from ML model)
            }
            
        except Exception as e:
            logger.error(f"Error predicting adherence risk: {str(e)}")
            return {'error': str(e)}
    
    def _predict_short_term_adherence(self, current_adherence: float, risk_score: int) -> float:
        """Predict adherence for next 7 days"""
        # Simple prediction model
        base_prediction = current_adherence
        
        # Adjust based on risk factors
        risk_adjustment = risk_score * 0.3
        predicted_adherence = max(0, base_prediction - risk_adjustment)
        
        return round(predicted_adherence, 2)
    
    def _generate_recommendations(self, patterns: Dict, adherence_rate: float) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        try:
            # Overall adherence recommendations
            if adherence_rate < 70:
                recommendations.append("🚨 Critical: Schedule urgent consultation with healthcare provider")
                recommendations.append("📞 Consider setting up family member notifications")
            elif adherence_rate < 85:
                recommendations.append("⚠️ Monitor adherence closely and adjust reminder timing")
            
            # Time-based recommendations
            time_patterns = patterns.get('time_patterns', {})
            worst_time = None
            worst_rate = 100
            
            for time_slot, data in time_patterns.items():
                rate = data.get('adherence_rate', 100)
                if rate < worst_rate:
                    worst_rate = rate
                    worst_time = time_slot
            
            if worst_time and worst_rate < 70:
                recommendations.append(f"⏰ Focus improvement on {worst_time} reminders")
                recommendations.append(f"💡 Consider adjusting {worst_time} medicine timing")
            
            # Day-based recommendations
            day_patterns = patterns.get('day_patterns', {})
            weekend_rates = []
            for day in ['Saturday', 'Sunday']:
                if day in day_patterns:
                    weekend_rates.append(day_patterns[day].get('adherence_rate', 100))
            
            if weekend_rates and np.mean(weekend_rates) < 70:
                recommendations.append("📅 Set special weekend reminder schedule")
                recommendations.append("👨‍👩‍👧‍👦 Involve family in weekend medicine routine")
            
            # General recommendations
            if not recommendations:
                recommendations.append("✅ Excellent adherence! Keep up the good work")
                recommendations.append("📊 Continue current reminder schedule")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Error generating recommendations"]
    
    def get_population_insights(self, medicine_type: Optional[str] = None) -> Dict[str, Any]:
        """Get insights across patient population"""
        try:
            with Session(database_engine) as session:
                # Get population adherence data
                query = session.query(MedicineSchedule)
                if medicine_type:
                    query = query.filter(MedicineSchedule.medicine_name.ilike(f'%{medicine_type}%'))
                
                schedules = query.all()
                
                if not schedules:
                    return {'error': 'No population data found'}
                
                # Calculate population metrics
                total_patients = len(schedules)
                avg_adherence_rates = []
                medicine_popularity = {}
                
                for schedule in schedules:
                    # This would require adherence calculation per patient
                    # For now, using mock data structure
                    medicine_popularity[schedule.medicine_name] = medicine_popularity.get(schedule.medicine_name, 0) + 1
                
                # Sort medicines by popularity
                popular_medicines = sorted(medicine_popularity.items(), key=lambda x: x[1], reverse=True)[:10]
                
                return {
                    'total_patients': total_patients,
                    'medicine_type_filter': medicine_type,
                    'popular_medicines': popular_medicines,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'insights': [
                        f"Analysis covers {total_patients} patients",
                        f"Most prescribed: {popular_medicines[0][0] if popular_medicines else 'N/A'}",
                        "Population data helps optimize reminder strategies"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting population insights: {str(e)}")
            return {'error': str(e)}
    
    def optimize_reminder_timing(self, patient_id: str) -> Dict[str, Any]:
        """Use AI to optimize reminder timing for a patient"""
        try:
            # Analyze current patterns
            analysis = self.analyze_patient_adherence(patient_id, 30)
            if 'error' in analysis:
                return analysis
            
            patterns = analysis.get('patterns', {})
            time_patterns = patterns.get('time_patterns', {})
            
            # Find optimal timing
            optimal_recommendations = []
            
            # Recommend best performing time slots
            best_times = []
            for time_slot, data in time_patterns.items():
                rate = data.get('adherence_rate', 0)
                best_times.append((time_slot, rate))
            
            # Sort by adherence rate
            best_times.sort(key=lambda x: x[1], reverse=True)
            
            if best_times:
                optimal_recommendations.append(f"Best adherence time: {best_times[0][0]} ({best_times[0][1]:.1f}%)")
                
                if len(best_times) > 1 and best_times[-1][1] < 70:
                    optimal_recommendations.append(f"Avoid scheduling during: {best_times[-1][0]} ({best_times[-1][1]:.1f}%)")
            
            return {
                'patient_id': patient_id,
                'current_adherence': analysis.get('adherence_rate', 0),
                'optimal_timing_recommendations': optimal_recommendations,
                'time_slot_performance': time_patterns,
                'optimization_confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error optimizing reminder timing: {str(e)}")
            return {'error': str(e)}

# Global analytics instance
predictive_analytics = PredictiveAnalytics()