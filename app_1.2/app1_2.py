from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Initialize workout dictionary
workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}

# Workout Chart Data
workout_chart = {
    "Warm-up": ["5 min Jog", "Jumping Jacks", "Arm Circles", "Leg Swings", "Dynamic Stretching"],
    "Workout": ["Push-ups", "Squats", "Plank", "Lunges", "Burpees", "Crunches"],
    "Cool-down": ["Slow Walking", "Static Stretching", "Deep Breathing", "Yoga Poses"]
}

# Diet Chart Data
diet_plans = {
    "Weight Loss": ["Oatmeal with Fruits", "Grilled Chicken Salad", "Vegetable Soup", "Brown Rice & Stir-fry Veggies"],
    "Muscle Gain": ["Egg Omelet", "Chicken Breast", "Quinoa & Beans", "Protein Shake", "Greek Yogurt with Nuts"],
    "Endurance": ["Banana & Peanut Butter", "Whole Grain Pasta", "Sweet Potatoes", "Salmon & Avocado", "Trail Mix"]
}

@app.route('/')
def index():
    """Main page - Log Workouts"""
    total_time = sum(entry['duration'] for category in workouts.values() for entry in category)
    return render_template('index.html', workouts=workouts, total_time=total_time)

@app.route('/add_workout', methods=['POST'])
def add_workout():
    """Add a workout entry to the log"""
    category = request.form.get('category', 'Workout')
    workout = request.form.get('workout', '').strip()
    duration_str = request.form.get('duration', '').strip()
    
    if not workout or not duration_str:
        flash('Please enter both exercise and duration.', 'error')
        return redirect(url_for('index'))
    
    try:
        duration = int(duration_str)
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        entry = {
            "id": len([e for cat in workouts.values() for e in cat]) + 1,
            "exercise": workout,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        workouts[category].append(entry)
        flash(f'{workout} added to {category} category successfully!', 'success')
        
    except ValueError:
        flash('Duration must be a positive number.', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_workout/<category>/<int:workout_id>', methods=['POST'])
def delete_workout(category, workout_id):
    """Delete a specific workout entry"""
    if category in workouts:
        workouts[category] = [w for w in workouts[category] if w['id'] != workout_id]
        flash('Workout deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/summary')
def summary():
    """Show detailed summary page"""
    total_time = sum(entry['duration'] for category in workouts.values() for entry in category)
    
    # Motivational message based on total time
    if total_time < 30:
        motivation = "Good start! Keep moving 💪"
    elif total_time < 60:
        motivation = "Nice effort! You're building consistency 🔥"
    else:
        motivation = "Excellent dedication! Keep up the great work 🏆"
    
    return render_template('summary.html', workouts=workouts, total_time=total_time, motivation=motivation)

@app.route('/workout-chart')
def workout_chart_page():
    """Display personalized workout chart"""
    return render_template('workout_chart.html', workout_chart=workout_chart)

@app.route('/diet-chart')
def diet_chart_page():
    """Display diet plans for different fitness goals"""
    return render_template('diet_chart.html', diet_plans=diet_plans)

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    """API endpoint to get all workouts as JSON"""
    return jsonify(workouts)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint for workout statistics"""
    stats = {
        "total_time": sum(entry['duration'] for category in workouts.values() for entry in category),
        "total_workouts": sum(len(category) for category in workouts.values()),
        "by_category": {
            cat: {
                "count": len(sessions),
                "total_minutes": sum(e['duration'] for e in sessions)
            } for cat, sessions in workouts.items()
        }
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5002)