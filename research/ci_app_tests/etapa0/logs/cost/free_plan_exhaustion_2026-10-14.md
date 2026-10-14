# CircleCI Free plan: what happens when credits run out (read 2026-10-14)

## Official docs — https://circleci.com/docs/guides/plans-pricing/credits/
(as returned by WebFetch; quotes)

* "When your available credits reach 0, personal builds are blocked until your
  credits refill at the start of the next month."
* "Open source builds are not subject to this block and continue to run even if
  your credit balance is exhausted."
* "Organizations on the Free Plan receive 30,000 credits per month for personal
  (non-open source) usage."
* "Organizations on our Free Plan can use up to 400,000 credits per month, for
  free, for Linux open source builds."
* "Using our Free Plan and keeping your repository public will enable this for you."

## Pricing page — https://circleci.com/pricing/
* Free plan Docker x86: Small, Medium, Medium+, Large = "Yes"; X-large and above "—".
* "Credits on the Free plan expire after a month and do not roll over."

## Support article (CONFLICTS with the docs) —
https://support.circleci.com/en/articles/15091234-upgrade-your-plan-to-unblock-build
* "Free Plan credits are allocated on a weekly basis and do not roll over."
* "Once your weekly credit allotment is exhausted, builds will be blocked until
  credits renew."

## This repository
`https://api.github.com/repos/daniloceano/CycloPhaser` → `private: false`,
`visibility: public` (2026-10-14). The CircleCI jobs run on Linux Docker.
Per the official docs above, these builds would count as open source builds
(400 000/month, not blocked at 0). Whether that allowance actually applies
cannot be confirmed in the web app (next section).

## Open source allowance is not visible (re-read 2026-10-14)
Same official page, "Open source credit usage": "Using our Free Plan and keeping
your repository public will enable this for you. Open source credit availability
and limits are not visible in the CircleCI web app." FAQ "Are there credit plans
for open source projects?": "Open source credit availability and limits will not
be visible in the UI."
