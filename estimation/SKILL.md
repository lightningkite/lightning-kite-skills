---
name: estimation
description: This skill should be used when estimating a project using KiteUI and Lightning Server.
version: 1.0.0
---

Start by reading the skills for KiteUI and Lightning Server to get a foundation for what tech we use - lots of things that are slow for other dev shops are quite fast for us.

Stray notes about them:

- Deployment is trivial; terraform is automatically generated from server definitions
- ModelRestEndpoints combined with ModelCache on the frontend makes defining general REST access completely trivial
- Integrations are usually highly accelerated with agentic development, given they are mostly looking up information
- KiteUI makes theming and styling basically free and changable late in the process
- We design for mobile screen sizes up front to make sure that we don't have to worry about shrinking screens later
- Auth is pre-built
- Print CSS styling is easy to do in KiteUI

We at Lightning Kite estimate using this technique:

- List all of the:
  - Models (implied to be using ModelRestEndpoints)
  - Custom Endpoints (odd endpoints that absolutely can't fit REST + signals)
  - External Integrations
  - Screens
  - Complex frontend components
- Estimate each of the above items in "hackathon hours" - how long would it take to make a hackathon-worthy version?
- Multiply hackathon hours by 4 to get an estimate of actual dev hours
  - First iteration is the hackathon, second is the polish, third and fourth are the feedback and QA
- Our standard shop rate is $150/hour

Estimates should be output as a CSV with the columns "category", "item", "hackathon_hours", "justification" (why that many hours, keep this very succinct), "dev_hours" (calculated), and "cost" (calculated).

