from flask import Flask, render_template

app = Flask(__name__)

# Mock Data
news_list = [
    {"title": "ประกาศวันหยุด", "category": "HR", "date": "18/03/2026", "summary": "แจ้งวันหยุดบริษัท"},
    {"title": "อบรม Safety", "category": "Safety", "date": "20/03/2026", "summary": "อบรมความปลอดภัย"},
]

training_list = [
    {"course": "Core Tools", "date": "25/03/2026", "time": "09:00-16:00", "location": "ห้องมรกต", "trainer": "External", "status": "เปิดรับ"},
]

@app.route("/")
def home():
    return render_template("dashboard/index.html")

@app.route("/news")
def news():
    return render_template("news/index.html", news_list=news_list)

@app.route("/training")
def training():
    return render_template("training/index.html", training_list=training_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
