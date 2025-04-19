from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from datetime import datetime
from fpdf import FPDF
import requests
import json
import csv

app = Flask(__name__)

# Ensure the reports folder exists
os.makedirs('reports', exist_ok=True)

# Home Route
@app.route("/")
def home():
    return render_template("app.html")

# Vulnerability Scanning Route
@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    url = data.get("url")

    results = {}

    # SQL Injection
    sql_result = check_sql_injection(url)
    results["SQL Injection"] = sql_result["vulnerability"]

    # XSS
    xss_result = check_xss(url)
    results["XSS"] = xss_result["vulnerability"]

    # CSRF
    csrf_result = check_csrf(url)
    results["CSRF"] = csrf_result["vulnerability"]

    # Command Injection
    cmd_injection_result = check_command_injection(url)
    results["Command Injection"] = cmd_injection_result["vulnerability"]

    # Log scan result
    log_scan_result(url, results, file_type="json")

    # Generate PDF report
    pdf_file_path = generate_pdf_report(url, results)

    return jsonify({
        "results": results,
        "pdf_report": f"/reports/{os.path.basename(pdf_file_path)}"  # Provide the correct link for downloading PDF
    })

# PDF Report Generation
def generate_pdf_report(url, results, filename="scan_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="API Vulnerability Scan Report", ln=True, align="C")
    pdf.cell(200, 10, txt=f"Scanned URL: {url}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", size=11)

    for vuln_type, vuln_status in results.items():
        pdf.cell(200, 10, txt=f"{vuln_type}: {vuln_status}", ln=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"reports/scan_report_{timestamp}.pdf"

    pdf.output(full_filename)
    return full_filename

# Route to serve PDF reports
@app.route('/reports/<filename>')
def download_report(filename):
    return send_from_directory('reports', filename, as_attachment=True, mimetype='application/pdf')

# SQL Injection Scanner
def check_sql_injection(url):
    test_payload = "' OR '1'='1"
    try:
        response = requests.post(url, json={"username": test_payload, "password": test_payload})
        if "SQL Injection" in response.text or "error" in response.text.lower():
            return {"vulnerability": "Possible SQL Injection detected!"}
    except Exception as e:
        return {"vulnerability": f"Error testing SQL Injection: {str(e)}"}
    return {"vulnerability": "No SQL Injection vulnerability detected."}

# XSS Scanner
def check_xss(url):
    test_payload = "<script>alert('XSS')</script>"
    try:
        response = requests.post(url, data={"input": test_payload})
        if test_payload in response.text:
            return {"vulnerability": "Possible XSS vulnerability detected!"}
    except Exception as e:
        return {"vulnerability": f"Error testing XSS: {str(e)}"}
    return {"vulnerability": "No XSS vulnerability detected."}

# CSRF Scanner
def check_csrf(url):
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"test": "csrf_test"}
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            if "csrf" not in response.text.lower():
                return {"vulnerability": "Possible CSRF vulnerability detected!"}
    except Exception as e:
        return {"vulnerability": f"Error testing CSRF: {str(e)}"}
    return {"vulnerability": "No CSRF vulnerability detected."}

# Command Injection Scanner
def check_command_injection(url):
    test_payload = "test; ls"
    try:
        response = requests.post(url, json={"input": test_payload})
        indicators = ["bin", "usr", "etc", "home", "root", "lib"]
        if any(indicator in response.text for indicator in indicators):
            return {"vulnerability": "Possible Command Injection detected!"}
    except Exception as e:
        return {"vulnerability": f"Error testing Command Injection: {str(e)}"}
    return {"vulnerability": "No Command Injection vulnerability detected."}

# Function to log scan results
def log_scan_result(url, results, file_type="json"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "url": url,
        "results": results
    }

    if file_type == "json":
        filename = "scan_logs.json"
        filepath = os.path.join("reports", filename)

        # If file exists, load and append; else create new
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(log_entry)

        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    elif file_type == "csv":
        filename = "scan_logs.csv"
        filepath = os.path.join("reports", filename)
        file_exists = os.path.isfile(filepath)

        with open(filepath, "a", newline="") as csvfile:
            fieldnames = ["timestamp", "url"] + list(results.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            row = {"timestamp": timestamp, "url": url}
            row.update(results)
            writer.writerow(row)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)