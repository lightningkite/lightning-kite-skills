---
name: service-abstractions
description: This skill should be used when the user asks about Service Abstractions library, infrastructure service management, or database/cache/file system configurations in Kotlin
version: 1.1.0
---

# Service Abstractions

Kotlin interfaces for infrastructure (database, cache, files, email, SMS, AI, payments, ...), each implementation chosen by a settings URL.  Source: `~/Projects/service-abstractions/`.

**The docs are the reference; read the chapter before writing code:** `~/Projects/service-abstractions/docs/index.md` (learning path, chapter per service, module table).  Key chapters:

| Topic | Doc |
|---|---|
| Settings URLs, `SettingContext`, scheme registration, lifecycle | `docs/basis.md` |
| Value types (`EmailAddress`, units, `MediaType`, `TypedData`) | `docs/data.md` |
| Tables, CRUD, indexes, permissions, vector search | `docs/database.md` |
| Conditions, modifications, optics, sorting, KSP build setup | `docs/database-queries.md` |
| Cache / files / email / SMS / ... | `docs/cache.md`, `docs/files.md`, `docs/email.md`, ... |
| Every URL scheme and its parameters | `docs/settings-url-reference.md` |
| Upgrading from 1.3 | `service-abstractions-1.4-migration` skill |

## Core pattern

```kotlin
@Serializable
data class AppSettings(
    val database: Database.Settings = Database.Settings("ram"),
    val cache: Cache.Settings = Cache.Settings("ram"),
)

MongoDatabase; RedisCache                     // reference each driver once, or parsing fails "No handler mongodb"
val context = TestSettingContext()            // Lightning Server provides the production context
val database = settings.database("database", context)
val posts: Table<Post> = database.prepare(DatabaseTableDefinition<Post>())   // creates table + indexes
```

- Each `Settings` serializes as a bare string: a settings file is a flat map of URLs (`"database": "mongodb://localhost/app"`).
- Every setting is constructed at startup; an empty string fails.  Omit unused ones.
- `connect()` is optional (services connect lazily); call `disconnect()` before a serverless freeze.

## Models and queries

```kotlin
@Queryable                                    // = @Serializable + generated fields
data class Post(
    override val _id: Uuid = Uuid.random(),
    @Index val author: EmailAddress,
    val title: String,
    val tags: List<String> = listOf(),
    val address: Address? = null,
) : HasId<Uuid>

Post.title eq "Hi"                            // Post.title is a Lens<Post, String>
Post.address.notNull.city eq "Provo"          // .notNull/.elements/.asType give an Optic
Post.author.raw contains "@example.com"       // .raw reaches a value class's inner value
(Post.title eq "a") or (Post.tags.any { it eq "kotlin" })   // parenthesize: infix ops share precedence
Condition<Post> { it.title eq "x" }
Modification<Post> { it.tags += "kotlin"; it.title assign "New" }
sort<Post> { it.title.ascending(ignoreCase = true) }

posts.updateOneById(id, Modification { it.title assign "Hello" })
posts.find(Post.tags.any { it eq "kotlin" }, orderBy = sort { it.title.ascending() }, limit = 20).toList()
```

Imports: `com.lightningkite.services.database.*` and `com.lightningkite.services.database.optics.*` (`notNull`, `elements`, `asType`, `raw`).

Deprecated forms that still compile with warnings: `User.path.email`, top-level `User_email`, lowercase `condition { }` / `modification { }`, `@GenerateDataClassPaths`, `DataClassPath*`.  Write `User.email`, `Condition { }`, `Modification { }`, `@Queryable`, `Optic`/`Lens`.

### KSP setup

In a multiplatform module, **only** `kspCommonMainKotlinMetadata` writes commonMain's fields (into `build/generated/ksp/common/commonMain/kotlin`, which must be a `commonMain` srcDir); `kspKotlinJvm` and the other target tasks deliberately write nothing for commonMain models.  The module's build file must make everything else wait for it, or the target KSP tasks fail with "The generated sources for commonMain are missing" (from 1000.0.0; a task that can't check leaves the folder empty and every generated field an unresolved reference):

```kotlin
tasks.matching { (it.name.startsWith("ksp") || it.name.startsWith("compile")) && it.name != "kspCommonMainKotlinMetadata" }
    .configureEach { dependsOn("kspCommonMainKotlinMetadata") }
```

Full setup (srcDir, processor on every `ksp*` configuration): "Build setup" in `docs/database-queries.md`.  Generated fields are top-level extensions in the model's package; other packages import them by name.

## Other services, in one line each

```kotlin
cache.set("session:abc", session, timeToLive = 30.minutes);  cache.get<Session>("session:abc")
files.root.then("avatars", "ada.png").put(TypedData.bytes(png, MediaType.Image.PNG))   // ExternalFileSystem
email.send(Email(subject = "Hi", to = listOf(EmailAddressWithName(addr, "Ada")), html = { body { p { +"Hello" } } }))
```

`Email(html = "<p>…</p>")` with a string is deprecated; the builder is kotlinx.html.

## Testing

Use `ram` (and `console`/`test` fakes) with `TestSettingContext()`; each chapter's Testing section shows how to read what a fake captured.  `delay://100ms-500ms/ram` adds latency; `mongodb-test` runs a throwaway MongoDB.  The `*-test` modules' suites are for implementation authors.

## Gotchas

- **"No handler <scheme>"**: driver class never referenced (AI/embedding modules: `XSettings.ensureRegistered()`).
- **Missing `optics.*` import**: "Unresolved reference 'notNull'".
- **Stale generated code** after a processor upgrade: delete `build/generated/ksp`.
- **Renaming a model class** without passing the old `name` to `DatabaseTableDefinition` points at a new, empty table.
- **Map fields** can't be queried or modified per key; `assign` the whole map.
- **Versions**: modules are versioned independently (epoch 1 = `1000.x`); use the catalog `com.lightningkite.stack:service-abstractions-catalog` (see `docs/index.md#installing`).  Releasing / trying local builds goes through `./lk release` in `~/Projects/metawork` (see its README), never a hand-run `publishToMavenLocal`.
