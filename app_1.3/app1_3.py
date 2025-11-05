from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from datetime import datetime, date
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors as rl_colors
from reportlab.lib.utils import ImageReader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "replace-with-secure-key"

# ---------- Color Palette (used in templates CSS) ----------
COLOR_PRIMARY = "#4CAF50"
COLOR_SECONDARY = "#2196F3"

# ---------- MET Values ----------
MET_VALUES = {
    "Warm-up": 3,
    "Workout": 6,
    "Cool-down": 2.5
}

# ---------- In-memory data stores ----------
user_info = {}  # {"name":..., "regn_id":..., "age":..., "gender":..., "height":..., "weight":..., "bmi":..., "bmr":...}
workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}
daily_workouts = {}  # date_iso -> {"Warm-up": [], "Workout": [], "Cool-down": []}

# ---------- Helpers ----------
def calculate_bmi(weight_kg, height_cm):
    return weight_kg / ((height_cm/100)**2)

def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender.upper() == "M":
        return 10*weight_kg + 6.25*height_cm - 5*age + 5
    else:
        return 10*weight_kg + 6.25*height_cm - 5*age - 161

def calories_from_met(met, weight_kg, duration_min):
    # formula same as original: (MET * 3.5 * weight / 200) * duration
    return (met * 3.5 * weight_kg / 200.0) * duration_min

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html", user_info=user_info)

@app.route("/save_user", methods=["POST"])
def save_user():
    try:
        name = request.form.get("name", "").strip()
        regn_id = request.form.get("regn_id", "").strip()
        age = int(request.form.get("age", "0").strip())
        gender = request.form.get("gender", "M").strip().upper()
        height_cm = float(request.form.get("height", "0").strip())
        weight_kg = float(request.form.get("weight", "0").strip())
        bmi = calculate_bmi(weight_kg, height_cm)
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        user_info.clear()
        user_info.update({
            "name": name,
            "regn_id": regn_id,
            "age": age,
            "gender": gender,
            "height": height_cm,
            "weight": weight_kg,
            "bmi": bmi,
            "bmr": bmr,
            "weekly_cal_goal": 2000
        })
        flash(f"User info saved! BMI={bmi:.1f}, BMR={bmr:.0f} kcal/day", "success")
    except Exception as e:
        flash(f"Invalid input: {e}", "danger")
    return redirect(url_for("index"))

@app.route("/log")
def log():
    return render_template("log.html", workouts=workouts)

@app.route("/add_workout", methods=["POST"])
def add_workout():
    category = request.form.get("category", "Workout")
    exercise = request.form.get("exercise", "").strip()
    duration_str = request.form.get("duration", "").strip()
    if not exercise or not duration_str:
        flash("Please enter both exercise and duration.", "danger")
        return redirect(url_for("log"))
    try:
        duration = int(duration_str)
        if duration <= 0:
            raise ValueError("Duration must be positive.")
    except ValueError:
        flash("Duration must be a positive whole number.", "danger")
        return redirect(url_for("log"))
    weight = user_info.get("weight", 70)
    met = MET_VALUES.get(category, 5)
    calories = calories_from_met(met, weight, duration)
    entry = {
        "exercise": exercise,
        "duration": duration,
        "calories": calories,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    workouts.setdefault(category, []).append(entry)
    today_iso = date.today().isoformat()
    if today_iso not in daily_workouts:
        daily_workouts[today_iso] = {"Warm-up": [], "Workout": [], "Cool-down": []}
    daily_workouts[today_iso].setdefault(category, []).append(entry)
    flash(f"Added {exercise} ({duration} min) to {category}!", "success")
    return redirect(url_for("log"))

@app.route("/summary")
def summary():
    # compute lifetime totals and total minutes
    total_minutes = sum(e['duration'] for sessions in workouts.values() for e in sessions)
    return render_template("summary.html", workouts=workouts, total_minutes=total_minutes)

@app.route("/progress")
def progress():
    totals = {cat: sum(entry['duration'] for entry in sessions) for cat, sessions in workouts.items()}
    total_minutes = sum(totals.values())
    # chart endpoints will render images dynamically
    return render_template("progress.html", totals=totals, total_minutes=total_minutes)



@app.route("/chart_bar.png")
def chart_bar():
    totals = {cat: sum(entry['duration'] for entry in sessions) for cat, sessions in workouts.items()}
    categories = list(totals.keys())
    values = [totals[c] for c in categories]
    if sum(values) == 0:
        # return a small blank image with message
        fig = plt.figure(figsize=(6,3))
        plt.text(0.5,0.5,"No workout data logged yet.", ha='center', va='center')
    else:
        fig, ax = plt.subplots(figsize=(6,3))
        chart_colors = [COLOR_SECONDARY, COLOR_PRIMARY, "#FFC107"]
        ax.bar(categories, values, color=chart_colors)
        ax.set_title("Total Minutes per Category")
        ax.set_ylabel("Total Minutes")
        ax.grid(axis='y', linestyle='-', alpha=0.3)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route("/chart_pie.png")
def chart_pie():
    totals = {cat: sum(entry['duration'] for entry in sessions) for cat, sessions in workouts.items()}
    categories = list(totals.keys())
    values = [totals[c] for c in categories]
    nonzero_labels = [c for c,v in zip(categories, values) if v>0]
    nonzero_values = [v for v in values if v>0]
    if not nonzero_values:
        fig = plt.figure(figsize=(3,3))
        plt.text(0.5,0.5,"No data", ha='center', va='center')
    else:
        fig, ax = plt.subplots(figsize=(3,3))
        chart_colors = [COLOR_SECONDARY, COLOR_PRIMARY, "#FFC107"]
        pie_colors = [chart_colors[i] for i,v in enumerate(values) if v>0]
        ax.pie(nonzero_values, labels=nonzero_labels, autopct="%1.1f%%", startangle=90, colors=pie_colors, wedgeprops={'linewidth':1, 'edgecolor':'white'})
        ax.axis('equal')
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route("/export_pdf")
def export_pdf():
    if not user_info:
        flash("Please save user info first!", "danger")
        return redirect(url_for("index"))
    # create PDF in-memory
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, f"Weekly Fitness Report - {user_info.get('name','')}")
    c.setFont("Helvetica", 11)
    c.drawString(50, height-80, f"Regn-ID: {user_info.get('regn_id','')} | Age: {user_info.get('age','')} | Gender: {user_info.get('gender','')}")
    c.drawString(50, height-100, f"Height: {user_info.get('height','')} cm | Weight: {user_info.get('weight','')} kg | BMI: {user_info.get('bmi',0):.1f} | BMR: {user_info.get('bmr',0):.0f} kcal/day")
    # Table
    y = height-140
    table_data = [["Category","Exercise","Duration(min)","Calories(kcal)","Date"]]
    for cat, sessions in workouts.items():
        for e in sessions:
            table_data.append([cat, e['exercise'], str(e['duration']), f"{e['calories']:.1f}", e['timestamp'].split()[0]])
    table = Table(table_data, colWidths=[80,150,80,80,80])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),rl_colors.lightblue),("GRID",(0,0),(-1,-1),0.5,rl_colors.black)]))
    table.wrapOn(c, width-100, y)
    table.drawOn(c, 50, y-20)
    c.save()
    buffer.seek(0)
    filename = f"{user_info.get('name','user')}_weekly_report.pdf".replace(" ", "_")
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
