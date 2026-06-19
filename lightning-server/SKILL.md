---
name: lightning-server
description: IMPORTANT - Read this skill proactively when working on any file that imports from com.lightningkite.lightningserver. This skill covers Lightning Server framework, Kotlin server development, building APIs, database operations, authentication, and testing patterns.
version: 1.3.0
---

# Lightning Server Development Skill

You are an expert Lightning Server developer. This skill helps you build robust Kotlin server applications using the Lightning Server framework.

**⚠️ IMPORTANT:** Proactively read this skill whenever you open or work on a file that imports from `com.lightningkite.lightningserver.*`. The patterns and lifecycle details here are critical for correct implementation.

## Framework Overview

Lightning Server is a Kotlin-based server framework for building APIs across multiple serverless platforms. It provides:
- Type-safe endpoint definitions with auto-generated documentation
- Database abstractions (MongoDB, Postgres, JSON files)
- Caching abstractions (Redis, Memcached, DynamoDB)
- File storage abstractions (S3, Azure, local)
- Authentication & authorization (email, SMS, OAuth, password, OTP)
- WebSocket support
- Background tasks and scheduled jobs
- Multi-platform SDK generation (TypeScript, Kotlin)
- OpenAPI documentation generation

**Version:** 5.x | **Main Branch:** master

## Key Principles

### REST-First Methodology

**⚠️ Before creating custom endpoints, ask if ModelRestEndpoints can handle it:**

1. **Can REST create + `interceptCreate` handle validation?** - Use for booking validation, conflict detection, subscription restrictions
2. **Can REST modify + `updateRestrictions` handle field rules?** - Use for phase transitions, state changes
3. **Can REST query handle the read?** - Client can compute complex views from multiple queries
4. **Can `postChange` handle side effects?** - Use for cascade updates, notifications

**Custom endpoints are ONLY needed for:**
- Hardware integrations (door unlocks, IoT) - external systems dictate the interface
- External API callbacks (webhooks) - third party dictates the contract
- Truly atomic multi-model operations where eventual consistency isn't acceptable

### ServerBuilder Pattern

```kotlin
object MyServer : ServerBuilder() {
    val database = setting("database", Database.Settings())
    val cache = setting("cache", Cache.Settings())

    val hello = path.get bind HttpHandler {
        HttpResponse.plainText("Hello World!")
    }
}
```

### ModelRestEndpoints for CRUD

**Always use ModelRestEndpoints for CRUD operations:**

```kotlin
@Serializable
@GenerateDataClassPaths
data class Post(
    override val _id: Uuid = Uuid.random(),
    val title: String,
    val authorId: Uuid
) : HasId<Uuid>

val postInfo = database.modelInfo(
    auth = UserAuth.require(),
    permissions = {
        val isOwner = condition { it.authorId eq auth.id }
        ModelPermissions(
            create = Condition.Always,
            read = Condition.Always,
            update = isOwner,
            delete = isOwner
        )
    }
)

val posts = path.path("posts").path("rest") module ModelRestEndpoints(postInfo)
```

This gives you: `GET /posts/rest`, `GET /posts/rest/{id}`, `POST /posts/rest`, `PUT /posts/rest/{id}`, `DELETE /posts/rest/{id}`, `POST /posts/rest/query`

### Lifecycle Hook Decision Tree

**Need to validate before creation?** → Use `interceptCreate`
**Need to validate before update?** → Use `interceptChange`
**Need old value for validation?** → Use `interceptChangePerInstance` (expensive!)
**Need to prevent field modification?** → Use `updateRestrictions` (`.cannotBeModified()` or `.requires(condition) { valueCondition }`)
**Need to trigger side effects?** → Use `postChange`, `postCreate`, or `postRawChanges` (batch)
**Need to clean up after deletion?** → Use `postDelete`

**⚠️ CRITICAL:** Denormalized fields are NOT populated in `interceptCreate` - fetch source data directly!

### Error Handling

```kotlin
throw BadRequestException("Invalid input")
throw NotFoundException("Resource not found")
throw UnauthorizedException("Auth required")
throw ForbiddenException("Access denied")
```

## Detailed Documentation

For in-depth coverage, see these companion documents:

- **[rest-lifecycle.md](rest-lifecycle.md)** - Complete REST operation lifecycles, hook reference, signal composition, common pitfalls
- **[authentication.md](authentication.md)** - PrincipalType, optional auth, auth caching, auto-user creation
- **[database.md](database.md)** - Database operations, modifications, migrations, PATCH syntax
- **[endpoints.md](endpoints.md)** - Endpoint patterns, ApiHttpHandler, WebSockets, background tasks, caching
- **[testing.md](testing.md)** - Test patterns, infrastructure setup, debug tokens, common pitfalls
- **[troubleshooting.md](troubleshooting.md)** - Common errors, imports, anti-patterns, best practices

## Quick Reference

### Common Imports

```kotlin
// Database operations
import com.lightningkite.services.database.condition
import com.lightningkite.services.database.modification
import com.lightningkite.services.database.eq
import com.lightningkite.services.database.lt
import com.lightningkite.services.database.gte

// DateTime (NOT kotlin.time!)
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.Clock

// Flow
import kotlinx.coroutines.flow.toList
```

### REST PATCH Syntax

```bash
# Set a field
PATCH /model/rest/{id}
{"fieldName": {"Assign": "newValue"}}

# Clear optional field
{"expireAt": {"Assign": null}}

# Increment
{"count": {"Increment": 5}}
```

### Typed Endpoints

```kotlin
val createPost = path.path("posts").post bind ApiHttpHandler(
    summary = "Create post",
    auth = UserAuth.require(),
    implementation = { input: CreatePostRequest ->
        database().table<Post>().insertOne(Post(title = input.title))!!
    }
)
```

## Related Lightning Kite Libraries

**CSV serialization** — `com.lightningkite:kotlinx-serialization-csv-durable` (catalog: `libs.csvDurable`). Source: `~/Projects/kotlinx-serialization-csv-durable/`. Multiplatform (JVM/JS/iOS/Android). Reach for this before hand-rolling CSV parse/escape — it works on any `@Serializable` type, with both eager and streaming APIs:

```kotlin
val csv = CsvFormat(StringDeferringConfig(EmptySerializersModule()))
csv.encodeSequenceToAppendable(MyRow.serializer(), rows.asSequence(), writer)  // streaming
val list = csv.decodeFromReader(ListSerializer(MyRow.serializer()), reader)    // eager
```

Field names become column headers; nullable scalars round-trip; nested structures fall back to JSON in a single cell.

## ⚠️ CRITICAL PITFALLS

### ModelRestEndpoints operation names + WebSocket combine FOOTGUN

Quick reference — use these exact names when calling endpoints in tests or referencing them programmatically:

| Operation | Property name | Notes |
|-----------|--------------|-------|
| List/query | `.list` | POST body is `Query<T>` |
| Single item | `.detail` | |
| Insert one | `.insert` | |
| Update (modify) | `.modify` | NOT `.update` — compile error |
| Delete one | `.deleteItem` | NOT `.delete` — compile error |
| Bulk delete | `.bulkDelete` | |
| Insert many | `.insertBulk` | |

#### ⚠️ FOOTGUN: combining with WebSocket moves ops under `.rest.endpoints.<op>`

When you add `ModelRestUpdatesWebsocket` to an endpoint via `+`, the combined type is `ModelRestEndpointsAndUpdatesWebsocket`. **The REST operations are no longer directly on `.rest` — they move under `.rest.endpoints.<op>`.**

**The danger:** both forms compile without error. The wrong form silently targets the wrong object and produces NotFoundException (or no-op) at runtime. No compiler warning. This has cost builders 20+ minutes.

```kotlin
// Endpoint definition:
val rest = path include ModelRestEndpoints(info) + ModelRestUpdatesWebsocket(info)
// ↑ rest is ModelRestEndpointsAndUpdatesWebsocket — ops are under .rest.endpoints.*

// ❌ WRONG — compiles fine, but .rest.<op> is the wrong accessor; throws at runtime
EventEndpoints.rest.insert.test(auth, event)
EventEndpoints.rest.list.test(auth, Query())

// ✅ CORRECT — ops live under .rest.endpoints.<op>
EventEndpoints.rest.endpoints.insert.test(auth, event)
EventEndpoints.rest.endpoints.list.test(auth, Query())
EventEndpoints.rest.endpoints.modify.test(id, auth, modification { ... })
EventEndpoints.rest.endpoints.deleteItem.test(id, auth, Unit)
```

Compare with a **plain `ModelRestEndpoints`** (no WebSocket):
```kotlin
// Endpoint definition:
val rest = path include ModelRestEndpoints(info)
// ↑ rest is ModelRestEndpoints — ops are directly on .rest.*

// ✅ CORRECT for plain ModelRestEndpoints
MessageEndpoints.rest.insert.test(auth, message)
MessageEndpoints.rest.modify.test(id, auth, modification { ... })
MessageEndpoints.rest.deleteItem.test(id, auth, Unit)
```

**Rule of thumb:** look at the endpoint definition. If you see `ModelRestEndpoints(info) + ModelRestUpdatesWebsocket(info)`, every test/programmatic call needs `.rest.endpoints.<op>`. If it's just `ModelRestEndpoints(info)`, use `.rest.<op>` directly.

Verified: EventEndpoints.kt (demo/iter5-events) uses the `+` combine form; testing.md shows both forms in detail.

### `postPermissionsForUser` — receiver context and imports

The `postPermissionsForUser` lambda receiver is `AuthAccess<USER>` (= `Access<*, *, USER>`). Inside it:
- `auth` gives `Authentication<User>` (the authenticated user's token/session)
- `auth.id` gives the user's ID (`User.ID`)
- `auth.fetch()` fetches the full `User` from the database — requires explicit import

```kotlin
import com.lightningkite.lightningserver.auth.fetch  // required for auth.fetch()
import com.lightningkite.lightningserver.auth.id     // required for auth.id

postPermissionsForUser = { table ->
    table.interceptCreate { message ->
        val user = auth.fetch()   // fetches User from database
        message.copy(
            sender = auth.id,
            senderName = user.name,
        )
    }
}
```

Use this to force server-side field values that the client must not control (sender ID, timestamps, etc.).

Verified: MessageEndpoints.kt (demo/iter3-chat).

## Anti-Patterns

❌ Manually create CRUD endpoints (use ModelRestEndpoints)
❌ Multiple UploadEarlyEndpoint instances (serialization conflicts)
❌ Call Server.build() multiple times in tests
❌ Assume denormalized fields exist in interceptCreate
❌ Use `kotlin.time.DateTimeUnit` (use `kotlinx.datetime`)
❌ Forget @GenerateDataClassPaths on models
❌ Allow users to update their own record without `updateRestrictions` — they can escalate `role` fields!
❌ Forget MetaEndpoints — no health checks, no bulk API, no OpenAPI docs
❌ Duplicate models across server/client — use a multiplatform `-shared` module instead

## When to Read This Skill

Invoke this skill proactively when you:
- Open any file with `import com.lightningkite.lightningserver.*`
- Work on Lightning Server endpoints
- Set up authentication
- Work with databases
- Handle file uploads
- Implement WebSockets
- Create background tasks
- Write tests
- Deploy to AWS
- See compilation errors related to Lightning Server
