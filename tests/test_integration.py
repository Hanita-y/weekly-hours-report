"""End-to-end test: fixture → generated HTML and PDF (no live send)."""
from datetime import date, datetime
from unittest.mock import MagicMock


def test_full_pipeline_with_mock_rube(sample_sheet_data, default_config, tmp_path):
    from scripts.sheets_reader import fetch_workbook_via_rube, normalize_workbook
    from scripts.analyzer import build_report
    from scripts.renderer import render_email_html, render_pdf_bytes

    mock_rube = MagicMock()
    mock_rube.execute_tool.return_value = {
        "valueRanges": [
            {"values": sample_sheet_data["tabs"]["אופיר"]},
            {"values": sample_sheet_data["tabs"]["אביב"]},
        ]
    }
    tabs = fetch_workbook_via_rube(
        default_config["sheet"]["spreadsheet_id"],
        default_config["sheet"]["employee_tabs"],
        mock_rube,
    )
    df = normalize_workbook(tabs, default_config)
    report = build_report(df, date(2026, 4, 19), default_config)
    html = render_email_html(report, default_config, datetime(2026, 4, 19, 8, 0))
    pdf = render_pdf_bytes(report, default_config, datetime(2026, 4, 19, 8, 0))

    assert "אופיר" in html
    assert "אביב" in html
    assert pdf[:5] == b"%PDF-"

    # Write outputs to tmp_path for manual inspection if run interactively
    (tmp_path / "email.html").write_text(html, encoding="utf-8")
    (tmp_path / "report.pdf").write_bytes(pdf)
