# Power BI Build Guide: Release Readiness Dashboard

> Simulated project. Meraki Industries and all data are fictional. Not affiliated with Cisco Meraki.

This guide builds a 2-page Power BI Desktop report on the data in [`/data`](../data), as of **November 13, 2026**.

| File | Use |
|---|---|
| [`measures.dax`](measures.dax) | Calculated tables (Part A), calculated columns (Part B) and measures (Part C) |
| [`meraki-theme.json`](meraki-theme.json) | Report theme. Navy and teal, with green for GO, red for NO-GO and amber for warnings |
| [`../data/README.md`](../data/README.md) | Table and metric definitions. The measures follow them exactly |

Check your result against **[Expected values](#8-expected-values-checklist)** at the end. They match the SQL queries in [`/sql`](../sql).

---

## 1. Set up the file

1. Open Power BI Desktop and go to **File → Options and settings → Options**.
   - **Current file → Data load:** uncheck **Auto date/time** and **Autodetect new relationships after data is loaded**. You will create the date table and the relationships yourself.
   - **Current file → Regional settings:** set the locale to **English (United States)**.
2. Go to **View → Themes → Browse for themes** and select `powerbi/meraki-theme.json`.
3. Save the report as `powerbi/meraki-release-readiness.pbix`.

## 2. Load the CSVs

1. Go to **Home → Get data → Text/CSV**. Load each of the 7 files in `data/` and click **Transform Data**. Every file has a header row, is UTF-8 and uses commas.
2. In Power Query, keep the table names in the table below and set these column types. Empty cells become `null` once the column is typed. If a date column shows `Error`, use **Replace Errors → null**.

| Table | Whole number | Decimal | Date | Text (everything else) |
|---|---|---|---|---|
| depots | wave, technicians | | planned_cutover_date, actual_cutover_date | depot_id, depot_name, region |
| legacy_tickets | | | created_date, closed_date | ticket_id, depot_id, status, priority, customer_id |
| migrated_tickets | wave | | created_date, closed_date, migrated_at | migrated_id, legacy_ticket_id, depot_id, status, priority, customer_id |
| test_cases | wave | | executed_date | test_id, test_type, module, status |
| defects | wave | | opened_date, closed_date | defect_id, severity, status, module, title |
| readiness_criteria | wave, weight, score | threshold, actual_value | assessed_date | criterion_id, criterion, category, comparator, unit, met, gate |
| risks | probability, impact | | | risk_id, description, owner, response, status |

3. **Create the Wave dimension.** Right-click `depots` → **Reference**, rename the new query `Wave`, open **Advanced Editor** and paste:

```m
let
    Source = depots,
    Kept = Table.SelectColumns(Source, {"wave", "region", "planned_cutover_date", "actual_cutover_date"}),
    Distinct = Table.Distinct(Kept),
    Label = Table.AddColumn(Distinct, "Wave Label", each "Wave " & Text.From([wave]) & " - " & [region], type text),
    Sorted = Table.Sort(Label, {{"wave", Order.Ascending}})
in
    Sorted
```

   You should get 4 rows. Labels read like `Wave 3 - Midwest`.

4. **Create the measures table.** Go to **Home → Enter data**, name the table `_Measures`, keep the default column and click **Load**. After you add the measures, hide `Column1`. The table then moves to the top of the Data pane.
5. Click **Close & Apply**.

## 3. Calculated tables and the date table

Go to **Modeling → New table** and paste each table from **Part A** of `measures.dax`:

| Table | Purpose | After creating it |
|---|---|---|
| `Date` | Calendar from Oct 1, 2023 to Jan 31, 2027 | **Table tools → Mark as date table** on `Date[Date]`. Sort `Month` by `Year Month` |
| `Discrepancy Type` | 4 discrepancy types for the Page 2 bar chart. Disconnected, no relationships | Sort `Type` by `Sort` and hide `Sort` |

## 4. Relationships

Open **Model view** and create these relationships. All of them are **single** cross-filter direction and **active** unless noted.

| From (one side) | To (many side) | Cardinality | Notes |
|---|---|---|---|
| `Wave[wave]` | `depots[wave]` | 1 : * | Wave filters depots, and through them both ticket tables |
| `depots[depot_id]` | `legacy_tickets[depot_id]` | 1 : * | |
| `depots[depot_id]` | `migrated_tickets[depot_id]` | 1 : * | Do **not** also relate `migrated_tickets[wave]` to `Wave`. A second path would make the model ambiguous |
| `Wave[wave]` | `test_cases[wave]` | 1 : * | |
| `Wave[wave]` | `defects[wave]` | 1 : * | |
| `Wave[wave]` | `readiness_criteria[wave]` | 1 : * | |
| `Date[Date]` | `defects[opened_date]` | 1 : * | Active |
| `Date[Date]` | `defects[closed_date]` | 1 : * | **Inactive**. Use it with `USERELATIONSHIP` if you add trend visuals |
| `Date[Date]` | `test_cases[executed_date]` | 1 : * | |
| `Date[Date]` | `legacy_tickets[created_date]` | 1 : * | |

- **No legacy-to-migrated relationship:** the link between `legacy_tickets` and `migrated_tickets` (`ticket_id` = `legacy_ticket_id`) is resolved in DAX with `TREATAS` (Part B2). That avoids a second filter path between `depots` and `migrated_tickets`.
- **`risks` stays unrelated:** it isn't used on these 2 pages.
- **Hide technical columns:** hide the foreign keys on the many side (`depot_id`, `wave` in the fact tables) so report authors use `Wave` and `depots`. In `Wave`, set **Sort by column** of `Wave Label` to `wave`.

## 5. Calculated columns and measures

1. **Calculated columns (Part B).** Select the table, go to **Table tools → New column** and paste each column:
   - `legacy_tickets`: **Is Open**, then **Recon Status**. Recon Status uses the same rule as `sql/01_reconciliation.sql`.
   - `readiness_criteria`: **Target Label** and **Actual Label**.
2. **Measures (Part C).** Open **DAX query view**, paste the whole block from `DEFINE` to the end and click **Update model: Add new measures** in the CodeLens above `DEFINE`. Run the query (F5) and compare the result with the [checklist](#8-expected-values-checklist).
3. **Format strings.** Each measure's comment gives its format (`0.0%`, `#,0`, `0.0`). Set them under **Measure tools → Format**. Also group the measures into display folders: `Testing`, `Defects`, `Migration`, `Readiness`, `Parameters`, `Colors`.

## 6. Page 1: "Release Readiness"

**Canvas:** 16:9, 1280 × 720. Page background comes from the theme. Positions are given as x, y, width, height in pixels.

| # | Visual | Position | Fields | Filters | Formatting |
|---|---|---|---|---|---|
| 1 | **Text box** (title) | 16, 8, 800, 56 | "Release Readiness: Meraki Service Migration". Second line: the `[Snapshot Label]` measure (Insert → Text box → **+ Value**) | none | Title 20 pt Segoe UI Semibold, navy. Subtitle 10 pt grey |
| 2 | **Text box** (disclaimer) | 830, 8, 434, 56 | "Simulated project. Meraki Industries and all data are fictional. Not affiliated with Cisco Meraki." | none | 8 pt italic grey, right-aligned |
| 3 | **Card** ×4 (Wave 3 KPIs) | Row at y 72, height 100. x = 16, 334, 652, 970, each 294 wide | `[Readiness Score]`, `[UAT Pass Rate]`, `[Open S1 Defects]`, `[Gates Failed]` | Visual-level filter `Wave[wave]` = 3 on each card | Title "Wave 3 · …". Callout value color fx → Field value: `[Go/No-Go Color]`, `[UAT Pass Rate Color]`, `[S1 Color]`, `[Go/No-Go Color]` |
| 4 | **Clustered column chart**: Readiness score by wave | 16, 184, 410, 260 | X axis: `Wave[Wave Label]`. Y axis: `[Readiness Score]`. Tooltips: `[Criteria Met]`, `[Gates Failed]` | none | Y axis 0–100. **Constant line** at 90, dashed, labeled "GO threshold (90)". Columns fx → Field value `[Go/No-Go Color]`. Data labels `0.0` |
| 5 | **Table**: GO/NO-GO status per wave | 438, 184, 826, 260 | `Wave[Wave Label]`, `[Wave Phase]`, `Wave[planned_cutover_date]`, `Wave[actual_cutover_date]`, `[Readiness Score]`, `[Gates Failed]`, `[Go/No-Go]` | none | Rename columns (Wave, Phase, Planned cutover, Actual cutover, Score, Gates failed, Decision). Conditional formatting: **Decision** background fx → Field value `[Go/No-Go Color]` with white bold font. **Phase** font color fx → `[Wave Phase Color]`. **Gates failed** shown as icons (0 = green check, >0 = red X). Totals off |
| 6 | **Clustered column chart**: UAT pass rate vs 95% target | 16, 456, 410, 248 | X axis: `Wave[Wave Label]`. Y axis: `[UAT Pass Rate]`. Tooltips: `[Tests Executed]`, `[Execution %]`, `[Tests Blocked]`, `[Tests Not Run]` | none (Wave 4 is blank: UAT not started) | Y axis 80%–100%. **Constant line** at 0.95, dashed red, labeled "Target 95%". Columns fx → `[UAT Pass Rate Color]`. Data labels `0.0%`. Turn on **Show items with no data** on the X axis so Wave 4 stays visible |
| 7 | **Stacked column chart**: Open S1/S2 defects | 438, 456, 400, 248 | X axis: `Wave[Wave Label]`. Y axis: `[Open Defects]`. Legend: `defects[severity]`. Tooltips: `[Avg Open Defect Age (days)]`, `[Max Open Defect Age (days)]` | Visual filter `defects[severity]` is S1 or S2 | Series colors S1 = `#D64541`, S2 = `#F2A900`. Data labels on. Show items with no data on the X axis. Subtitle "Open = not Closed or Deferred" |
| 8 | **Table**: Failed gate criteria, Wave 3 | 850, 456, 414, 248 | `readiness_criteria[criterion_id]`, `[criterion]`, `[gate]`, `[Target Label]`, `[Actual Label]`, `[score]`, `[Points Lost]` | Visual filters `readiness_criteria[wave]` = 3 **and** `readiness_criteria[met]` = "N" | Sort by Points Lost, descending. **Points Lost** data bars in red. **gate** = "Y" shown with a red flag icon. Rename to Gate, Target, Actual, Score, Points lost. Title "Why Wave 3 is NO-GO" |

**Interactions:** with visual 4 selected, go to **Format → Edit interactions** and set visual 5 to *Highlight*. Leave the defaults otherwise.

## 7. Page 2: "Migration Quality"

| # | Visual | Position | Fields | Filters | Formatting |
|---|---|---|---|---|---|
| 1 | **Text box** title and disclaimer | Same as Page 1 | "Migration Quality: Ticket Reconciliation" + `[Snapshot Label]` | none | Same as Page 1 |
| 2 | **Slicer**: Wave | 16, 72, 1248, 48 | `Wave[Wave Label]` | none | Style **Tile**, multi-select with Ctrl. "Select all" on. No header |
| 3 | **Card** ×4 | Row at y 128, height 96. x = 16, 334, 652, 970, each 294 wide | `[Legacy Tickets In Scope]`, `[Migrated Tickets]`, `[Reconciliation %]`, `[Open Tickets Lost]` | none (they follow the slicer) | Values `#,0`, `0.0%`, `#,0`. **Reconciliation %** color fx → `[Reconciliation Color]`. **Open Tickets Lost** color fx → `[Open Tickets Lost Color]`. Reference label under Reconciliation %: "Target 99.5%" |
| 4 | **Clustered column chart**: Legacy vs migrated tickets | 16, 236, 620, 230 | X axis: `Wave[Wave Label]`. Y axis: `[Legacy Tickets]`, `[Migrated Tickets]`. Tooltips: `[Duplicate Rows]`, `[Migrated Rows]` | none | Legacy = navy `#13294B`, Migrated = teal `#0E8C8C`. Data labels `#,0`. Subtitle "Wave 4 not migrated yet" |
| 5 | **Clustered column chart**: Reconciliation % vs 99.5% threshold | 648, 236, 616, 230 | X axis: `Wave[Wave Label]`. Y axis: `[Reconciliation %]`. Tooltips: `[Discrepancies]`, `[Reconciled Tickets]` | `[Reconciliation %]` is not blank (hides Wave 4) | **Y axis 97%–100%**, so the gap is visible. Add the subtitle "Axis starts at 97%". **Constant line** at 0.995, dashed red, labeled "Threshold 99.5%". Columns fx → `[Reconciliation Color]`. Data labels `0.0%` |
| 6 | **Stacked bar chart**: Discrepancies by type | 16, 478, 620, 226 | Y axis: `'Discrepancy Type'[Type]`. X axis: `[Discrepancy Count]`. Legend: `Wave[Wave Label]` | `Wave[wave]` is 1, 2 or 3 | Sort the axis by `Type` (uses `Sort`). Wave colors: navy, light blue, amber for Wave 3. Data labels on. Subtitle "Duplicate loads are extra rows. They do not lower reconciliation %" |
| 7 | **Table**: Open tickets lost | 648, 478, 616, 226 | `legacy_tickets[ticket_id]`, `depots[depot_name]`, `legacy_tickets[status]`, `legacy_tickets[priority]`, `legacy_tickets[created_date]`, `legacy_tickets[customer_id]` | `legacy_tickets[Recon Status]` = "Missing" **and** `legacy_tickets[Is Open]` = True | Title "Open tickets lost: must be re-loaded before cutover (DEF-100, MSM-52)". Red left border via conditional formatting on `ticket_id`. Sort by priority |

**Optional drill-through:** add a hidden page with `legacy_tickets` details and the drill-through field `legacy_tickets[Recon Status]`, so users can right-click a bar in visual 6 to see the tickets behind it.

## 8. Expected values (checklist)

These numbers come from `sql/01`–`05` against `data/meraki.db`. Your report should show the same values.

| Measure | Wave 1 | Wave 2 | Wave 3 | Wave 4 |
|---|---|---|---|---|
| Wave Phase | Live | Live | In UAT | In configuration |
| Readiness Score | 100.0 | 100.0 | **68.5** | 10.8 |
| Gates Failed | 0 | 0 | **4** | 4 |
| Go/No-Go | GO | GO | **NO-GO** | NO-GO |
| UAT Pass Rate | 97.0% | 96.5% | **91.1%** | (blank) |
| SIT Pass Rate | 96.7% | 95.8% | 95.8% | 78.6% |
| Open S1 / S2 Defects (Nov 13) | 0 / 0 | 0 / 0 | **2 / 2** | 1 / 3 |
| Legacy Tickets | 2,602 | 2,578 | 3,610 | 3,214 |
| Migrated Tickets (distinct) | 2,600 | 2,574 | 3,589 | (blank) |
| Reconciliation % | 99.8% | 99.6% | **98.7%** | (blank) |
| Missing / Status mismatch / Missing dates | 2 / 2 / 1 | 4 / 3 / 3 | 21 / 16 / 10 | (blank) |
| Duplicate Rows | 0 | 2 | 7 | (blank) |
| Open Tickets Lost | 0 | 0 | **4** | (blank) |

- **Totals with no wave filter:** 12,004 legacy tickets, of which 8,790 are in scope.
- **Lost tickets table:** the 4 open tickets lost are LT-011529, LT-011684, LT-011854 and LT-011902.
- **Failed gates table for Wave 3:** C03 open S1 defects, C06 open tickets lost, C05 reconciliation and C01 UAT pass rate. They cost 12.0, 10.0, 4.8 and 4.7 points.

## 9. Publish

1. Save the `.pbix` in `powerbi/`.
2. Export each page as an image (**File → Export → PDF**, or a screenshot) into `img/`, for example `img/pbi-release-readiness.png` and `img/pbi-migration-quality.png`, so the dashboard shows on GitHub.
3. Optionally, publish to the Power BI Service. If you do, don't publish to web publicly unless the disclaimer stays visible on every page.
