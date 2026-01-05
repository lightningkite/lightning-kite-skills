# Database Operations

## ModelRestEndpoints for CRUD Operations

**⚠️ IMPORTANT:** Use ModelRestEndpoints for CRUD operations rather than manually creating database endpoints.

### Basic Setup

```kotlin
// Define your model with @GenerateDataClassPaths
@Serializable
@GenerateDataClassPaths
data class Post(
    override val _id: Uuid = Uuid.random(),
    val title: String,
    val content: String,
    val authorId: Uuid,
    val createdAt: Instant = Clock.System.now()
) : HasId<Uuid>

// Set up ModelInfo with auth and permissions
val postInfo = database.modelInfo(
    auth = UserAuth.require() or AuthRequirement.None,
    permissions = {
        val user = authOrNull?.fetch()
        val isOwner = condition { it.authorId eqNn user?._id }

        ModelPermissions(
            create = if (user != null) Condition.Always else Condition.Never,
            read = Condition.Always,
            update = isOwner,
            delete = isOwner
        )
    }
)

// Create REST endpoints automatically (provides list, get, create, update, delete, query)
val posts = path.path("posts").path("rest") module ModelRestEndpoints(postInfo)

// Optional: Add WebSocket updates for real-time changes
val postsWithWs = path.path("posts").path("rest") include
    ModelRestEndpoints(postInfo) + ModelRestUpdatesWebsocket(postInfo)
```

### What ModelRestEndpoints Provides

- `GET /posts/rest` - List with pagination, sorting, filtering
- `GET /posts/rest/{id}` - Get by ID
- `POST /posts/rest` - Create
- `PUT /posts/rest/{id}` - Update
- `DELETE /posts/rest/{id}` - Delete
- `POST /posts/rest/query` - Advanced querying
- `WS /posts/rest/watch` - Real-time updates (if WebSocket added)

## Signal Composition and Lifecycle Hooks

ModelInfo supports powerful signal composition for validation, side effects, and data integrity:

```kotlin
val projectInfo = database.modelInfo(
    auth = UserAuth.require(),
    permissions = { permissions(this) },
    signals = { table ->
        table
            // Validate changes before they're applied
            .interceptChange(::interceptChange)

            // Validate creates before insertion
            .interceptCreates { validateProjects(it) }

            // React after changes are persisted
            .postChange { old, new -> handleProjectChange(old, new) }

            // Clean up after deletion
            .postDelete { deleteRelatedData(it) }

            // Process images automatically
            .interceptImagesForProcessing(
                MediaPreviewOptions.CorrectOddFeatures,
                MediaPreviewOptions(sizeInPixels = 200, type = MediaType.Image.JPEG)
            ) { it.avatar }

            // Maintain denormalized fields
            .denormalize(
                Project_organization,
                Project_organizationName,
                organizationTable,
                Organization_name,
                null
            )
    }
)
```

## Manual Database Operations

Use low-level database operations for custom business logic beyond simple CRUD:

```kotlin
val posts = database().table<Post>()

// Insert
posts.insertOne(Post(title = "Hello", content = "World"))

// Query
posts.find(condition { it.title eq "Hello" }).toList()

// Update
posts.updateOne(
    condition { it._id eq id },
    modification { it.title assign "Updated" }
)

// Delete
posts.deleteMany(condition { it.authorId eq userId })

// Complex queries
posts.find(
    condition = condition {
        (it.title.contains("Kotlin")) and (it.createdAt gt yesterday)
    },
    orderBy = listOf(SortPart(Post.path.createdAt, false)),
    skip = page * pageSize,
    limit = pageSize
).toList()
```

Use manual operations when you need:
- Custom business logic beyond CRUD
- Complex queries not supported by ModelRestEndpoints
- Special validation or transformation logic
- Aggregations or computed fields

## Modification Validation with mod.vet()

Validate modifications before they're applied to the database using `mod.vet()`:

```kotlin
fun interceptChange(mod: Modification<Project>): Modification<Project> {
    // Validate specific field modifications
    mod.vet(Project_projectTags) { fieldMod ->
        when (fieldMod) {
            is Modification.Assign -> {
                if (fieldMod.value.any { it != it.trim() })
                    throw BadRequestException("All tags must be trimmed")
                if (fieldMod.value.any { it != it.lowercase() })
                    throw BadRequestException("All tags must be lowercase")
            }
            is Modification.SetAppend -> {
                if (fieldMod.items.any { it != it.trim() })
                    throw BadRequestException("All tags must be trimmed")
                if (fieldMod.items.any { it != it.lowercase() })
                    throw BadRequestException("All tags must be lowercase")
            }
            else -> {}
        }
    }
    return mod
}

// Use in signals
signals = { table ->
    table.interceptChange(::interceptChange)
}
```

**Common Modification types:**
- `Modification.Assign` - Setting a value directly
- `Modification.SetAppend` / `Modification.SetRemove` - Modifying sets
- `Modification.ListAppend` / `Modification.ListRemove` - Modifying lists
- `Modification.Increment` / `Modification.Decrement` - Math operations

## Cascade Updates in postChange

```kotlin
context(runtime: ServerRuntime)
suspend fun postChange(old: Project, new: Project) {
    // Update denormalized fields across tables
    if (old.name != new.name) {
        Server.tasks.info.baseTable()
            .updateManyIgnoringResult(
                condition { it.project eq new._id },
                modification { it.projectName assign new.name }
            )
        Server.timeEntries.info.baseTable()
            .updateManyIgnoringResult(
                condition { it.project eq new._id },
                modification { it.projectName assign new.name }
            )
    }
}

context(runtime: ServerRuntime)
suspend fun postDelete(project: Project) {
    // Clean up related records
    Server.tasks.info.baseTable()
        .deleteManyIgnoringOld(condition { it.project eq project._id })
}
```

**Best practices:**
- Use `interceptChange` for validation (can throw exceptions to prevent changes)
- Use `postChange` for side effects (cascade updates, notifications, logging)
- Use `postDelete` for cleanup (delete related records, notify systems)
- Use `updateManyIgnoringResult` for performance (skips fetching updated records)
- Use `deleteManyIgnoringOld` for performance (skips fetching deleted records)

## REST PATCH with Modifications

**⚠️ CRITICAL:** REST PATCH endpoints ALWAYS use `Modification<T>` wrapper, never raw values.

**To update a field via PATCH:**
```bash
# Set a field to a value
PATCH /model/rest/{id}
{"fieldName": {"Assign": "newValue"}}

# Set an optional field to null (clear it)
PATCH /model/rest/{id}
{"fieldName": {"Assign": null}}

# Increment a number
PATCH /model/rest/{id}
{"count": {"Increment": 5}}

# Multiple fields at once
PATCH /model/rest/{id}
{
  "Chain": [
    {"firstName": {"Assign": "John"}},
    {"age": {"Increment": 1}}
  ]
}
```

**Common Use Cases:**

**Confirm a tentative reservation (clear expireAt):**
```bash
PATCH /reservation/rest/{id}
{"expireAt": {"Assign": null}}
```

**Cancel a reservation (set cancelledAt):**
```bash
PATCH /reservation/rest/{id}
{"cancelledAt": {"Assign": "2025-12-20T00:00:00Z"}}
```

**Check in to a session (set checkedInAt):**
```bash
PATCH /reservation/rest/{id}
{"checkedInAt": {"Assign": "2025-12-20T14:00:00Z"}}
```

**Why this matters:**
- ❌ `{"expireAt": null}` → JSON parse error
- ✅ `{"expireAt": {"Assign": null}}` → Works correctly
- Error message is cryptic because it comes from JSON parser itself
- Always wrap field updates in Modification objects

## Migrations and Startup Tasks

**Idempotent Migrations with `doOnce`:**

```kotlin
context(_: ServerRuntime)
suspend fun runMigrations() {
    // doOnce ensures migration only runs once, tracked in database
    doOnce("migrate-categories", database) {
        logging("migrate-categories") {
            migrateCategories()
        }
    }
    doOnce("migrate-icons", database) { migrateIcons() }
}

context(_: ServerRuntime)
suspend fun migrateCategories() {
    val projects = database().table<Project>().all().toList()
    for (project in projects) {
        database().table<Project>().updateOne(
            condition { it._id eq project._id },
            modification { it.categories assign project.legacyCategories.toSet() }
        )
    }
}
```

**Startup Initialization:**

```kotlin
// In Server object - runs once on server startup
init {
    path.path("setUpAdmins") bind startupOnce(database) {
        defaultData()  // Creates default admin users, organizations, etc.
    }
}

context(_: ServerRuntime)
suspend fun defaultData() {
    val adminUser = database().table<User>().insertOne(
        User(email = "admin@example.com", isSuperUser = true)
    )
    database().table<Organization>().insertOne(
        Organization(name = "Default Org")
    )
}
```

**Benefits:**
- `doOnce` tracks completion in database - safe for restarts
- Runs automatically on server startup
- Can be triggered manually via endpoint or CLI
- Idempotent - safe to call multiple times
