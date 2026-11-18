---
name: lightning-server
description: IMPORTANT - Read this skill proactively when working on any file that imports from com.lightningkite.lightningserver. This skill covers Lightning Server framework, Kotlin server development, building APIs, database operations, authentication, and testing patterns.
version: 2.0.0
---

# Lightning Server

Kotlin framework for HTTP/WebSocket backends: one `ServerBuilder` object declares endpoints, settings (database,
cache, files, email), auth, tasks and schedules; the framework serves it, generates OpenAPI and client SDKs, runs
tests in memory, and writes the AWS Terraform.

## Where the truth lives

Source: `~/Projects/lightning-server` (read it instead of guessing).  The guide is `docs-guide/guide/*.md`; every
Kotlin block in it is compiled from `docs-guide/src/samples`, so its code is safe to copy.

**Start with `docs-guide/guide/condensed-guide.md`**: one page, every common task (project setup, server, routes,
typed endpoints, models, REST + permissions, queries, auth/login, files, websockets, tasks, cache, testing, running,
AWS deploy, CORS/rate limiting), each linking to its full chapter.  Then the chapter for the task at hand:

| Topic | Chapter |
|---|---|
| Gradle setup, stack catalog, multi-module layout, KSP stanza for shared models | `setup.md`, `project-structure.md` |
| Routing, typed endpoints, errors, validation, serialization | `routing.md`, `typed-endpoints.md`, `error-handling.md`, `validation.md`, `serialization.md` |
| Settings files and secrets | `settings.md`, `services.md` |
| Database, query DSL, signals/interceptors, indexes, upsert, compare-and-swap | `database.md`, `advanced-database.md` |
| Generated CRUD (`ModelRestEndpoints`), routes, JSON condition/modification syntax | `model-rest.md` |
| Permissions, `updateRestrictions`, field masking | `permissions.md` |
| Live queries (`ModelRestUpdatesWebSocket`) | `model-realtime.md` |
| Auth principals, proofs, sessions, OAuth | `auth.md`, `proof-session.md`, `oauth.md` |
| Files/uploads, media, email, notifications | `files.md`, `media.md`, `email.md`, `notifications.md` |
| WebSockets, pub/sub, tasks, schedules, caching | `websockets.md`, `pubsub.md`, `tasks.md`, `schedules.md`, `caching.md` |
| CORS/interceptors, rate limiting, bulk requests, `MetaEndpoints`/admin | `cors-interceptors.md`, `rate-limiting.md`, `bulk-endpoints.md`, `meta-admin.md` |
| Testing | `testing.md` |
| Running, engines, AWS/EC2/VM deploy, Terraform | `running.md`, `engines.md`, `aws-deployment.md`, `deploy-ec2.md`, `deploy-vm.md`, `terraform.md` |
| Client SDKs | `client-sdks.md` |
| Upgrading old code | `appendix/migration-to-epoch-1.md` (also `migration-v4-to-v5.md`, `migration-v5.1-to-v5.2.md`) |

Service Abstractions (database, cache, files, email) has its own docs: see the `service-abstractions` skill.

## Versions and releases

The libraries are on **epoch 1**: every module has its own version, starting at `1000.0.0` (Lightning Server 5.4 on
Service Abstractions 1.4).  Apps take versions from the stack catalog
(`from("com.lightningkite:stack-catalog:<version>")` as `lk`, plus `platform(lk.stack.bom)`); see `setup.md`.
Never run `publishToMavenLocal` by hand: it publishes unreleased code under the last released version.  To try local
changes, `./lk release` in `~/Projects/metawork` (see its README) and point the app's catalog version at `local`.

## REST first

Before writing a custom endpoint, check whether `ModelRestEndpoints` plus hooks covers it:
- validation or forced fields on create: `interceptCreate` in `signals`, or `postPermissionsForUser`
- field rules on update: `updateRestrictions` in `ModelPermissions`
- side effects: `postCreate` / `postChange` / `postDelete` (long work belongs in a `Task`)
- complex reads: let the client combine queries

Custom endpoints are for webhooks, hardware/third-party contracts, and multi-model operations that must not be
eventually consistent.  The hook table is in `advanced-database.md#signals-and-interceptors`.

## Gotchas (verified against source)

- **Routes have no `/rest` segment** unless you mount one.  `path.path("posts") include ModelRestEndpoints(info)`
  gives `GET /posts`, `POST /posts/query`, `GET /posts/{id}`, `POST /posts` (insert), `PUT /posts/{id}` (replace),
  `PATCH /posts/{id}` (modify, body is a `Modification` JSON), `DELETE /posts/{id}`, `/count`, `/bulk...`.
  Property names: `list`, `query`, `detail`, `insert`, `insertBulk`, `replace`, `upsert`, `modify`, `deleteItem`,
  `bulkDelete`, `count`.
- **`ModelRestEndpoints(info) + ModelRestUpdatesWebSocket(info)`** needs
  `import com.lightningkite.lightningserver.typed.ModelRestEndpointsAndUpdatesWebSocket.Companion.plus`.  The result
  exposes `.endpoints.<op>` and `.webSocket`, so tests call `Thing.rest.endpoints.insert.test(...)`.
- **`AuthEndpoints` (and `SessionManager`) register their principal**; don't also `register(UserAuth)`.  Only a
  server without them needs `register(UserAuth)`.
- **Uploads**: mount one `GlobalUploadEndpoints(files, database, Runtime.Constant(listOf()), authOptions = ...)`.
  `UploadEarlyEndpoint` is a deprecated alias.  It installs the contextual `ServerFile` serializer, so include only
  one (or one `FileUploadBasis` with per-feature `UploadEndpoints`; see `files.md`).
- **`MetaEndpoints("com.example", cache)`**: the `(packageName, database, cache)` constructor is deprecated.
- **Settings JSON**: service settings are URL strings: `"database": "mongodb://localhost/app"`, not
  `{"url": ...}` (see the value-format table in `settings.md`).
- **Cache TTL** is `timeToLive =`: `cache.set("k", v, timeToLive = 5.minutes)`.
- **AWS handler**: `class AwsHandler : AwsAdapter(Server.build())`.
- **Time types** are `kotlin.time` (`Instant`, `Clock`, `Duration`); calendar types (`LocalDate`, `DateTimeUnit`,
  `TimeZone`) are `kotlinx.datetime`.  In model files import `kotlin.time.Instant` **by name**, never
  `kotlin.time.*`: KSP-generated files copy your imports and add `kotlinx.datetime.*`, and two star-imported
  `Instant`s break the generated code.
- **Query DSL** is Service Abstractions 1.4: generated fields are optics (`Post.title eq "x"`, no `Post_title` /
  `Post.path`); builders are `Condition<T> { }` / `Modification<T> { }` (lowercase `condition`/`modification` are
  deprecated).  Give `Condition` an explicit type when inference fails.
- **Denormalized fields are empty in `interceptCreate`**: signals wrap outside the denormalizations, which fill
  them in afterwards; fetch the source row yourself.  Denormalization (`modelInfoWithDeno` with
  `ref.denormalizes(info) { x watch ref.y }` / `snapshot`, target fields `@Denormalized`) is not in the guide yet;
  read the KDoc in `typed/src/main/kotlin/.../typed/denormalize/ModelInfoWithDeno.kt`.
- **Signals see writes through the model info only** (`info.table()` / `info.table(auth)` / REST).  Signal
  lambdas run with `ServerRuntime` in context, so cross-table writes from `postCreate`/`postChange` work.
- **Users editing their own row** need `updateRestrictions` (e.g. `it.role.cannotBeModified()`), or they can
  promote themselves.
- **Tests**: `Server.testBlocking(settings = { database set Database.Settings("ram") }) { ... }` builds a fresh
  runtime per test; `UserAuth.testAuth(user)` for auth; runtime work the test does itself goes in `execute { }`.
- Put shared models in a multiplatform `-shared` module rather than duplicating them for clients; that module needs
  the `kspCommonMainKotlinMetadata` stanza from `project-structure.md`.

## Related libraries

**CSV**: `com.lightningkite:kotlinx-serialization-csv-durable` (source `~/Projects/kotlinx-serialization-csv-durable/`)
works on any `@Serializable` type, eager or streaming; use it before hand-rolling CSV.
