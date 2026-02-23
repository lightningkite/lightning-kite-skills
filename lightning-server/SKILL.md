---
name: Lightning Server Development
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
