"""
Gemini AI Integration Module for Preventive Healthcare Score System.
Handles health score calculation, chatbot, monthly reports, and doctor recommendations.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.0-flash"


def _get_model():
    """Get configured Gemini model."""
    return genai.GenerativeModel(MODEL_NAME)


def calculate_health_score(data):
    """
    Use Gemini AI to calculate a preventive healthcare score (0-100)
    and provide health recommendations.
    """
    if not GEMINI_API_KEY:
        return _local_health_score(data)

    try:
        model = _get_model()
        prompt = f"""You are a preventive healthcare AI assistant. Analyze the following health data and provide:
1. A preventive healthcare score from 0 to 100
2. A risk level: "Healthy" (80-100), "Moderate" (60-79), "Risk" (40-59), "High Risk" (below 40)
3. 5 specific health recommendations
4. A brief health summary

Health Data:
- Age: {data.get('age')}
- Gender: {data.get('gender')}
- Height: {data.get('height')} cm
- Weight: {data.get('weight')} kg
- BMI: {data.get('bmi', 'N/A')}
- Blood Pressure: {data.get('blood_pressure')}
- Sugar Level: {data.get('sugar_level')} mg/dL
- Heart Rate: {data.get('heart_rate')} bpm
- Sleep Hours: {data.get('sleep_hours')} hours/day
- Exercise Minutes: {data.get('exercise_minutes')} min/day
- Steps Per Day: {data.get('steps_per_day')}
- Water Intake: {data.get('water_intake')} liters/day
- Smoking: {data.get('smoking')}
- Alcohol: {data.get('alcohol')}

Respond ONLY with valid JSON in this exact format:
{{
    "score": <integer 0-100>,
    "risk_level": "<Healthy|Moderate|Risk|High Risk>",
    "recommendations": ["<rec1>", "<rec2>", "<rec3>", "<rec4>", "<rec5>"],
    "summary": "<brief health summary>"
}}"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        # Validate score range
        result["score"] = max(0, min(100, int(result.get("score", 50))))
        return result

    except Exception as e:
        print(f"Gemini API error: {e}")
        return _local_health_score(data)


def _local_health_score(data):
    """Fallback local health score calculation when Gemini is unavailable."""
    score = 100

    # BMI scoring (ideal: 18.5-24.9)
    bmi = data.get("bmi", 0)
    if bmi:
        bmi = float(bmi)
        if 18.5 <= bmi <= 24.9:
            score -= 0
        elif 25 <= bmi <= 29.9:
            score -= 10
        elif bmi >= 30:
            score -= 20
        elif bmi < 18.5:
            score -= 10

    # Blood pressure scoring
    bp = data.get("blood_pressure", "120/80")
    try:
        systolic, diastolic = map(int, bp.split("/"))
        if systolic > 140 or diastolic > 90:
            score -= 15
        elif systolic > 130 or diastolic > 85:
            score -= 8
    except (ValueError, AttributeError):
        pass

    # Sugar level scoring (normal: 70-100 fasting)
    sugar = float(data.get("sugar_level", 90))
    if sugar > 200:
        score -= 20
    elif sugar > 140:
        score -= 12
    elif sugar > 100:
        score -= 5

    # Heart rate scoring (ideal: 60-100)
    hr = float(data.get("heart_rate", 72))
    if hr < 50 or hr > 120:
        score -= 10
    elif hr < 60 or hr > 100:
        score -= 5

    # Sleep scoring (ideal: 7-9 hours)
    sleep = float(data.get("sleep_hours", 7))
    if sleep < 5 or sleep > 10:
        score -= 10
    elif sleep < 6 or sleep > 9:
        score -= 5

    # Exercise scoring (ideal: 30+ min/day)
    exercise = float(data.get("exercise_minutes", 0))
    if exercise >= 60:
        score -= 0
    elif exercise >= 30:
        score -= 2
    elif exercise >= 15:
        score -= 8
    else:
        score -= 15

    # Steps scoring (ideal: 10000+)
    steps = float(data.get("steps_per_day", 0))
    if steps >= 10000:
        score -= 0
    elif steps >= 7000:
        score -= 3
    elif steps >= 5000:
        score -= 7
    else:
        score -= 12

    # Water intake scoring (ideal: 2-3L)
    water = float(data.get("water_intake", 2))
    if water >= 3:
        score -= 0
    elif water >= 2:
        score -= 2
    elif water >= 1:
        score -= 7
    else:
        score -= 12

    # Smoking penalty
    smoking = data.get("smoking", "No")
    if smoking and smoking.lower() in ["yes", "true", "1"]:
        score -= 15

    # Alcohol penalty
    alcohol = data.get("alcohol", "No")
    if alcohol and alcohol.lower() in ["yes", "true", "1"]:
        score -= 8

    score = max(0, min(100, score))

    # Determine risk level
    if score >= 80:
        risk_level = "Healthy"
    elif score >= 60:
        risk_level = "Moderate"
    elif score >= 40:
        risk_level = "Risk"
    else:
        risk_level = "High Risk"

    # Generate recommendations
    recommendations = _generate_recommendations(data, score)

    return {
        "score": score,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "summary": f"Your preventive healthcare score is {score}/100 ({risk_level}). "
                   f"{'Great job maintaining your health!' if score >= 80 else 'Consider the recommendations below to improve your health.'}"
    }


def _generate_recommendations(data, score):
    """Generate health recommendations based on data."""
    recs = []
    bmi = float(data.get("bmi", 0))
    if bmi > 25:
        recs.append("Consider a balanced diet and regular exercise to bring your BMI into the healthy range (18.5-24.9).")
    elif bmi < 18.5:
        recs.append("Your BMI is below the healthy range. Consider increasing your caloric intake with nutritious foods.")

    sleep = float(data.get("sleep_hours", 7))
    if sleep < 7:
        recs.append(f"You're sleeping only {sleep} hours. Aim for 7-9 hours of quality sleep per night.")

    exercise = float(data.get("exercise_minutes", 0))
    if exercise < 30:
        recs.append(f"Increase your daily exercise to at least 30 minutes. Currently at {exercise} minutes.")

    steps = float(data.get("steps_per_day", 0))
    if steps < 7000:
        recs.append(f"Try to walk more! Aim for at least 10,000 steps daily. Currently at {int(steps)} steps.")

    water = float(data.get("water_intake", 2))
    if water < 2:
        recs.append(f"Increase your water intake to at least 2-3 liters per day. Currently at {water}L.")

    smoking = data.get("smoking", "No")
    if smoking and smoking.lower() in ["yes", "true", "1"]:
        recs.append("Quitting smoking is one of the best things you can do for your health. Consider cessation programs.")

    alcohol = data.get("alcohol", "No")
    if alcohol and alcohol.lower() in ["yes", "true", "1"]:
        recs.append("Reduce alcohol consumption to improve liver health and overall well-being.")

    sugar = float(data.get("sugar_level", 90))
    if sugar > 100:
        recs.append("Your sugar level is elevated. Monitor your carbohydrate intake and consider consulting a doctor.")

    if not recs:
        recs.append("Excellent! Keep maintaining your healthy lifestyle.")
        recs.append("Continue with regular health check-ups at least once a year.")

    return recs[:5]


def get_chatbot_response(message, history=None):
    """
    Get an AI chatbot response for health-related questions.
    """
    if not GEMINI_API_KEY:
        return _fallback_chatbot(message)

    try:
        model = _get_model()

        context = """You are a helpful and friendly preventive healthcare AI assistant. 
You provide general health information, wellness tips, and preventive care guidance.
Important: Always remind users to consult with healthcare professionals for medical decisions.
Keep responses concise, practical, and easy to understand.
If asked non-health questions, politely redirect to health topics."""

        chat_history = ""
        if history:
            for msg in history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                chat_history += f"\n{role}: {content}"

        prompt = f"""{context}

{f'Previous conversation:{chat_history}' if chat_history else ''}

User: {message}

Respond helpfully and concisely:"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"Chatbot error: {e}")
        return _fallback_chatbot(message)


def _fallback_chatbot(message):
    """Fallback responses when Gemini is unavailable."""
    message_lower = message.lower()

    if any(word in message_lower for word in ["bmi", "weight", "obesity"]):
        return ("BMI (Body Mass Index) is calculated as weight(kg) / height(m)². "
                "A healthy BMI is between 18.5 and 24.9. "
                "Maintaining a healthy weight through balanced diet and exercise is key to preventive health. "
                "Please consult a healthcare professional for personalized advice.")
    elif any(word in message_lower for word in ["sleep", "insomnia", "rest"]):
        return ("Good sleep is crucial for health! Adults should aim for 7-9 hours per night. "
                "Tips: maintain a consistent sleep schedule, avoid screens before bed, "
                "keep your room cool and dark. If you have persistent sleep issues, consult a doctor.")
    elif any(word in message_lower for word in ["exercise", "workout", "fitness"]):
        return ("The WHO recommends at least 150 minutes of moderate exercise per week. "
                "Start with walking, gradually increase intensity. Mix cardio with strength training. "
                "Even 30 minutes of daily brisk walking can significantly improve your health!")
    elif any(word in message_lower for word in ["diet", "food", "nutrition", "eat"]):
        return ("A balanced diet includes plenty of fruits, vegetables, whole grains, lean proteins, "
                "and healthy fats. Limit processed foods, sugary drinks, and excess sodium. "
                "Stay hydrated with at least 2 liters of water daily.")
    elif any(word in message_lower for word in ["stress", "anxiety", "mental"]):
        return ("Mental health is just as important as physical health! "
                "Try meditation, deep breathing, or yoga for stress relief. "
                "Regular exercise and adequate sleep also help manage stress. "
                "Don't hesitate to seek professional help if needed.")
    elif any(word in message_lower for word in ["blood pressure", "bp", "hypertension"]):
        return ("Normal blood pressure is below 120/80 mmHg. "
                "To maintain healthy BP: reduce sodium, exercise regularly, manage stress, "
                "limit alcohol, and maintain a healthy weight. Monitor your BP regularly.")
    elif any(word in message_lower for word in ["sugar", "diabetes", "glucose"]):
        return ("Normal fasting blood sugar is 70-100 mg/dL. "
                "To manage blood sugar: eat balanced meals, exercise regularly, "
                "limit refined carbs and sugary foods, and maintain a healthy weight. "
                "Regular monitoring is important if you're at risk.")
    elif any(word in message_lower for word in ["heart", "cardiac", "cardiovascular"]):
        return ("Heart health tips: exercise regularly, eat heart-healthy foods (fish, nuts, vegetables), "
                "manage stress, don't smoke, limit alcohol, and monitor your blood pressure and cholesterol. "
                "A resting heart rate of 60-100 bpm is normal for adults.")
    else:
        return ("I'm your preventive healthcare assistant! I can help with questions about: "
                "BMI & weight management, sleep, exercise, nutrition, stress management, "
                "blood pressure, blood sugar, heart health, and general wellness tips. "
                "What would you like to know? Remember to consult a doctor for medical advice.")


def generate_monthly_report(data_list):
    """
    Generate a monthly health report from a list of health data entries.
    """
    if not data_list:
        return {"error": "No health data available for report generation."}

    if not GEMINI_API_KEY:
        return _local_monthly_report(data_list)

    try:
        model = _get_model()

        data_summary = []
        for entry in data_list:
            data_summary.append({
                "date": entry.get("timestamp", "N/A"),
                "score": entry.get("score", "N/A"),
                "bmi": entry.get("bmi", "N/A"),
                "blood_pressure": entry.get("blood_pressure", "N/A"),
                "sugar_level": entry.get("sugar_level", "N/A"),
                "heart_rate": entry.get("heart_rate", "N/A"),
                "sleep_hours": entry.get("sleep_hours", "N/A"),
                "exercise_minutes": entry.get("exercise_minutes", "N/A"),
                "steps_per_day": entry.get("steps_per_day", "N/A"),
                "water_intake": entry.get("water_intake", "N/A"),
            })

        prompt = f"""Analyze this monthly health data and generate a comprehensive health report.

Health Records:
{json.dumps(data_summary, indent=2)}

Provide a JSON response with:
{{
    "overall_trend": "<improving|stable|declining>",
    "average_score": <number>,
    "summary": "<paragraph summary of monthly health>",
    "key_improvements": ["<improvement1>", "<improvement2>"],
    "areas_of_concern": ["<concern1>", "<concern2>"],
    "next_month_goals": ["<goal1>", "<goal2>", "<goal3>"],
    "doctor_visit_recommended": <true|false>,
    "doctor_visit_reason": "<reason if recommended>"
}}"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    except Exception as e:
        print(f"Report generation error: {e}")
        return _local_monthly_report(data_list)


def _local_monthly_report(data_list):
    """Fallback local monthly report generation."""
    scores = [d.get("score", 0) for d in data_list if d.get("score")]
    avg_score = sum(scores) / len(scores) if scores else 0

    if len(scores) >= 2:
        trend = "improving" if scores[-1] > scores[0] else ("declining" if scores[-1] < scores[0] else "stable")
    else:
        trend = "stable"

    return {
        "overall_trend": trend,
        "average_score": round(avg_score, 1),
        "summary": f"Based on {len(data_list)} health entries this month, your average score is {avg_score:.1f}/100. "
                   f"Your health trend is {trend}.",
        "key_improvements": [
            "Continue monitoring your health metrics regularly",
            "Maintain consistency in your health routine"
        ],
        "areas_of_concern": [
            "Ensure all metrics remain in healthy ranges",
            "Consider increasing physical activity if below recommended levels"
        ],
        "next_month_goals": [
            "Maintain or improve your current health score",
            "Aim for at least 30 minutes of daily exercise",
            "Drink at least 2 liters of water daily"
        ],
        "doctor_visit_recommended": avg_score < 60,
        "doctor_visit_reason": "Your average health score is below 60, indicating potential health risks." if avg_score < 60 else ""
    }


def get_doctor_recommendation(score, risk_level, data):
    """Get doctor/specialist recommendation based on health metrics."""
    recommendations = []

    if risk_level in ["High Risk", "Risk"]:
        recommendations.append({
            "specialist": "General Physician",
            "reason": f"Your health score is {score} ({risk_level}). A general checkup is recommended.",
            "urgency": "high" if risk_level == "High Risk" else "medium"
        })

    bp = data.get("blood_pressure", "120/80")
    try:
        systolic, diastolic = map(int, bp.split("/"))
        if systolic > 140 or diastolic > 90:
            recommendations.append({
                "specialist": "Cardiologist",
                "reason": f"Blood pressure ({bp}) is above normal range. Cardiovascular evaluation is advisable.",
                "urgency": "high"
            })
    except (ValueError, AttributeError):
        pass

    sugar = float(data.get("sugar_level", 90))
    if sugar > 140:
        recommendations.append({
            "specialist": "Endocrinologist",
            "reason": f"Blood sugar level ({sugar} mg/dL) is elevated. Screening for diabetes is recommended.",
            "urgency": "high" if sugar > 200 else "medium"
        })

    hr = float(data.get("heart_rate", 72))
    if hr < 50 or hr > 120:
        recommendations.append({
            "specialist": "Cardiologist",
            "reason": f"Heart rate ({hr} bpm) is outside the normal range. Cardiac evaluation is advisable.",
            "urgency": "high"
        })

    bmi = float(data.get("bmi", 22))
    if bmi > 30:
        recommendations.append({
            "specialist": "Nutritionist / Dietitian",
            "reason": f"BMI ({bmi:.1f}) indicates obesity. A nutrition plan can help achieve a healthy weight.",
            "urgency": "medium"
        })
    elif bmi < 18.5:
        recommendations.append({
            "specialist": "Nutritionist / Dietitian",
            "reason": f"BMI ({bmi:.1f}) is below healthy range. Nutritional assessment is recommended.",
            "urgency": "medium"
        })

    sleep = float(data.get("sleep_hours", 7))
    if sleep < 5:
        recommendations.append({
            "specialist": "Sleep Specialist",
            "reason": f"Only {sleep} hours of sleep per night. A sleep assessment may help identify issues.",
            "urgency": "medium"
        })

    if not recommendations:
        recommendations.append({
            "specialist": "General Physician",
            "reason": "All metrics look good! An annual preventive checkup is still recommended.",
            "urgency": "low"
        })

    return recommendations
