from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# In-memory storage (use database in production)
workouts = []

@app.route('/')
def index():
    return render_template('index.html', workouts=workouts)

@app.route('/add_workout', methods=['POST'])
def add_workout():
    workout = request.form.get('workout', '').strip()
    duration_str = request.form.get('duration', '').strip()
    
    if not workout or not duration_str:
        flash('Please enter both workout and duration.', 'error')
        return redirect(url_for('index'))
    
    try:
        duration = int(duration_str)
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        workouts.append({
            'id': len(workouts) + 1,
            'workout': workout,
            'duration': duration,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        flash(f"'{workout}' added successfully!", 'success')
    except ValueError:
        flash('Duration must be a positive number.', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_workout/<int:workout_id>', methods=['POST'])
def delete_workout(workout_id):
    global workouts
    workouts = [w for w in workouts if w['id'] != workout_id]
    flash('Workout deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    return jsonify(workouts)

if __name__ == '__main__':
    app.run(debug=True)