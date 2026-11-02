---
name: estimation
description: This skill should be used when estimating a project using KiteUI and Lightning Server.
version: 2.0.0
---

Start by reading the skills for KiteUI and Lightning Server to get a foundation for what tech we use - lots of things that are slow for other dev shops are quite fast for us.

Stray notes about them:

- Deployment is trivial on AWS; terraform is automatically generated from server definitions. Client-hosted or on-prem deployments don't get this for free, so estimate them.
- ModelRestEndpoints combined with ModelCache on the frontend makes defining general REST access completely trivial
- Integrations are usually highly accelerated with agentic development, given they are mostly looking up information
- KiteUI makes theming and styling basically free and changable late in the process
- We design for mobile screen sizes up front to make sure that we don't have to worry about shrinking screens later
- Auth is pre-built
- Print CSS styling is easy to do in KiteUI

## Method

- List all of the:
  - Models (implied to be using ModelRestEndpoints)
  - Custom Endpoints (odd endpoints that absolutely can't fit REST + signals)
  - External Integrations
  - Screens
  - Complex frontend components
  - Cross-app requirements the client demands (accessibility, load testing, security audits, compliance docs)
- Estimate each item in "hackathon hours" - how long would it take to make a hackathon-worthy version?
- Hackathon hours × 4 = actual dev hours
  - First iteration is the hackathon, second is the polish, third and fourth are the feedback and QA
- Our standard shop rate is $150/hour

## Output

Write the estimate as a JSON file named `<project>-estimate.json`, then render it with the script in this skill's directory:

```bash
python3 ~/.claude/skills/estimation/generate_estimate.py <project>-estimate.json                 # -> <project>-estimate.md
python3 ~/.claude/skills/estimation/generate_estimate.py <project>-estimate.json --format xlsx   # -> <project>-estimate.xlsx, needs openpyxl
```

Never hand-edit the Markdown; change the JSON and re-render. Dev hours, costs, subtotals, and all totals are calculated by the script, so the JSON only holds hackathon hours. The script rejects unknown keys, so a typo fails loudly instead of silently dropping out of the totals.

### JSON format

```json
{
  "title": "Acme Portal Estimate",
  "metadata": [
    {"label": "Client", "value": "Acme Corp (RFP #123)"},
    {"label": "Prepared", "value": "2026-09-29"}
  ],
  "rate": 150,
  "hackathon_multiplier": 4,
  "sections": [
    {
      "title": "Core Platform",
      "description": "Optional paragraph under the heading.",
      "groups": [
        {
          "title": "Server",
          "items": [
            {"item": "Users: User model & roles", "hackathon_hours": 1, "justification": "Auth is pre-built."}
          ]
        },
        {
          "title": "Reporting",
          "summary_title": "Reporting Add-On",
          "optional": true,
          "items": [
            {"item": "Reports: Monthly PDF export", "hackathon_hours": 3, "justification": ""}
          ]
        }
      ]
    },
    {
      "title": "Spanish Support",
      "optional": true,
      "items": [
        {"item": "Translated UI strings", "hackathon_hours": 2, "justification": ""}
      ]
    }
  ],
  "assumptions": ["Client provides API sandbox access."],
  "not_included": ["Hosting costs."],
  "challenges": ["**Legacy API:** No documentation exists."],
  "open_questions": ["Is SSO required at launch?"]
}
```

- **Top level:** `title` and `sections` are required. `rate` defaults to 150 and `hackathon_multiplier` to 4. `metadata` rows appear under the title. Each of the four note lists becomes a bulleted section at the end, and each may be omitted.
- **Sections** hold either `items` directly or `groups` of items, never both. Each group is one row in the summary table, labelled `Section (Group)` unless it sets `summary_title`.
- **Items:** `item` and `hackathon_hours` are required and `justification` is optional. Prefix item names with their area (`Users:`, `Admin:`, `Genesys:`) so long tables stay scannable. Keep justifications to one short sentence, and leave them empty when the item is obvious.
- **Optional scope:** `"optional": true` on a section or group leaves it out of the base total. It is priced on its own in an Optional Features table, which also shows base plus that option. Groups inherit `optional` from their section and can override it with `"optional": false`.
- **Structure:** a typical project has one section per phase, with groups for Server, Integrations, and each frontend app, plus a Cross-App Requirements group. Put each budgetary option the client asked about in its own optional group so it gets its own summary row.
