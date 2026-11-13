# Jira backlog — space MSM

> Simulated project. Meraki Industries and all data are fictional. Not affiliated with Cisco Meraki.

`msm-backlog.csv` contains 5 epics and 28 stories for the Jira Cloud space **MSM**. Statuses reflect **November 13, 2026**:

- Wave 1–2 work and the core build are **Done**.
- Wave 3 work is **In Progress**.
- Wave 4 work and decommissioning are **To Do**.

## Importing into Jira Cloud

Go to **Settings → System → External system import → CSV**. Choose space MSM and set the **date format to `yyyy-MM-dd`**. Then map the columns:

| CSV column | Jira field |
|---|---|
| Issue Id | Issue Id |
| Parent Id | Parent Id (links each story to its epic) |
| Issue Type, Summary, Description, Priority, Status | Same-name fields |
| Labels (3 columns) | Labels. Jira needs one column per label |
| Story Points | Story Points (or *Story point estimate* in team-managed spaces) |
| Start date, Due date | Start date, Due date (used by the Timeline view) |
| Outward Link (Blocks) | Issue link **Blocks** |

- **Descriptions:** they use Jira wiki markup, and each one includes its acceptance criteria in Given/When/Then form.
- **Wave 3 blockers:** the four stories that caused the NO-GO each "block" story 124, *Wave 3 go/no-go decision and revised cutover plan*. They are the DEF-100 fix, the DEF-112 fix, reconciliation remediation and the UAT re-test. All four also carry the `no-go-blocker` label.
