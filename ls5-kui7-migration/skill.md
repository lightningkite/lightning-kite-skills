---
name: Lightning Server 5 & KiteUI 7 Migration Guide
description: This skill should be used when migrating a project from older versions of Lightning Server (4.x) and KiteUI (6.x) to the latest versions (LS 5 and KUI 7). It covers dependency changes, import updates, code pattern migrations, and common pitfalls.
version: 1.0.0
---

# Lightning Server 5 & KiteUI 7 Migration Guide

This comprehensive guide helps you migrate projects from Lightning Server 4.x and KiteUI 6.x to the latest versions (Lightning Server 5.x and KiteUI 7.x).

## Quick Overview of Major Changes

### Architecture Changes
- **Service Abstractions**: Database, files, cache, email, and notifications are now separate packages under `com.lightningkite.services.*`
- **ServerBuilder Pattern**: Endpoints use `ServerBuilder` objects instead of `ServerPathGroup`
- **Context Parameters**: Heavy use of Kotlin context parameters (`context(runtime: ServerRuntime)`)
- **Uuid**: Migrated from `com.lightningkite.UUID` to `kotlin.uuid.Uuid`
- **Instant**: Migrated from `kotlinx.datetime.Instant` to `kotlin.time.Instant`
- **KiteUI Syntax**: Changed from dash syntax (`card - col { }`) to dot syntax (`card.col { }`)

---

## Part 1: Gradle Configuration Changes

### 1.1 libs.versions.toml Updates

**Version Updates:**
```toml
# OLD Versions
kiteui = "6.0.1-96"
kotlin = "2.2.20"
lightningServer = "4.1.139"
lightningServerKiteui = "6.0.1-40"
vite = "0.6.0"

# NEW Versions
kiteui = "7.0.0-prerelease-93"
kotlin = "2.2.21"
lightningServer = "5.0.0-prerelease-275"
lightningServerKiteui = "8.0.0-prerelease-65"
kfc = "16.1.0"
serviceAbstractions = "0.0.1-94"
```

**Library Name Changes:**

| OLD Library | NEW Library |
|------------|-------------|
| `comLightningkiteKiteuiLibrary` | `comLightningKite-kiteui` |
| `comLightningkiteLightningserverShared` | Split into multiple modules (see below) |
| `comLightningkiteLightningserverServerCore` | `comLightningKite-lightningServer-core` |
| `comLightningkiteLightningserverServerMongo` | `comLightningKite-services-database-mongodb` |
| `comLightningkiteLightningserverServerFirebase` | `comLightningKite-services-notifications-firebase` |
| `comLightningkiteLightningserverServerMedia` | `comLightningKite-lightningServer-media` |
| `comLightningkiteLightningserverProcessor` | `comLightningKite-services-database-processor` |
| `comLightningkiteLightningserverClient` | `comLightningKite-lightningServerClient` |
| `comLightningkiteLightningserverServerKtor` | `comLightningKite-lightningServer-engine-ktor` |
| `comLightningkiteLightningserverServerAws` | `comLightningKite-lightningServer-engine-aws` |

**NEW Split Shared Modules (replace single `...Shared`):**
```toml
[libraries]
comLightningKite-lightningServer-core-shared = { module = "com.lightningkite.lightningserver:core-shared", version.ref = "lightningServer" }
comLightningKite-lightningServer-typed-shared = { module = "com.lightningkite.lightningserver:typed-shared", version.ref = "lightningServer" }
comLightningKite-lightningServer-sessions-shared = { module = "com.lightningkite.lightningserver:sessions-shared", version.ref = "lightningServer" }
comLightningKite-lightningServer-files-shared = { module = "com.lightningkite.lightningserver:files-shared", version.ref = "lightningServer" }
comLightningKite-lightningServer-media-shared = { module = "com.lightningkite.lightningserver:media-shared", version.ref = "lightningServer" }
```

**NEW Service Abstractions Libraries:**
```toml
comLightningKite-services-database = { module = "com.lightningkite.services:database", version.ref = "serviceAbstractions" }
comLightningKite-services-database-jsonfile = { module = "com.lightningkite.services:database-jsonfile", version.ref = "serviceAbstractions" }
comLightningKite-services-database-mongodb = { module = "com.lightningkite.services:database-mongodb", version.ref = "serviceAbstractions" }
comLightningKite-services-database-processor = { module = "com.lightningkite.services:database-processor", version.ref = "serviceAbstractions" }
comLightningKite-services-email-javasmtp = { module = "com.lightningkite.services:email-javasmtp", version.ref = "serviceAbstractions" }
comLightningKite-services-files-s3 = { module = "com.lightningkite.services:files-s3", version.ref = "serviceAbstractions" }
comLightningKite-services-notifications-firebase = { module = "com.lightningkite.services:notifications-fcm", version.ref = "serviceAbstractions" }
```

**Plugin Changes:**
```toml
[plugins]
# OLD
comLightningkiteKiteui = { id = "com.lightningkite.kiteui", version.ref = "kiteui" }
vite = { id = "dev.opensavvy.vite.kotlin", version.ref = "vite" }

# NEW
comLightningKite-kiteuiPlugin = { id = "com.lightningkite.kiteui", version.ref = "kiteui" }
kfc = { id = "io.github.turansky.kfc.application", version.ref = "kfc" }
jsPlainObjects = { id = "org.jetbrains.kotlin.plugin.js-plain-objects", version.ref = "jsPlainObjects" }
```

### 1.2 apps/build.gradle.kts Updates

**Plugin Changes:**
```kotlin
// OLD
plugins {
    alias(libs.plugins.comLightningkiteKiteui)
    alias(libs.plugins.vite)
    id("com.google.gms.google-services")
}

// NEW
plugins {
    alias(libs.plugins.comLightningKite.kiteuiPlugin)
    alias(libs.plugins.kfc)
    alias(libs.plugins.jsPlainObjects)
    alias(libs.plugins.googleServices)
}
```

**Dependency Changes:**
```kotlin
// OLD
commonMain.dependencies {
    api(libs.comLightningkiteKiteuiLibrary)
    api(libs.comLightningkiteLightningserverShared)
    api(libs.comLightningkiteLightningserverClient)
}

// NEW
commonMain.dependencies {
    api(libs.comLightningKite.kiteui)
    api(libs.comLightningKite.lightningServer.core.shared)
    api(libs.comLightningKite.lightningServer.typed.shared)
    api(libs.comLightningKite.lightningServer.sessions.shared)
    api(libs.comLightningKite.lightningServerClient)
}
```

**Add Compiler Options (REQUIRED):**
```kotlin
kotlin {
    compilerOptions {
        optIn.add("kotlin.time.ExperimentalTime")
        optIn.add("kotlin.uuid.ExperimentalUuidApi")
        freeCompilerArgs.add("-Xcontext-parameters")
    }
}
```

**Remove Vite Config (replaced by KFC):**
```kotlin
// REMOVE this block
vite {
    publicDir.set("public")
    base.set("/")
}
```

### 1.3 server/build.gradle.kts Updates

```kotlin
// OLD
dependencies {
    api(libs.comLightningkiteLightningserverShared)
    api(libs.comLightningkiteLightningserverServerCore)
    api(libs.comLightningkiteLightningserverServerMongo)
    api(libs.comLightningkiteLightningserverServerFirebase)
    api(libs.comLightningkiteLightningserverServerMedia)
    ksp(libs.comLightningkiteLightningserverProcessor)
}

// NEW
dependencies {
    api(libs.comLightningKite.services.database)
    api(libs.comLightningKite.services.database.jsonfile)
    api(libs.comLightningKite.services.database.mongodb)
    api(libs.comLightningKite.services.notifications.firebase)
    api(libs.comLightningKite.lightningServer.core)
    api(libs.comLightningKite.lightningServer.typed)
    api(libs.comLightningKite.lightningServer.files)
    api(libs.comLightningKite.lightningServer.media)
    api(libs.comLightningKite.lightningServer.sessions)
    api(libs.comLightningKite.lightningServer.sessions.email)
    api(libs.comLightningKite.lightningServer.sessions.sms)
    ksp(libs.comLightningKite.services.database.processor)
}

kotlin {
    compilerOptions {
        optIn.add("kotlin.time.ExperimentalTime")
        optIn.add("kotlin.uuid.ExperimentalUuidApi")
        freeCompilerArgs.add("-Xcontext-parameters")
    }
}
```

### 1.4 shared/build.gradle.kts Updates

```kotlin
// OLD
commonMain.dependencies {
    api(libs.comLightningkiteLightningserverShared)
}

// NEW
commonMain.dependencies {
    api(libs.comLightningKite.lightningServer.core.shared)
    api(libs.comLightningKite.lightningServer.typed.shared)
    api(libs.comLightningKite.lightningServer.sessions.shared)
    api(libs.comLightningKite.lightningServer.files.shared)
    api(libs.comLightningKite.lightningServer.media.shared)
}

kotlin {
    compilerOptions {
        optIn.add("kotlin.time.ExperimentalTime")
        optIn.add("kotlin.uuid.ExperimentalUuidApi")
        freeCompilerArgs.add("-Xcontext-parameters")
    }
}
```

---

## Part 2: Import Statement Changes

### 2.1 Core Type Imports

```kotlin
// OLD
import com.lightningkite.UUID
import com.lightningkite.now
import com.lightningkite.nowLocal

// NEW
import kotlin.uuid.Uuid
import kotlin.time.Instant
import kotlin.time.Clock
// Note: now() comes from com.lightningkite.lightningserver.runtime.now
import com.lightningkite.lightningserver.runtime.now
```

### 2.2 Database Imports

```kotlin
// OLD
import com.lightningkite.lightningdb.*

// NEW
import com.lightningkite.services.data.*
import com.lightningkite.services.database.*
import com.lightningkite.services.files.*
```

### 2.3 Lightning Server Imports

```kotlin
// OLD
import com.lightningkite.lightningserver.auth.Authentication
import com.lightningkite.lightningserver.auth.authOptions
import com.lightningkite.lightningserver.core.ServerPath
import com.lightningkite.lightningserver.core.ServerPathGroup
import com.lightningkite.lightningserver.db.*
import com.lightningkite.lightningserver.exceptions.*
import com.lightningkite.lightningserver.settings.Settings
import com.lightningkite.lightningserver.settings.setting
import com.lightningkite.lightningserver.settings.generalSettings
import com.lightningkite.lightningserver.schedule.CronPattern
import com.lightningkite.lightningserver.schedule.schedule
import com.lightningkite.lightningserver.tasks.task
import com.lightningkite.lightningserver.tasks.startup
import com.lightningkite.lightningserver.tasks.startupOnce

// NEW
import com.lightningkite.lightningserver.*
import com.lightningkite.lightningserver.auth.AuthRequirement
import com.lightningkite.lightningserver.auth.require
import com.lightningkite.lightningserver.definition.builder.ServerBuilder
import com.lightningkite.lightningserver.definition.generalSettings
import com.lightningkite.lightningserver.definition.secretBasis
import com.lightningkite.lightningserver.definition.ScheduledTask
import com.lightningkite.lightningserver.definition.Task
import com.lightningkite.lightningserver.data.CronPattern
import com.lightningkite.lightningserver.runtime.ServerRuntime
import com.lightningkite.lightningserver.runtime.invoke
import com.lightningkite.lightningserver.runtime.now
import com.lightningkite.lightningserver.pathing.arg1
import com.lightningkite.lightningserver.typed.startupOnce
```

### 2.4 Session & Auth Imports

```kotlin
// OLD
import com.lightningkite.lightningserver.auth.proof.PasswordSecret
import com.lightningkite.lightningserver.auth.proof.OtpSecret
import com.lightningkite.lightningserver.auth.proof.Proof
import com.lightningkite.lightningserver.auth.AuthClientEndpoints

// NEW
import com.lightningkite.lightningserver.sessions.*
import com.lightningkite.lightningserver.sessions.PasswordSecret
import com.lightningkite.lightningserver.sessions.TotpSecret
import com.lightningkite.lightningserver.sessions.proofs.Proof
import com.lightningkite.lightningserver.auth.AuthEndpoints
```

### 2.5 Service Abstractions Imports

```kotlin
// OLD
import com.lightningkite.lightningserver.files.ServerFile
import com.lightningkite.lightningserver.email.Email
import com.lightningkite.lightningserver.email.EmailLabeledValue
import com.lightningkite.lightningserver.core.ContentType
import com.lightningkite.lightningserver.db.Database
import com.lightningkite.lightningserver.cache.CacheSettings
import com.lightningkite.lightningserver.files.FilesSettings
import com.lightningkite.lightningserver.notifications.NotificationSettings

// NEW
import com.lightningkite.services.files.ServerFile
import com.lightningkite.services.files.PublicFileSystem
import com.lightningkite.services.email.Email
import com.lightningkite.services.email.EmailAddressWithName
import com.lightningkite.services.database.Database
import com.lightningkite.services.cache.Cache
import com.lightningkite.services.notifications.NotificationService
import com.lightningkite.MediaType
```

### 2.6 Client-Side Imports

```kotlin
// OLD
import com.lightningkite.lightningdb.*
import com.lightningkite.lightningserver.auth.AuthClientEndpoints

// NEW
import com.lightningkite.lightningserver.*
import com.lightningkite.lightningserver.sessions.*
import com.lightningkite.lightningserver.auth.AuthEndpoints
import com.lightningkite.services.data.*
import com.lightningkite.services.database.*
import com.lightningkite.services.files.*
```

---

## Part 3: Code Pattern Changes

### 3.1 Server Definition Pattern

```kotlin
// OLD
object Server : ServerPathGroup(ServerPath.root) {
    val cache = setting(name = "cache", default = CacheSettings())
    val database = setting(name = "database", default = DatabaseSettings())
    val email = setting(name = "email", default = EmailSettings())
    val files = setting(name = "files", default = FilesSettings())
    val notifications = setting("notifications", default = NotificationSettings("console"))

    val users = UserEndpoints(path("users"))
}

// NEW
object Server : ServerBuilder() {
    val cache = setting("cache", Cache.Settings())
    val database = setting("database", Database.Settings())
    val email = setting("email", EmailService.Settings())
    val files = setting("files", PublicFileSystem.Settings())
    val notifications = setting("notifications", NotificationService.Settings("console"))

    val users = path.path("users") module UserEndpoints
}
```

### 3.2 Endpoint Group Definition

```kotlin
// OLD
class UserEndpoints(path: ServerPath) : ServerPathGroup(path) {
    val info: ModelInfo<User, User, UUID> = Server.database.modelInfo(
        authOptions = authOptions<User>(),
        serialization = ModelSerializationInfo<User, UUID>(),
        permissions = ::permissions,
        signals = { collection -> /* ... */ }
    )

    val rest = ModelRestEndpoints(path("rest"), info)
    val socketUpdates = ModelRestUpdatesWebsocket(path("rest"), info)
}

// NEW
object UserEndpoints : ServerBuilder() {
    val info: ModelInfo<User, User, Uuid> = Server.database.modelInfo(
        auth = UserAuth.require(),
        permissions = { permissions(this) },
        signals = { table -> /* ... */ }
    )

    val rest = path.path("rest") include ModelRestEndpoints(info)
    val socketUpdates = path.path("rest") include ModelRestUpdatesWebsocket(info)
}
```

### 3.3 Permissions Function Signature

```kotlin
// OLD
suspend fun permissions(auth: AuthAccessor<User>): ModelPermissions<User> {
    if (auth.isSuperUser()) return ModelPermissions.allowAll<User>()
    // ...
}

// NEW
context(runtime: ServerRuntime)
suspend fun permissions(auth: AuthAccess<User>): ModelPermissions<User> {
    if (auth.isSuperUser()) return ModelPermissions.allowAll<User>()
    // ...
}
```

### 3.4 Signal Hooks

```kotlin
// OLD
signals = { collection ->
    collection
        .interceptCreates(::interceptCreates)
        .postChange(::postChange)
        .postCreate(::postCreate)
}

// Hook function:
suspend fun interceptCreates(users: Iterable<User>): List<User> { /* ... */ }
suspend fun postChange(old: User, new: User) { /* ... */ }
suspend fun postCreate(user: User) { /* ... */ }

// NEW
signals = { table ->
    table
        .interceptCreates { interceptCreates(it) }
        .postChange { o, n -> postChange(o, n) }
        .postCreate { postCreate(it) }
}

// Hook function (now requires context parameter):
context(runtime: ServerRuntime)
suspend fun interceptCreates(users: Iterable<User>): List<User> { /* ... */ }

context(runtime: ServerRuntime)
suspend fun postChange(old: User, new: User) { /* ... */ }

context(runtime: ServerRuntime)
suspend fun postCreate(user: User) { /* ... */ }
```

### 3.5 Table Access Methods

```kotlin
// OLD
info.collection().find(condition { /* ... */ })
info.collection().insertOne(model)
info.collection().updateManyIgnoringResult(condition, modification)
info.baseCollection().updateManyIgnoringResult(condition, modification)

// NEW
info.table().find(condition { /* ... */ })
info.table().insertOne(model)
info.table().updateManyIgnoringResult(condition, modification)
info.baseTable().updateManyIgnoringResult(condition, modification)
```

### 3.6 Startup Tasks

```kotlin
// OLD
init {
    startupOnce("$path/appStoreTestUser", Server.database) {
        // initialization code
    }
}

// NEW
val createAppStoreTester = path.path("appStoreTestUser") bind startupOnce(Server.database) {
    // initialization code
}
```

### 3.7 HTTP Endpoint Binding

```kotlin
// OLD
val index = get.handler {
    HttpResponse.redirectToGet(meta.admin.path.toString())
}

// NEW
val index = path.get bind HttpHandler {
    HttpResponse.redirectToGet(meta.admin2.location.path.toString())
}
```

### 3.8 Path Arguments

```kotlin
// OLD
val idPath = restPath.arg<UUID>("ID", "User _ID")

// NEW
val idPath = restPath.arg<Uuid>("ID")
```

### 3.9 Task Invocation

```kotlin
// OLD
newUserNotifications(user)

// NEW
newUserNotifications.invoke(user)
```

### 3.10 Media Types

```kotlin
// OLD
import com.lightningkite.lightningserver.core.ContentType
MediaPreviewOptions(sizeInPixels = 200, type = ContentType.Image.JPEG)

// NEW
import com.lightningkite.MediaType
MediaPreviewOptions(sizeInPixels = 200, type = MediaType.Image.JPEG)
```

---

## Part 4: KiteUI 7 Changes

### 4.1 View Modifier Syntax (MAJOR CHANGE)

The biggest change in KiteUI 7 is the view modifier syntax. The dash operator is replaced with dot operator:

```kotlin
// OLD (Dash syntax)
centered - sizeConstraints(width = 10.rem) - row {
    centered - icon(Icon.folderCopy, "")
    centered - text { /* ... */ }
}
scrolling - col {
    expanding - space()
    centered - important - button { /* ... */ }
}
card - button {
    /* ... */
}

// NEW (Dot syntax)
centered.sizeConstraints(width = 10.rem).row {
    centered.icon(Icon.folderCopy, "")
    centered.text { /* ... */ }
}
scrolling.col {
    expanding.space()
    centered.important.button { /* ... */ }
}
card.button {
    /* ... */
}
```

### 4.2 Semantic Application

```kotlin
// OLD
ListSemantic.onNext - col { /* ... */ }
DialogSemantic.onNext - col { /* ... */ }
TestServerSemantic.onNext - button { /* ... */ }

// NEW
ListSemantic.onNext.col { /* ... */ }
// OR
onNext(ListSemantic).col { /* ... */ }
onNext(DialogSemantic).col { /* ... */ }
onNext(TestServerSemantic).button { /* ... */ }
```

### 4.3 ViewWrapper Removal

```kotlin
// OLD
fun userMark() = sizeConstraints(width = size, height = size) - (if (hint) {
    hintPopover(PopoverPreferredDirection.rightCenter) { /* ... */ }
} else ViewWrapper) - frame { /* ... */ }

// NEW
fun userMark() = (if (hint) {
    sizeConstraints(width = size, height = size).hintPopover(PopoverPreferredDirection.rightCenter) { /* ... */ }
} else sizeConstraints(width = size, height = size)).frame { /* ... */ }
```

### 4.4 Render Function Return Type

```kotlin
// OLD
override fun ViewWriter.render(): ViewModifiable = scrolling - col { /* ... */ }

// NEW
override fun ViewWriter.render() {
    scrolling.col { /* ... */ }
}
// Note: render() returns Unit now, not ViewModifiable
```

### 4.5 Theme Derivations

```kotlin
// OLD
Theme(
    derivations = mapOf(
        HeaderSemantic to { it.withoutBack(font = title) },
        FieldSemantic to { it.withBack(outlineWidth = 1.px, revert = true) },
    )
)

// NEW
Theme(
    semanticOverrides = semanticOverridesOf(
        HeaderSemantic to { it.withoutBack(font = title) },
        FieldSemantic to { it.withBack(outlineWidth = 1.px, cascading = false) },
    )
)
// Note: `revert = true` is now `cascading = false`
```

### 4.6 OuterSemantic CornerRadii

```kotlin
// OLD
OuterSemantic to {
    it.withBack(
        cascading = false,
        gap = 1.px,
        padding = Edges.ZERO,
        background = Color.gray(0.3f)
    )
}

// NEW
OuterSemantic to {
    it.withBack(
        cascading = false,
        gap = 1.px,
        padding = Edges.ZERO,
        background = Color.gray(0.3f),
        cornerRadii = CornerRadii.Constant(0.dp),  // REQUIRED now
    )
}
```

### 4.7 App Function

```kotlin
// OLD
fun ViewWriter.app(navigator: PageNavigator, dialog: PageNavigator): ViewModifiable {
    prepareModelsClient()
    prepareModelsShared()
    com.lightningkite.prepareModelsShared()
    DefaultSerializersModule = ClientModule
    // ...
    return OuterSemantic.onNext - frame { /* ... */ }
}

// NEW
fun ViewWriter.app(navigator: PageNavigator, dialog: PageNavigator) {
    // Model preparation calls removed - no longer needed
    // ...
    OuterSemantic.onNext.frame { /* ... */ }
}
// Note: Returns Unit now, model prep calls removed
```

---

## Part 5: Model Changes

### 5.1 UUID to Uuid

```kotlin
// OLD
data class User(
    override val _id: UUID = UUID.random(),
    @References(User::class) val spouse: UUID? = null,
    @MultipleReferences(Project::class) val projectFavorites: Set<UUID> = emptySet(),
) : HasId<UUID>

// NEW
data class User(
    override val _id: Uuid = Uuid.random(),
    @References(User::class) val spouse: Uuid? = null,
    @MultipleReferences(Project::class) val projectFavorites: Set<Uuid> = emptySet(),
) : HasId<Uuid>
```

### 5.2 Clock Usage

```kotlin
// OLD
val currentYear = Clock.System.now().toLocalDateTime(TimeZone.currentSystemDefault()).year
val releaseDate: LocalDate = Clock.default.todayIn(TimeZone.currentSystemDefault())

// NEW
val currentYear = now().toLocalDateTime(TimeZone.currentSystemDefault()).year
val releaseDate: LocalDate = Clock.System.todayIn(TimeZone.currentSystemDefault())
```

### 5.3 LocalDate Formatting

```kotlin
// OLD
date.format(LocalDate.Format {
    monthNumber(Padding.NONE); char('/'); dayOfMonth(Padding.NONE); char('/'); year()
})

// NEW
date.format(LocalDate.Format {
    monthNumber(Padding.NONE); char('/'); day(Padding.NONE); char('/'); year()
})
// Note: `dayOfMonth` is now `day`
```

### 5.4 Import Ordering

```kotlin
// OLD (mixed imports)
import kotlinx.datetime.*
import kotlin.time.Duration

// NEW (Kotlin stdlib first, then kotlinx)
import kotlin.time.Duration
import kotlin.time.Instant
import kotlin.uuid.Uuid
import kotlinx.datetime.LocalDate
import kotlinx.datetime.TimeZone
```

---

## Part 6: Client SDK Changes

### 6.1 Session Class

```kotlin
// OLD
class UserSession(
    private val api2: Api2,
    val userId: UUID
) {
    val uncached get() = api2
    val otpSecret: ModelCache<OtpSecret, UUID> = ModelCache(uncached.otpSecret, ...)
}

// NEW
class UserSession(
    val uncached: Api,
    val userId: Uuid
) {
    val totpSecret: ModelCache<TotpSecret, Uuid> = ModelCache(uncached.userAuth.totp, ...)
}
// Note: Api2 renamed to Api, OtpSecret renamed to TotpSecret
```

### 6.2 API Endpoint Paths

```kotlin
// OLD
uncached.eventSubscription
uncached.comment
uncached.notificationForUser
uncached.otpSecret

// NEW
uncached.ltNotifications.subscriptions
uncached.comments
uncached.ltNotifications.notifications
uncached.userAuth.totp
```

### 6.3 Auth Component

```kotlin
// OLD
AuthComponent2(
    AuthClientEndpoints(
        subjects = mapOf("User" to api.userAuth),
        authenticatedSubjects = mapOf(),
        emailProof = api.emailProof,
        oneTimePasswordProof = api.oneTimePasswordProof,
        backupCodeProof = api.backupCodeProof,
        passwordProof = api.passwordProof,
    )
)

// NEW
AuthComponent2(
    AuthEndpoints(
        subjects = mapOf("User" to api.userAuth),
        emailProof = api.userAuth.email,
        oneTimePasswordProof = api.userAuth.totp,
        backupCodeProof = api.userAuth.backupCode,
        passwordProof = api.userAuth.password,
    )
)
// Note: authenticatedSubjects removed, proof endpoints moved under userAuth
```

### 6.4 LiveApi Class

```kotlin
// OLD
class LiveApi2(val fetcher: Fetcher): Api2 { /* ... */ }
(session().uncached as LiveApi2).fetcher

// NEW
class LiveApi(val fetcher: Fetcher): Api { /* ... */ }
(session().uncached as LiveApi).fetcher
```

---

## Part 7: Server Endpoint Registration

### 7.1 Module Pattern

```kotlin
// OLD
val users = UserEndpoints(path("users"))
val comments = CommentsEndpoints(path("comments"))

// NEW
val users = path.path("users") module UserEndpoints
val comments = path.path("comments") module CommentsEndpoints
```

### 7.2 REST + WebSocket Endpoints

```kotlin
// OLD
val rest = ModelRestEndpoints(path("rest"), info)
val socketUpdates = ModelRestUpdatesWebsocket(path("rest"), info)

// NEW
val rest = path.path("rest") include ModelRestEndpoints(info)
val socketUpdates = path.path("rest") include ModelRestUpdatesWebsocket(info)
// OR combined:
val restWithWs = path.path("rest") include ModelRestEndpoints(info) + ModelRestUpdatesWebsocket(info)
```

### 7.3 Multiplex WebSocket

```kotlin
// OLD
import com.lightningkite.lightningserver.websocket.MultiplexWebSocketHandler
val multiplex = path("multiplex").websocket(MultiplexWebSocketHandler(cache))

// NEW
import com.lightningkite.lightningserver.websockets.MultiplexWebSocketHandler
import com.lightningkite.lightningserver.websockets.QueryParamWebSocketHandler
val multiplex = path.path("multiplex") include MultiplexWebSocketHandler(cache)
```

---

## Part 8: Common Migration Pitfalls

### 8.1 Forgotten Context Parameters

**Symptom:** Compile error about missing context receiver

**Solution:** Add `context(runtime: ServerRuntime)` to functions called from hooks:

```kotlin
// Add context to all hook functions
context(runtime: ServerRuntime)
suspend fun myHookFunction() { /* ... */ }
```

### 8.2 Collection vs Table

**Symptom:** Unresolved reference `collection()`

**Solution:** Replace all `.collection()` with `.table()`:

```kotlin
// Find and replace:
info.collection()  ->  info.table()
info.baseCollection()  ->  info.baseTable()
```

### 8.3 Missing CornerRadii in OuterSemantic

**Symptom:** Runtime theme errors or unexpected rendering

**Solution:** Add `cornerRadii = CornerRadii.Constant(0.dp)` to OuterSemantic overrides

### 8.4 Dash Syntax Compilation Errors

**Symptom:** Many "unresolved reference" errors in KiteUI code

**Solution:** Convert all dash syntax to dot syntax:

```bash
# Regex find/replace pattern (approximate):
# Find: (\w+)\s*-\s*(\w+)
# Replace with: $1.$2
# Then manually review and fix edge cases
```

### 8.5 Wrong Instant Import

**Symptom:** Type mismatch errors with Instant

**Solution:** Use `kotlin.time.Instant` not `kotlinx.datetime.Instant`:

```kotlin
import kotlin.time.Instant
// NOT: import kotlinx.datetime.Instant
```

### 8.6 Api2 Renamed to Api

**Symptom:** Unresolved reference `Api2`

**Solution:** Rename `Api2` to `Api` and `LiveApi2` to `LiveApi`

### 8.7 OtpSecret Renamed to TotpSecret

**Symptom:** Unresolved reference `OtpSecret`

**Solution:** Replace `OtpSecret` with `TotpSecret`

---

## Part 9: Migration Checklist

### Pre-Migration
- [ ] Create a migration branch
- [ ] Backup current working state
- [ ] Document any custom modifications

### Gradle Files
- [ ] Update `libs.versions.toml` with new versions and library names
- [ ] Update all `build.gradle.kts` files with new dependencies
- [ ] Add compiler options for context parameters and experimental APIs
- [ ] Replace Vite plugin with KFC plugin

### Server Code
- [ ] Convert `ServerPathGroup` classes to `ServerBuilder` objects
- [ ] Update all imports (see Part 2)
- [ ] Replace `.collection()` with `.table()` everywhere
- [ ] Add `context(runtime: ServerRuntime)` to hook functions
- [ ] Update endpoint registration to use `module` and `include`
- [ ] Replace `UUID` with `Uuid`
- [ ] Update settings types (`CacheSettings` -> `Cache.Settings()`, etc.)

### Shared Models
- [ ] Replace `UUID` with `Uuid` in all data classes
- [ ] Update `HasId<UUID>` to `HasId<Uuid>`
- [ ] Update date formatting (`dayOfMonth` -> `day`)
- [ ] Update imports for services.data and services.database

### Client/Apps Code
- [ ] Convert all dash syntax to dot syntax in KiteUI views
- [ ] Update `render()` to return `Unit`
- [ ] Replace `derivations` with `semanticOverrides`
- [ ] Replace `revert = true` with `cascading = false`
- [ ] Add `cornerRadii` to OuterSemantic overrides
- [ ] Update auth component configuration
- [ ] Update session class references (Api2 -> Api)
- [ ] Remove `prepareModels*` calls
- [ ] Update endpoint paths in SDK usage

### Post-Migration
- [ ] Run `./gradlew build` to check for compilation errors
- [ ] Fix any remaining import issues
- [ ] Run server and verify endpoints work
- [ ] Test client application
- [ ] Run all tests

---

## Part 10: Automated Migration Helpers

### 10.1 Regex Replacements for KiteUI

These regex patterns can help automate common replacements (test carefully!):

```regex
# Dash to dot (simple cases)
Find: (\w+)\s+-\s+(\w+)\s+\{
Replace: $1.$2 {

# centered - text pattern
Find: centered\s+-\s+text
Replace: centered.text

# expanding - space pattern
Find: expanding\s+-\s+space
Replace: expanding.space
```

### 10.2 Import Replacement Script

For bulk import updates, consider using sed:

```bash
# UUID to Uuid
find . -name "*.kt" -exec sed -i '' 's/com\.lightningkite\.UUID/kotlin.uuid.Uuid/g' {} \;

# Collection to table
find . -name "*.kt" -exec sed -i '' 's/\.collection()/\.table()/g' {} \;
find . -name "*.kt" -exec sed -i '' 's/\.baseCollection()/\.baseTable()/g' {} \;
```

---

## Usage

**When to invoke this skill:**
- You're upgrading a project from LS 4.x to LS 5.x
- You're upgrading from KiteUI 6.x to KiteUI 7.x
- You see compilation errors after updating Lightning Kite dependencies
- You need to understand the differences between old and new patterns
- You're seeing context parameter errors in server code

Say: "Help me migrate to Lightning Server 5" or "What changed between KiteUI 6 and 7?"
