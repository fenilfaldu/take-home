import json
import os
import sys
import re

RESULTS_PATH = "submission/results.json"
SUMMARY_PATH = "submission/summary.md"


def test_results_file_exists():
    assert os.path.exists(RESULTS_PATH), "results.json not found in submission/"


def test_results_schema():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    required_keys = {
        "segment_with_decline",
        "largest_drop_event",
        "mobile_engagement_change_pct",
        "desktop_engagement_change_pct",
        "regression_start_day",
        "baseline_period",
        "regression_period",
        "country_engagement_changes",
    }
    missing = required_keys - results.keys()
    assert not missing, f"Missing keys in results.json: {missing}"


def test_segment_identification():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    assert results["segment_with_decline"] == "mobile", \
        f"Expected 'mobile', got '{results['segment_with_decline']}'"


def test_funnel_stage_identification():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    # Both interpretations are valid analytical conclusions:
    # - add_to_cart: largest absolute drop in pp (59.8pp)
    # - purchase: largest relative change (-83.8%)
    valid_answers = ["add_to_cart", "purchase"]
    assert results["largest_drop_event"] in valid_answers, \
        f"Expected one of {valid_answers}, got '{results['largest_drop_event']}'"


def test_regression_start_day():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    day = results["regression_start_day"]
    assert isinstance(day, int), \
        f"regression_start_day must be an integer, got {type(day).__name__}"
    # Accept reasonable range for changepoint detection (day 18-26)
    assert 18 <= day <= 26, \
        f"regression_start_day should be in range 18-26 (got {day})"


def test_mobile_engagement_declined():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    mobile_change = results["mobile_engagement_change_pct"]
    assert isinstance(mobile_change, (int, float)), \
        "mobile_engagement_change_pct must be numeric"
    assert mobile_change < 0, \
        f"Mobile engagement should show a decline (negative value), got {mobile_change}%"


def test_mobile_declined_more_than_desktop():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    mobile_change = results["mobile_engagement_change_pct"]
    desktop_change = results["desktop_engagement_change_pct"]
    assert isinstance(desktop_change, (int, float)), \
        "desktop_engagement_change_pct must be numeric"
    assert mobile_change < desktop_change, \
        f"Mobile ({mobile_change}%) should have declined more than desktop ({desktop_change}%)"


def test_country_engagement_changes():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    countries = results["country_engagement_changes"]
    assert isinstance(countries, dict), \
        "country_engagement_changes must be a dictionary"
    assert len(countries) >= 4, \
        f"Expected at least 4 countries in country_engagement_changes, got {len(countries)}"

    for code, val in countries.items():
        assert isinstance(val, (int, float)), \
            f"Country '{code}' engagement change must be numeric, got {type(val).__name__}"


def test_all_countries_declined():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    countries = results["country_engagement_changes"]
    declined = {k: v for k, v in countries.items() if v < 0}
    assert len(declined) >= len(countries) * 0.7, \
        f"Most countries should show decline. Only {len(declined)}/{len(countries)} declined."


def test_engagement_trend_png():
    assert os.path.exists("submission/engagement_trend.png"), \
        "Missing required visualization: submission/engagement_trend.png"


def test_funnel_comparison_png():
    assert os.path.exists("submission/funnel_comparison.png"), \
        "Missing required visualization: submission/funnel_comparison.png"


def test_geographic_breakdown_png():
    assert os.path.exists("submission/geographic_breakdown.png"), \
        "Missing required visualization: submission/geographic_breakdown.png"


def test_mobile_event_volume_png():
    assert os.path.exists("submission/mobile_event_volume.png"), \
        "Missing required visualization: submission/mobile_event_volume.png"


def test_platform_gap_png():
    assert os.path.exists("submission/platform_gap.png"), \
        "Missing required visualization: submission/platform_gap.png"


def test_summary_exists():
    assert os.path.exists(SUMMARY_PATH), "summary.md not found in submission/"


def test_storytelling_structure():
    with open(SUMMARY_PATH) as f:
        content = f.read().lower()

    required_sections = [
        "executive summary",
        "key findings",
        "impacted segment",
        "funnel breakdown",
        "geographic analysis",
        "conclusion",
    ]
    for section in required_sections:
        assert section in content, f"Missing required section: '{section}'"


def test_summary_has_funnel_table():
    with open(SUMMARY_PATH) as f:
        content = f.read()

    pipe_lines = [line for line in content.split("\n") if "|" in line and "---" not in line]
    assert len(pipe_lines) >= 3, \
        f"Funnel Breakdown section must contain a markdown table (found {len(pipe_lines)} table rows)"

    header_line = None
    for line in content.split("\n"):
        if "|" in line and "stage" in line.lower():
            header_line = line.lower()
            break

    if header_line:
        assert "baseline" in header_line, \
            "Funnel table must have a 'Baseline Rate' column"
        assert "recent" in header_line or "regression" in header_line, \
            "Funnel table must have a 'Recent Rate' column"


def test_summary_has_key_findings():
    with open(SUMMARY_PATH) as f:
        content = f.read()

    findings_start = content.lower().find("key findings")
    if findings_start == -1:
        assert False, "Key Findings section not found"

    # Find the end of Key Findings section (next major section)
    next_section = len(content)
    section_headers = ["impacted segment", "funnel breakdown", "geographic analysis", "conclusion", "## "]
    for header in section_headers:
        # Search after Key Findings, case-insensitive for header
        idx = content.lower().find(header, findings_start + 20)
        if idx != -1 and idx < next_section:
            next_section = idx

    findings_text = content[findings_start:next_section]

    # Use regex to properly count markdown list items at line beginnings
    # Count numbered items: lines starting with "1. ", "2. ", etc. (possibly with leading whitespace)
    numbered_items = len(re.findall(r'^\s*\d+\.\s+', findings_text, re.MULTILINE))
    
    # Count bullet items: lines starting with "- " (possibly with leading whitespace)
    bullet_items = len(re.findall(r'^\s*-\s+', findings_text, re.MULTILINE))
    
    # Also count bold headers as findings (e.g., "**1. Finding Name:**" or "**Finding Name**")
    bold_items = len(re.findall(r'^\s*\*\*\d+\.\s+[^*]+\*\*', findings_text, re.MULTILINE))
    bold_items += len(re.findall(r'^\s*\*\*[^*]+\*\*:', findings_text, re.MULTILINE))
    
    total_items = max(numbered_items, bullet_items, bold_items)
    
    assert total_items >= 3, \
        f"Key Findings should contain at least 3 distinct findings, found ~{total_items} (numbered: {numbered_items}, bullets: {bullet_items}, bold: {bold_items})"


if __name__ == "__main__":
    tests = [
        test_results_file_exists,
        test_results_schema,
        test_segment_identification,
        test_funnel_stage_identification,
        test_regression_start_day,
        test_mobile_engagement_declined,
        test_mobile_declined_more_than_desktop,
        test_country_engagement_changes,
        test_all_countries_declined,
        test_engagement_trend_png,
        test_funnel_comparison_png,
        test_geographic_breakdown_png,
        test_mobile_event_volume_png,
        test_platform_gap_png,
        test_summary_exists,
        test_storytelling_structure,
        test_summary_has_funnel_table,
        test_summary_has_key_findings,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL: {test.__name__} - {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR: {test.__name__} - {e}")

    print(f"\n{passed}/{passed + failed} tests passed")
    sys.exit(0 if failed == 0 else 1)