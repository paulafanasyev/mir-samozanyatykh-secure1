# Multi-agent audit plan

## Roles
- Architecture: repository structure, API contracts, database and migrations.
- Security: authentication, authorization, IDOR, CSRF/CORS, secrets, uploads and webhooks.
- Backend: endpoint validation, errors, transactions, concurrency and tests.
- Frontend: routes, forms, accessibility, responsive UX and error/loading states.
- Svetlana: document workflows, generation, editing and safe AI fallbacks.
- Android: build configuration, permissions, networking, signing and APK installation.
- QA: unit, integration, API, E2E and regression coverage.
- Adversarial reviewer: independently challenges all findings and blocks release on unresolved critical issues.

## Release gate
No APK is considered ready until the project passes security review, tests, build verification and an independent adversarial review.
