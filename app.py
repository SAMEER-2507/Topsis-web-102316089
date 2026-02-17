import os
import re
import sys
import smtplib
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "topsis-web-service-secret-key"

# ── SMTP Configuration ──────────────────────────────────────────────
# The user MUST set these environment variables (or edit them here)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "true").lower() == "true"
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")      # sender email
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # app password


# ── TOPSIS Algorithm ────────────────────────────────────────────────
def run_topsis(df, weights, impacts):
    """Perform TOPSIS and return the dataframe with Score and Rank."""
    matrix = df.iloc[:, 1:].values.astype(float)

    # Normalise
    rss = np.sqrt((matrix ** 2).sum(axis=0))
    norm_matrix = matrix / rss

    # Weighted normalised matrix
    weighted_matrix = norm_matrix * weights

    # Ideal best / worst
    ideal_best = np.zeros(weighted_matrix.shape[1])
    ideal_worst = np.zeros(weighted_matrix.shape[1])
    for j in range(weighted_matrix.shape[1]):
        if impacts[j] == "+":
            ideal_best[j] = weighted_matrix[:, j].max()
            ideal_worst[j] = weighted_matrix[:, j].min()
        else:
            ideal_best[j] = weighted_matrix[:, j].min()
            ideal_worst[j] = weighted_matrix[:, j].max()

    # Euclidean distances
    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # Score & Rank
    scores = dist_worst / (dist_best + dist_worst)
    ranks = scores.argsort()[::-1].argsort() + 1

    result = df.copy()
    result["Topsis Score"] = np.round(scores, 2)
    result["Rank"] = ranks.astype(int)
    return result


# ── Email Sending ───────────────────────────────────────────────────
def send_email(to_email, result_df):
    """Send the TOPSIS result CSV as an email attachment."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP credentials not configured. "
            "Set SMTP_EMAIL and SMTP_PASSWORD environment variables."
        )

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = "TOPSIS Analysis Result"

    body = (
        "Hello,\n\n"
        "Please find attached the TOPSIS analysis result.\n\n"
        "Regards,\nTOPSIS Web Service"
    )
    msg.attach(MIMEText(body, "plain"))

    # Create CSV attachment
    csv_content = result_df.to_csv(index=False)
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(csv_content.encode("utf-8"))
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition", "attachment", filename="topsis-result.csv"
    )
    msg.attach(attachment)

    if SMTP_USE_SSL:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)


# ── Validation Helpers ──────────────────────────────────────────────
def validate_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


# ── Routes ──────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # --- Collect form data ---
        file = request.files.get("file")
        weights_str = request.form.get("weights", "").strip()
        impacts_str = request.form.get("impacts", "").strip()
        email = request.form.get("email", "").strip()

        # --- Validations ---
        if not file or file.filename == "":
            flash("Please select a file.", "error")
            return redirect(url_for("index"))

        if not weights_str:
            flash("Please enter weights.", "error")
            return redirect(url_for("index"))

        if not impacts_str:
            flash("Please enter impacts.", "error")
            return redirect(url_for("index"))

        if not email:
            flash("Please enter an email address.", "error")
            return redirect(url_for("index"))

        if not validate_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("index"))

        # Parse weights
        try:
            weights = [float(w.strip()) for w in weights_str.split(",")]
        except ValueError:
            flash("Weights must be numeric values separated by commas.", "error")
            return redirect(url_for("index"))

        # Parse impacts
        impacts = [i.strip() for i in impacts_str.split(",")]
        for imp in impacts:
            if imp not in ("+", "-"):
                flash('Impacts must be either + or - (e.g., "+,+,-,+").', "error")
                return redirect(url_for("index"))

        # Weights and impacts count must match
        if len(weights) != len(impacts):
            flash(
                f"Number of weights ({len(weights)}) must equal "
                f"number of impacts ({len(impacts)}).",
                "error",
            )
            return redirect(url_for("index"))

        # Read the uploaded file
        try:
            filename = file.filename.lower()
            if filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)
        except Exception as e:
            flash(f"Could not read file: {e}", "error")
            return redirect(url_for("index"))

        if df.shape[1] < 3:
            flash("Input file must contain three or more columns.", "error")
            return redirect(url_for("index"))

        # Check numeric columns
        for col in df.columns[1:]:
            if not pd.to_numeric(df[col], errors="coerce").notnull().all():
                flash(
                    f'Column "{col}" contains non-numeric values.',
                    "error",
                )
                return redirect(url_for("index"))

        num_criteria = df.shape[1] - 1
        if len(weights) != num_criteria:
            flash(
                f"Number of weights ({len(weights)}) must match "
                f"number of criteria columns ({num_criteria}).",
                "error",
            )
            return redirect(url_for("index"))

        # --- Run TOPSIS ---
        try:
            result = run_topsis(df, np.array(weights), impacts)
        except Exception as e:
            flash(f"Error running TOPSIS: {e}", "error")
            return redirect(url_for("index"))

        # --- Send Email ---
        try:
            send_email(email, result)
            flash(
                f"Result sent successfully to {email}!",
                "success",
            )
        except Exception as e:
            flash(f"TOPSIS computed but email failed: {e}", "error")

        return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
