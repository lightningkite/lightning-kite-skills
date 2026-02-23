# Endpoint Patterns

## ServerBuilder Pattern

All Lightning Server applications use the `ServerBuilder` pattern:

```kotlin
object MyServer : ServerBuilder() {
    // Settings
    val database = setting("database", Database.Settings())
    val cache = setting("cache", Cache.Settings())

    // Endpoints
    val hello = path.get bind HttpHandler {
        HttpResponse.plainText("Hello World!")
    }
}
```

## Basic Endpoint Definition

Endpoints use a fluent path-building syntax:

```kotlin
// Simple GET
val root = path.get bind HttpHandler { /* ... */ }

// With path parameter
val getUser = path.path("users").arg<String>("id").get bind HttpHandler { request ->
    val id = request.path.arg1  // Type-safe access
    // ...
}

// Multiple arguments
val getUserPost = path.path("users").arg<String>("userId")
    .path("posts").arg<Int>("postId").get bind HttpHandler { request ->
    val userId = request.path.arg1  // String
    val postId = request.path.arg2  // Int
    // ...
}
```

## Typed Endpoints with ApiHttpHandler

Use `ApiHttpHandler` for typed endpoints with auto-documentation and SDK generation:

```kotlin
// Simple POST endpoint
val createPost = path.path("posts").post bind ApiHttpHandler(
    summary = "Create a blog post",
    auth = UserAuth.require(),
    implementation = { input: CreatePostRequest ->
        val post = Post(
            title = input.title,
            content = input.content,
            author = auth.id
        )
        database().table<Post>().insertOne(post)!!
    }
)

// Simple GET endpoint with no input
val stats = path.path("stats").get bind ApiHttpHandler(
    summary = "Get statistics",
    auth = UserAuth.require() or AuthRequirement.None,
    implementation = { _: Unit ->
        StatsResponse(
            userCount = database().table<User>().count(),
            postCount = database().table<Post>().count()
        )
    }
)

// Custom endpoint on ModelRestEndpoints detail path
val unlockDoor = rest.detailPath.path("unlock").post bind ApiHttpHandler(
    summary = "Unlock Door",
    description = "Unlocks the door for an active reservation",
    auth = UserAuth.require(),
    implementation = { _: Unit ->
        // Access path parameters from parent paths
        val reservationId = request.arg1  // From rest.detailPath

        // Implementation is automatically suspend - can call suspend functions directly
        val reservation = info.table().get(reservationId)
            ?: throw BadRequestException("Not found")

        // Validate state
        if (reservation.checkedInAt == null) {
            throw BadRequestException("Not checked in")
        }

        // Call suspend functions directly
        unifiClient.unlockDoor(reservation.lockId, durationSeconds = 60)

        Unit
    }
)

// With path parameter and input
val updateSettings = path.path("settings").arg<String>("key").post bind ApiHttpHandler(
    summary = "Update Setting",
    auth = UserAuth.require(),
    implementation = { newValue: String ->
        val settingKey = request.arg1  // Type-safe access to path arg
        settingsService.update(settingKey, newValue)
    }
)
```

**Key ApiHttpHandler features:**
- Implementation block is **automatically suspend** - no need to wrap in `runBlocking` or `coroutineScope`
- Access path parameters via `request.arg1`, `request.arg2`, etc. (type-safe based on `.arg<T>()` definitions)
- Input type is the type parameter (`{ input: InputType -> ... }`)
- Return value becomes the response body
- Can call suspend functions directly (database queries, external API calls, etc.)

## File Handling

```kotlin
val files = setting("files", PublicFileSystem.Settings())

// Upload (early binding)
val uploadEarly = path.path("upload") module
    UploadEarlyEndpoint(files, database, Runtime.Constant(listOf()))

// Get signed URL
val getFile = path.path("files").arg<String>("path").get bind HttpHandler {
    val filePath = it.arg1
    val fileRef = files().root.then(filePath)
    HttpResponse.plainText(fileRef.signedUrl)
}
```

## WebSockets

```kotlin
val topic = path.path("topic").topic(Message.serializer())

val socket = path.path("ws") bind WebSocketHandler(
    willConnect = { Uuid.random().toString() },
    didConnect = {
        subscribe(topic)
        send(WelcomeMessage())
    },
    messageFromClient = {
        topic.send(Message(currentState, it.content))
    },
    topicHandlers = {
        topic bind { send(it.value) }
    },
    disconnect = {
        println("Disconnected: $currentState")
    }
)
```

## Background Tasks

```kotlin
// Define task
val emailTask = path.path("tasks").path("email") bind Task { input: EmailRequest ->
    println("Sending email to ${input.to}")
    delay(1000)
    email().send(Email(subject = input.subject, to = listOf(EmailAddressWithName(input.to)),
                       plainText = input.body))
}

// Invoke task
val sendEmail = path.path("send-email").post bind HttpHandler { request ->
    emailTask.invoke(EmailRequest(request.body!!.text()))
    HttpResponse.plainText("Email queued")
}

// Scheduled task
val cleanup = path.path("scheduled-cleanup") bind ScheduledTask(
    frequency = 1.hours
) {
    println("Running cleanup...")
    database().table<OldData>().deleteMany(condition {
        it.createdAt lt Clock.System.now() - 30.days
    })
}

// Tentative reservation expiration pattern
val expireStaleReservations = path.path("scheduled").path("expire-reservations") bind ScheduledTask(
    frequency = 1.minutes
) {
    val now = Clock.System.now()
    val expiredCount = ReservationEndpoints.info.table().updateMany(
        condition {
            // Find tentative (has expireAt) reservations that have expired
            it.expireAt.notNull and
            (it.expireAt lt now) and
            it.cancelledAt.eq(null)
        },
        modification {
            it.cancelledAt assign now  // Mark as cancelled
        }
    )
    if (expiredCount > 0) {
        println("Expired $expiredCount stale tentative reservations")
    }
}
```

## Caching

```kotlin
val cache = setting("cache", Cache.Settings())

// Set with expiration
cache().set("key", "value", expire = 5.minutes)

// Get
val value = cache().get<String>("key")

// Remove
cache().remove("key")

// Cache-aside pattern
suspend fun getExpensiveData(id: String): Data {
    val cached = cache().get<Data>("data:$id")
    if (cached != null) return cached

    val fresh = database().table<Data>().get(id)
    cache().set("data:$id", fresh, expire = 10.minutes)
    return fresh
}
```

## Organizing Endpoints

Group related endpoints into ServerBuilder objects:

```kotlin
object ApiEndpoints : ServerBuilder() {
    val posts = path.path("posts") include PostsEndpoints
    val comments = path.path("comments") include CommentsEndpoints
}

object Server : ServerBuilder() {
    val api = path.path("api") include ApiEndpoints
}
```

## Error Handling

Use standard exceptions:

```kotlin
throw BadRequestException("Invalid input")
throw NotFoundException("Resource not found")
throw UnauthorizedException("Auth required")
throw ForbiddenException("Access denied")
```

## Accessing Services

Services are accessed through settings:

```kotlin
object Server : ServerBuilder() {
    val database = setting("database", Database.Settings())

    val endpoint = path.get bind HttpHandler {
        val db = database()
        // Use db...
    }
}
```

## MetaEndpoints

<!-- by Claude -->
Always include `MetaEndpoints` in your server for health checks, bulk API, and OpenAPI documentation:

```kotlin
import com.lightningkite.lightningserver.typed.MetaEndpoints

object Server : ServerBuilder() {
    val database = setting("database", Database.Settings())
    val cache = setting("cache", Cache.Settings())

    // ... other endpoints ...

    // MetaEndpoints provides:
    // - GET /meta/online - simple health check (returns 200 if healthy)
    // - GET /meta/health - detailed health with memory, CPU, service status
    // - Bulk API endpoints for efficient batch operations
    // - OpenAPI documentation
    val meta = path.path("meta") module MetaEndpoints(
        "com.yourcompany.yourproject",  // package name for schema generation
        database,
        cache
    )
}
```

**Why this matters:**
- Without MetaEndpoints, the **bulk API is not available** (clients can't batch multiple requests)
- Health endpoints are essential for load balancers and monitoring
- OpenAPI documentation is generated from this
- Package name parameter is used for schema generation

## Path Reference Pattern

Always store endpoint references for testing and internal calls:

```kotlin
object Server : ServerBuilder() {
    val createPost = path.path("posts").post bind ApiHttpHandler { ... }
    val getPost = path.path("posts").arg<Uuid>("id").get bind ApiHttpHandler { ... }

    // Can reference: Server.createPost, Server.getPost
}
```
