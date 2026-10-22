---
name: service-abstractions
description: This skill should be used when the user asks about Service Abstractions library, infrastructure service management, or database/cache/file system configurations in Kotlin
version: 1.0.0
---

# Service Abstractions Skill

This skill provides expertise in using the Service Abstractions Kotlin Multiplatform library for infrastructure service management.

## When to Use This Skill

Invoke this skill when working with:
- Service Abstractions library code
- Database, cache, file system, or other infrastructure service configurations
- Type-safe database queries using generated fields (optics)
- Settings-based service instantiation
- Multiplatform Kotlin projects using service abstractions

## Core Concepts

### Settings Pattern

Service Abstractions uses a settings-based configuration where services are instantiated from serializable configuration objects:

```kotlin
@Serializable
data class ServerSettings(
    val database: Database.Settings = Database.Settings("mongodb://localhost"),
    val cache: Cache.Settings = Cache.Settings("redis://localhost:6379"),
    val files: PublicFileSystem.Settings = PublicFileSystem.Settings("s3://bucket/path")
)

// Instantiate services with a context
val context = SettingContext(
    internalSerializersModule = module,
    otel = otel,
    // ... other shared resources
)

val db = settings.database("main-db", context)
val cache = settings.cache("app-cache", context)
val files = settings.files("uploads", context)
```

### Service Interface

All services implement the `Service` interface:

```kotlin
interface Service {
    val name: String
    val context: SettingContext
    suspend fun connect()
    suspend fun disconnect()  // Critical for serverless (Lambda, SnapStart)
    val healthCheckFrequency: Duration
    suspend fun healthCheck(): HealthStatus
}
```

**Important**: Always call `connect()` after instantiation and `disconnect()` when done, especially in serverless environments.

### URL-Based Configuration

Services are configured using URL schemes:

**In-Memory/Testing:**
- `ram://` or `ram` - In-memory implementation

**Databases:**
- `mongodb://host:port/database`
- `postgresql://host:port/database`
- `jsonfile://path/to/file.json`

**Caches:**
- `redis://host:port`
- `memcached://host:port`
- `dynamodb://region/table-name`

**File Systems:**
- `file://path/to/directory`
- `s3://bucket-name/prefix`

**Testing Suffix:**
- URLs ending in `-test` (e.g., `mongodb-test://`) start ephemeral instances for testing

## Database Usage

### Defining Models

```kotlin
@Queryable  // = @Serializable + generated field paths
data class User(
    override val _id: Uuid = Uuid.random(),
    @Index(unique = IndexUniqueness.Unique) val email: String,
    @Index val age: Int,
    val name: String,
    val nickname: String? = null,
    val address: Address? = null,
    val friends: List<Uuid> = listOf(),
) : HasId<Uuid>

@Queryable
data class Address(val city: String, val zip: String)
```

**Key Annotations:**
- `@Queryable` - Applies `@Serializable` and generates a typed field for every property (replaces `@Serializable @GenerateDataClassPaths`)
- `@Index` - Creates a database index (`unique = IndexUniqueness.Unique` for unique indexes)
- Model must implement `HasId<T>` with an `_id` field

### Generated Fields (Optics)

KSP generates one field per property on the companion: `User.email` is a `Field<User, String>`. Fields **are paths** — use them directly in conditions, modifications, and sorts, and chain them to reach nested values:

```kotlin
User.age                     // Field<User, Int>  (a Lens)
User.address.notNull.city    // Optic<User, String>
Lens<User>()                 // the whole User, when an API needs a root path
```

The path types live in `com.lightningkite.services.database.optics` (`Optic`, `Lens`, `Field`, `notNull`, `elements`, `asType`, ...), so import it alongside `com.lightningkite.services.database.*`.

- A **`Lens`** always reaches its target (`get` returns `B`). Fields, and fields composed with fields, are lenses.
- An **`Optic`** may not (`get` returns `B?`). `notNull`, `asType(...)`, and `elements` produce optics.

Run KSP after changing models:

```bash
./gradlew :your-module:kspCommonMainKotlinMetadata
```

### Getting a Table

```kotlin
val db: Database = settings.database("my-db", context)
db.connect()

val userTable: Table<User> = db.table<User>()          // named after the class
val userTable2: Table<User> = db.table<User>("users")  // explicit name
```

### CRUD Operations

```kotlin
// Insert
userTable.insertOne(user)
userTable.insert(listOf(user1, user2))

// Find
val adults = userTable.find(User.age gte 18).toList()
val john = userTable.get(userId)
val byEmail = userTable.findOne(User.email eq "john@example.com")

// Update
userTable.updateOne(
    condition = User.email eq "john@example.com",
    modification = Modification { it.age assign 31 },
)
userTable.updateOneById(userId, Modification { it.age += 1 })
userTable.updateMany(
    condition = User.age lt 18,
    modification = Modification { it.nickname assign "minor" },
)

// Delete
userTable.deleteOne(User.email eq "john@example.com")
userTable.deleteMany(User.age lt 13)
```

### Conditions

```kotlin
// Comparison
User.age eq 30
User.age neq 30
User.age gt 18
User.age gte 21
User.age lt 65
User.age lte 64
User.age inside setOf(18, 21)
User.age notInside setOf(0)

// Strings
User.email contains "@example.com"          // case-insensitive
User.name.contains("John", ignoreCase = false)
User.name.mapCondition(Condition.RegexMatches("^J.*"))

// Nullable values
User.nickname eq null
User.address.notNull.city eq "Boise"        // never matches a null address

// Collections
User.friends.any { it eq friendId }
User.friends.all { it neq blockedId }

// Combining
(User.age gte 18) and (User.age lt 65)
(User.email eq "a@x.com") or (User.email eq "b@x.com")
!(User.age lt 18)
Condition.Always
Condition.Never

// The builder form, when you'd rather not repeat the type name
Condition<User> { (it.age gte 18) and (it.name contains "John") }
```

### Modifications

```kotlin
Modification<User> {
    it.age assign 31
    it.age += 1                      // increment (any Number)
    it.age coerceAtMost 120
    it.friends += friendId           // append one / += listOf(...) to append many
    it.friends -= blockedId          // remove one / -= listOf(...) to remove many
    it.friends.removeAll { it eq blockedId }
    it.address.notNull.city assign "Boise"   // does nothing when address is null
}
```

Maps can't be queried or partially modified; assign the whole map.

### Aggregations

```kotlin
val countByAge: Map<Int, Int> = userTable.groupCount(groupBy = User.age)
val total: Int = userTable.count(User.age gte 18)
val avgAge: Double? = userTable.aggregate(Aggregate.Average, property = User.age)
val avgAgeByCity: Map<String?, Double?> = userTable.groupAggregate(
    Aggregate.Average,
    groupBy = User.address.notNull.city,
    property = User.age,
)
```

`Aggregate` is `Sum`, `Average`, `StandardDeviationSample`, or `StandardDeviationPopulation`.

### Sorting and Limits

```kotlin
val page = userTable.find(
    condition = Condition.Always,
    orderBy = listOf(SortPart(User.age, ascending = false), SortPart(User._id)),
    skip = 20,
    limit = 10,
).toList()

// Or with the builder
val order = sort<User> { it.age.descending(); it._id.ascending() }
```

### Text Search

Models with `@TextIndex(["name", "email"])` can be searched with `userTable.findByTextIndex("john", condition = ...)`, which returns scored results. There is no full-text *condition*; for simple filtering use `contains` on string fields.

## Cache Usage

```kotlin
val cache: Cache = settings.cache("my-cache", context)
await cache.connect()

// Set with expiration
cache.set("key", "value", Duration.parse("1h"))

// Get
val value: String? = cache.get("key")

// Delete
cache.remove("key")

// Add (only if not exists)
cache.add("key", "value", Duration.parse("30m"))

// Clear all
cache.clear()
```

## File System Usage

```kotlin
val fs: PublicFileSystem = settings.files("uploads", context)
await fs.connect()

// Upload
val fileId = fs.upload(
    path = FileRef.Known("users/avatar.jpg"),
    content = byteArray
)

// Download
val content: ByteArray = fs.get(FileRef.Known("users/avatar.jpg"))

// Delete
fs.delete(FileRef.Known("users/avatar.jpg"))

// List
val files = fs.list(FileRef.Known("users/"))

// Get public URL (if supported)
val url = fs.url(FileRef.Known("users/avatar.jpg"))
```

## Testing Patterns

### Shared Test Suites

Service Abstractions uses shared test suites to ensure all implementations satisfy the same contract:

```kotlin
// In your test file
class MyMongoDbTests : ConditionTests() {
    override val database: Database = Database.Settings(
        "mongodb-test://localhost"
    )(
        "test-db",
        testContext
    )

    init {
        runBlocking { database.connect() }
    }
}
```

The abstract test class (`ConditionTests`, `CacheTests`, etc.) contains comprehensive tests that all implementations must pass.

### Test Databases

Use `-test` suffix URLs for ephemeral test instances:
- `mongodb-test://` - Starts temporary MongoDB
- `redis-test://` - Starts temporary Redis
- `ram://` - In-memory (no setup needed)

## Common Patterns

### Service Lifecycle in Applications

```kotlin
class MyApplication(settings: ServerSettings) {
    private val context = SettingContext(...)
    private val database = settings.database("main", context)
    private val cache = settings.cache("main", context)

    suspend fun start() {
        database.connect()
        cache.connect()
    }

    suspend fun stop() {
        cache.disconnect()
        database.disconnect()
    }
}
```

### Serverless (AWS Lambda, SnapStart)

Services support disconnect/reconnect for serverless environments:

```kotlin
class LambdaHandler {
    private val db = settings.database("lambda-db", context)

    init {
        runBlocking { db.connect() }
    }

    // Called before snapshot
    fun beforeCheckpoint() {
        runBlocking { db.disconnect() }
    }

    // Called after restore
    fun afterRestore() {
        runBlocking { db.connect() }
    }
}
```

### Custom Serialization

Register custom serializers in the context:

```kotlin
val module = SerializersModule {
    contextual(MyCustomType::class, MyCustomTypeSerializer)
}

val context = SettingContext(
    internalSerializersModule = module,
    // ...
)
```

## Module Structure

- **basis/** - Core interfaces (Setting, Service, SettingContext)
- **database/** - Database abstraction + InMemoryDatabase
- **database-mongodb/** - MongoDB implementation
- **database-postgres/** - PostgreSQL implementation
- **database-jsonfile/** - JSON file database
- **cache/** - Cache abstraction + MapCache
- **cache-redis/** - Redis implementation
- **cache-memcached/** - Memcached implementation
- **cache-dynamodb/** - DynamoDB implementation
- **files/** - File system abstraction
- **files-s3/** - S3 implementation
- **email/** - Email service abstraction
- **email-javasmtp/** - SMTP implementation
- **sms/** - SMS abstraction
- **sms-twilio/** - Twilio implementation

## Common Pitfalls

1. **Forgetting to call connect()**: Services must be connected before use
2. **Stale generated fields**: Run KSP after adding/changing models
3. **Missing @Queryable**: Required for generated fields
4. **Missing optics import**: `notNull`, `elements`, `Lens` etc. live in `com.lightningkite.services.database.optics`
5. **Not implementing HasId**: Database models must have `_id` field
6. **Incorrect URL schemes**: Check supported schemes for each service
7. **Missing SerializersModule**: Custom types need registered serializers
8. **Platform compatibility**: Not all implementations support all platforms (e.g., MongoDB is JVM-only)

## Build Commands

```bash
# Generate fields for models
./gradlew :your-module:kspCommonMainKotlinMetadata

# Run tests
./gradlew jvmTest                    # Fast JVM tests
./gradlew allTests                   # All platform tests
./gradlew :module:jvmTest            # Specific module

# Build
./gradlew build                      # All modules
./gradlew :module:build              # Specific module

# Publish locally (for testing)
./gradlew publishToMavenLocal
```

## OpenTelemetry Integration

Services automatically integrate with OpenTelemetry when provided in context:

```kotlin
val otel = OpenTelemetry.noop()  // Or real implementation
val context = SettingContext(
    otel = otel,
    // ...
)

// All database/cache operations are automatically traced
```

## Health Checks

All services support health checks:

```kotlin
val status: HealthStatus = database.healthCheck()

when (status) {
    is HealthStatus.Healthy -> println("Service is healthy")
    is HealthStatus.Unhealthy -> println("Service unhealthy: ${status.message}")
}

// Services declare their preferred check frequency
val frequency: Duration = database.healthCheckFrequency
```

## Best Practices

1. **Use Settings objects**: Makes configuration serializable and testable
2. **Leverage type-safe queries**: Use generated fields (`User.age gte 18`) instead of raw conditions
3. **Add indexes**: Use `@Index` annotation on frequently queried fields
4. **Test with shared suites**: Extend abstract test classes to ensure compatibility
5. **Handle disconnect**: Implement proper lifecycle management for serverless
6. **Use ram:// for tests**: Fast in-memory implementations for unit tests
7. **Register serializers early**: Set up SerializersModule before creating context
8. **Check platform support**: Verify your target platforms support the implementation

## Example: Complete Application

```kotlin
@Serializable
data class AppSettings(
    val database: Database.Settings = Database.Settings("mongodb://localhost"),
    val cache: Cache.Settings = Cache.Settings("redis://localhost:6379")
)

@Queryable
data class Post(
    override val _id: Uuid = Uuid.random(),
    @Index val authorId: Uuid,
    val title: String,
    val content: String,
    @Index val createdAt: Long = Clock.System.now().toEpochMilliseconds()
) : HasId<Uuid>

class BlogService(settings: AppSettings) {
    private val context = SettingContext(...)
    private val database = settings.database("blog", context)
    private val cache = settings.cache("blog", context)

    private lateinit var posts: Table<Post>

    suspend fun start() {
        database.connect()
        cache.connect()
        posts = database.table<Post>()
    }

    suspend fun createPost(authorId: Uuid, title: String, content: String): Post {
        val post = Post(authorId = authorId, title = title, content = content)
        posts.insertOne(post)
        return post
    }

    suspend fun getPostsByAuthor(authorId: Uuid): List<Post> {
        return posts.find(
            condition = Post.authorId eq authorId,
            orderBy = listOf(SortPart(Post.createdAt, ascending = false))
        ).toList()
    }

    suspend fun getPost(id: Uuid): Post? {
        // Try cache first
        val cached = cache.get<Post>("post:$id")
        if (cached != null) return cached

        // Fall back to database
        val post = posts.get(id)
        if (post != null) {
            cache.set("post:${post._id}", post, Duration.parse("1h"))
        }
        return post
    }

    suspend fun stop() {
        cache.disconnect()
        database.disconnect()
    }
}
```

## Quick Reference

### Must Remember
- Call `connect()` after service instantiation
- Run KSP after model changes: `./gradlew :module:kspCommonMainKotlinMetadata`
- Models need `@Queryable` and `HasId<T>`; fields like `User.age` are paths
- Use `-test` suffix URLs for ephemeral test services
- Check platform compatibility for implementations

### Query Cheat Sheet
```kotlin
// Conditions (User.age is a generated field)
User.age eq 30            // also neq, gt, gte, lt, lte, inside, notInside
User.name contains "jo"
User.address.notNull.city eq "Boise"
User.friends.any { it eq id }

// Modifications
Modification<User> {
    it.age assign 31
    it.age += 1
    it.friends += id
}

// Combining
condition1 and condition2
condition1 or condition2
!condition
```
