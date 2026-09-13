"""Generate sample carrier assignment PDF for live demos."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parents[1] / "fixtures" / "pdfs" / "sample_carrier_assignment.pdf"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, "Carrier Assignment\nShipment: SHP-1042\nDelivery: 2026-09-15 14:00")
    OUT.write_bytes(pdf.output())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
