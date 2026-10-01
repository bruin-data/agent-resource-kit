# Tools

Sample scripts and CLIs an agent can shell out to, each paired with a skill that
tells the agent how to use it.

**Read the code before you run it.** Everything here holds to a higher bar than
the rest of the catalogue, because this is the only place that ships code you
will execute:

- **Credentials come from environment variables only.** Never a command
  argument, never a file in the repository, never printed or logged.
- **Read-only by default.** Anything that writes, updates or deletes requires an
  explicit confirmation flag and prints what it will change first.
- **Standalone.** No imports from the repository they were ported out of.
- **A README aimed at a human**, covering setup, credentials, configuration and
  limitations, alongside the `SKILL.md` aimed at an agent.

| Resource | Risk | Use it when |
|---|---|---|
| [`attio-cli`](attio-cli/) | approval-required | Reading or updating records, lists and attributes in an Attio CRM |
| [`blog-image-generator`](blog-image-generator/) | approval-required | Finding a licence-friendly Unsplash photo and cropping, treating and crediting it as a cover image |
| [`linkedin-enrichment`](linkedin-enrichment/) | approval-required | Pulling public LinkedIn company, person, post or job data through paid Apify actors |

## Third-party services

These wrap third-party products. You need your own account and your own
credentials, and their pricing, rate limits and terms are between you and them.
Nothing here is an endorsement, and none of it is maintained by the vendor.
