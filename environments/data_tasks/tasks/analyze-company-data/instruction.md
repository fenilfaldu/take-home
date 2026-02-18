The product team has flagged a potential engagement regression. Users seem less active recently, but no one has pinpointed the cause.

You have two datasets in the working directory:
* `users.csv`: User attributes including platform and country
* `events.csv`: Timestamped product events spanning 28 days

**Warning**: This is production data — expect inconsistencies, duplicates, and noise. Clean as needed before analysis.

Your task: Investigate the regression, identify the affected segment and broken funnel stage, and tell the story with data.

**Metric**: Engagement = events per user per day = `total_events / (unique_users * days_in_period)`. Change = `((recent - baseline) / baseline) * 100`.

**For largest_drop_event**: Measure this as the largest absolute drop in percentage points (pp), not relative percentage change. For example, a drop from 98.8% to 39.0% is a 59.8pp drop, which is larger than a drop from 64.4% to 10.4% (54.0pp drop), even though the latter has a higher relative percentage change.

**Requirements**:

Write `solution/solve.sh` to produce all outputs in `submission/`:

1. `submission/results.json`:
```json
{
  "segment_with_decline": "<platform>",
  "largest_drop_event": "<event_type>",
  "mobile_engagement_change_pct": <number>,
  "desktop_engagement_change_pct": <number>,
  "regression_start_day": <int>,
  "baseline_period": "<start>-<end>",
  "regression_period": "<start>-<end>",
  "country_engagement_changes": {"<code>": <number>, ...}
}
2. Exactly these visualizations:
   - `submission/engagement_trend.png`
   - `submission/funnel_comparison.png`
   - `submission/geographic_breakdown.png`
   - `submission/mobile_event_volume.png`
   - `submission/platform_gap.png`

3. `submission/summary.md` with sections: Executive Summary, Key Findings (3+), Impacted Segment, Funnel Breakdown (markdown table with Stage/Baseline Rate/Recent Rate/Change columns), Geographic Analysis, Conclusion

Hint: The regression doesn't affect all users equally. Look at platform-level trends to find when behavior shifts, then drill into the funnel.