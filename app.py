# app.py

import os
import datetime
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from test_runner import run_test_generation

app = Flask(__name__)
REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Cache for current session
last_test_result = {}
last_user_code = ""

@app.route("/", methods=["GET", "POST"])
def index():
    global last_test_result, last_user_code

    if request.method == "POST":
        last_user_code = request.form["code"]
        result = run_test_generation(last_user_code)
        last_test_result = result

        return render_template(
            "index.html",
            user_code=last_user_code,
            generated_tests=result["generated_tests"],
            test_output=result["test_output"],
            summary=result["summary"]
        )

    return render_template("index.html")

@app.route("/download/pdf")
def download_pdf():
    global last_test_result, last_user_code

    if not last_test_result:
        return "No test results found. Run tests first.", 400

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(REPORTS_DIR, f"test_report_{timestamp}.pdf")

    # Create a PDF document
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin

    def add_section(title, content):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, title)
        y -= 20
        c.setFont("Courier", 9)
        for line in content.splitlines():
            for wrapped_line in wrap_text(line, width - 2 * margin, c):
                c.drawString(margin, y, wrapped_line)
                y -= 12
                if y < 60:
                    c.showPage()
                    y = height - margin

    def wrap_text(text, max_width, canvas_obj):
        words = text.strip().split()
        lines = []
        line = ""
        for word in words:
            test_line = line + " " + word if line else word
            if canvas_obj.stringWidth(test_line, "Courier", 9) < max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "AI-Powered Unit Test Report")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    # Code sections
    add_section("User-Submitted Code:", last_user_code)
    add_section("Generated Test Cases:", last_test_result["generated_tests"])
    add_section("Test Execution Output:", last_test_result["test_output"])
    add_section("Summary:", last_test_result["summary"])

    # Save PDF
    c.save()
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
