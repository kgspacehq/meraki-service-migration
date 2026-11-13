# Project Charter — Meraki Service Migration & Release Readiness

> Simulated project. Meraki Industries and all data are fictional. Not affiliated with Cisco Meraki.

| | |
|---|---|
| **Program** | Meraki Modernization Program — Wave 1 (see [Company Profile](00-company-profile.md)) |
| **Sponsor** | Daniel Ortiz, VP of Field Operations |
| **Project Manager** | Keren |
| **Charter date** | June 15, 2026 |
| **Timeline** | July – December 2026 (depot migrations September – December 2026) |
| **Budget** | USD 1.2M |

## Business case
Meraki's 40 US service depots run on an on-premise ticketing system that the vendor no longer supports, which is both an operational and a security risk. Data capture is weak: 18% of service orders are closed with incomplete data, which delays billing and makes asset history unreliable. Moving to a cloud field-service platform removes the end-of-support risk, enforces data completeness at the point of capture, and lays the service-data foundation for the SAP S/4HANA Cloud ERP replacement (Program Wave 2).

## Objectives
1. Migrate all 40 depots to the cloud field-service platform by December 18, 2026.
2. Carry every open ticket and the last 3 years of service history over with no loss.
3. Cut service orders with incomplete data from 18% to under 5% within 90 days of the final wave.
4. Decommission the legacy ticketing system by January 31, 2027.

## Scope
| In scope | Out of scope |
|---|---|
| Platform configuration: work orders, dispatch, mobile app, SLAs | ERP replacement (Program Wave 2) |
| Migration of open tickets, 3 years of history, customer and asset master data | Archive data older than 3 years (kept read-only) |
| Integrations with the legacy ERP (billing, parts) and identity provider (SSO) | Changes to manufacturing plant systems |
| UAT, training, cutover and 4 weeks of hypercare per wave | New service offerings or pricing changes |
| Legacy system decommissioning | Hardware refresh of technician devices |

## Milestones
| Milestone | Scope | Target date |
|---|---|---|
| M0 — Charter approved | — | Jun 15, 2026 |
| M1 — Platform build complete, pilot UAT passed | Core configuration and integrations | Aug 28, 2026 |
| **Migration Wave 1** | Depots 1–10 (Southeast) | Sep 25, 2026 |
| **Migration Wave 2** | Depots 11–20 (Northeast) | Oct 23, 2026 |
| **Migration Wave 3** | Depots 21–30 (Midwest) | Nov 20, 2026 |
| **Migration Wave 4** | Depots 31–40 (West) | Dec 18, 2026 |
| M6 — Legacy system decommissioned, project closed | — | Jan 31, 2027 |

## Delivery approach
The project uses a **hybrid** approach:
- **Predictive** for the 4 migration waves and cutover: fixed dates, go/no-go gates, cutover runbooks and rollback plans.
- **Scrum** (2-week sprints) for platform configuration, integrations and testing. The backlog is managed in Jira, and each wave's scope is frozen 2 sprints before its cutover.

## Success metrics
| Metric | Target |
|---|---|
| Open tickets lost in migration | **0** |
| Service downtime per depot during cutover | **< 4 hours** |
| UAT pass rate before each wave | **≥ 95%** |

## Key assumptions
- The platform vendor provides a dedicated implementation team from July through hypercare.
- Depot managers release 2 key users per depot for UAT and train-the-trainer sessions.
- The legacy ERP's billing and parts interfaces stay stable until Program Wave 2.
- Legacy ticketing data can be extracted through database access, without vendor support.

## Constraints
- Budget is capped at USD 1.2M, including the vendor's services and a 10% contingency.
- Cutovers happen on weekends only. No cutovers during the Thanksgiving week or after December 18.
- No more than 10 depots per wave.
- Security must approve SSO, data residency and access controls before Migration Wave 1.

## High-level risks
| Risk | Impact | Response |
|---|---|---|
| Poor legacy data quality slows migration | High | Data profiling and cleansing sprints before each wave, with depot-level data owners |
| Integration with the legacy ERP fails at cutover | High | End-to-end integration tests in each sprint, and a rehearsal before each wave |
| Technicians resist the new mobile app | Medium | Super-users in each depot, hands-on training, and floor support in hypercare |
| Vendor resourcing gaps | Medium | Named resources in the SOW, with an escalation path to the vendor account lead |
| Wave 4 overlaps the holiday period | Medium | Fixed Dec 18 deadline and 1 week of schedule buffer held in Wave 3 |

## Approval
| Role | Name | Signature | Date |
|---|---|---|---|
| Sponsor — VP of Field Operations | Daniel Ortiz | | |
| Project Manager | Keren | | |
| IT Director | Priya Raman | | |
