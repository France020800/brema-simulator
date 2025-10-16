#!/usr/bin/env python3
import argparse
import datetime
import xml.etree.ElementTree as ET
import csv
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import navy, black, crimson
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import wap_calculator as wap


def generate_pdf_report(filename, results, total_points, failed_rows):
    """
    Generates a PDF report with the summary of results and total score.
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    pdfmetrics.registerFont(TTFont('DejaVuSans', 'fonts/DejaVuSans.ttf'))

    # --- Header ---
    logo_path = 'logo.png'
    try:
        c.drawImage(logo_path, -0.5 * inch, height - 0.5 * inch,
                    height=0.3 * inch, preserveAspectRatio=True, mask='auto')
        title_x_position = width / 2.0
    except IOError:
        print("Warning: 'logo.png' not found. Skipping logo in PDF report.")
        title_x_position = width / 2.0

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(navy)
    c.drawCentredString(title_x_position, height - 1 * inch, "Simulatore Coppa Brema")

    c.setFont("Helvetica", 9)
    c.setFillColor(black)
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawCentredString(title_x_position, height - 1.25 * inch, f"Generato il: {today}")

    # --- Results Table ---
    y_position = height - 2 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(0.75 * inch, y_position, "Sommario")
    y_position -= 0.3 * inch

    # Table Headers
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.75 * inch, y_position, "Atleta")
    c.drawString(2.5 * inch, y_position, "Stile")
    c.drawString(5.5 * inch, y_position, "Tempo")
    c.drawString(6.75 * inch, y_position, "Punteggio")
    y_position -= 0.05 * inch
    c.line(0.75 * inch, y_position, width - 0.75 * inch, y_position)  # Underline
    y_position -= 0.2 * inch

    # Table Rows
    c.setFont("DejaVuSans", 10)
    for res in results:
        full_name = f"{res['name']} {res['surname']}"
        c.drawString(0.75 * inch, y_position, full_name)
        c.drawString(2.5 * inch, y_position, res['stroke'])
        c.drawString(5.5 * inch, y_position, res['time'])
        c.drawRightString(7.5 * inch, y_position, f"{res['points']:.2f}")
        y_position -= 0.25 * inch
        # Add new page if content overflows
        if y_position < 1.5 * inch:
            c.showPage()
            y_position = height - 1 * inch
            c.setFont("DejaVuSans", 10)

    # --- Skipped Rows Section ---
    if failed_rows:
        y_position -= 0.3 * inch
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(crimson)
        c.drawString(0.75 * inch, y_position, "Skipped Entries")
        y_position -= 0.3 * inch

        c.setFont("Courier", 8)
        c.setFillColor(black)
        for entry in failed_rows:
            c.drawString(0.75 * inch, y_position, entry)
            y_position -= 0.15 * inch
            if y_position < 1.5 * inch:
                c.showPage()
                y_position = height - 1 * inch
                c.setFont("Courier", 8)

    # --- Final Score ---
    y_position -= 0.5 * inch
    if y_position < 1.5 * inch:
        c.showPage()
        y_position = height - 1.5 * inch

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(navy)
    c.line(0.75 * inch, y_position, width - 0.75 * inch, y_position)
    y_position -= 0.3 * inch
    c.drawString(0.75 * inch, y_position, "Punteggio Totale:")
    c.drawRightString(width - 0.75 * inch, y_position, f"{total_points:.2f}")
    y_position -= 0.05 * inch
    c.line(0.75 * inch, y_position, width - 0.75 * inch, y_position)

    c.save()


def main():
    """
    Main function to parse a CSV file and generate a PDF report.
    """
    parser = argparse.ArgumentParser(
        description="Generate a PDF report of World Aquatics points from a CSV file.",
        epilog="Example: python generate_report.py swimmers_data.csv --output report.pdf"
    )

    parser.add_argument("input_file", type=str, help="Path to the input CSV file.")
    parser.add_argument("--output", type=str, default="outs/swimming_points_report.pdf", help="Filename for the output PDF report.")

    args = parser.parse_args()

    # Parse the XML data from the string
    tree = ET.parse('data/brema_basetime.xml')
    root = tree.getroot()

    total_points = 0.0
    processed_results = []
    failed_rows = []

    try:
        with open(args.input_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row_num, row in enumerate(reader, 2):
                try:
                    name = row['name'].strip()
                    surname = row['surname'].strip()
                    course = row['course']
                    gender = row['gender']
                    stroke = row['stroke']
                    time = float(row['time'])

                    if not all([name, surname]):
                        raise ValueError("Name or surname is missing")

                    basetime = wap.find_basetime(root, course, gender, stroke)

                    if basetime is None:
                        raise ValueError(f"Base time not found for event.")

                    points = wap.calculate_points(basetime, time)
                    total_points += points
                    processed_results.append({
                        "name": name,
                        "surname": surname,
                        "stroke": stroke,
                        "time": wap.format_time(time),
                        "points": points
                    })

                except (KeyError, ValueError) as e:
                    failed_rows.append(f"Row {row_num}: Invalid data - {e} -> {row}")
                    continue

    except FileNotFoundError:
        print(f"Error: The file '{args.input_file}' was not found.")
        sys.exit(1)

    # Print summary to console
    print("\n--- Points Calculation Summary ---")
    for result in processed_results:
        print(f"  🏊 {result['stroke']:<25} | Time: {result['time']:<10}s | Points: {result['points']:>7.2f}")

    if failed_rows:
        print("\n--- Skipped Rows ---")
        for failed in failed_rows:
            print(f"  ⚠️  {failed}")

    try:
        generate_pdf_report(args.output, processed_results, total_points, failed_rows)
        print(f"\n✅ Report successfully generated: {args.output}")
    except NameError:
        print("\n❌ PDF generation failed. Make sure you have installed 'reportlab'.")
        print("Install it by running: pip install reportlab")
        print(
            "You may also need to install a font that supports emojis for the report to generate correctly (e.g. DejaVuSans).")
    except Exception as e:
        print(f"\n❌ An error occurred during PDF generation: {e}")

    print("\n----------------------------------")
    print(f"  TOTAL CALCULATED POINTS: {total_points:.2f}")
    print("----------------------------------")


if __name__ == "__main__":
    main()