---
name: lightning-server-kiteui
description: This skill should be used when the user wants to work with KiteUI and Lightning Server together.
version: 2.0.0
---

# Lightning Server + KiteUI

The glue library (`com.lightningkite.lightningserver:client` and `:server-client-utils`) turns a Lightning Server
into a typed client, a live client-side cache (`ModelCache`), auth screens, serializer-driven forms and an admin
panel.

This file is the entry point.  The full, current docs live in the library repo; read the chapter before writing code:

| Topic | Doc (`~/Projects/lightning-server-kiteui/docs/`) |
|---|---|
| Gradle setup, project layout, what the server must mount | `getting-started.md` |
| `generateSdk`, `Api`/`LiveApi`/`CachedApi`, fetchers, sessions, files | `api-client.md` |
| `ModelCache`: `item`/`list`, freshness, pagination, writes, edit-a-record | `model-cache.md` |
| `AuthComponent`, `ReAuthComponent`, `SecurityComponent` | `auth.md` |
| `form()`, `view()`, `renderTable()`, annotations, custom renderers | `forms.md` |
| `/meta/admin/` console | `admin.md` |
| `StaticSiteRenderer` | `static-site-rendering.md` |
| Mocks, virtual time, full-stack tests | `testing.md` |
| Working demo (`demo-server`, `demo-apps`): which page shows what | `demo-apps.md` |

For one side only, use the **lightning-server** skill (models, endpoints, permissions, auth, server tests) or the
**kiteui** skill (views, reactivity, navigation, theming, UI tests).  Start new projects from
[ls-kiteui-starter](https://github.com/lightningkite/ls-kiteui-starter).

## Layout and loop

```
shared/   KMP: @Queryable models, used by both sides
server/   JVM: Lightning Server; also writes the app's SDK
apps/     KMP: KiteUI app; the generated SDK (Api.kt, LiveApi.kt, CachedApi.kt) lives here
```

1. Change a model in `shared` or an endpoint in `server`.
2. `./gradlew :server:generateSdk` rewrites all three SDK files, `CachedApi.kt` included (`CachingSdk` adds one
   `ModelCache` per model).  Never hand-edit them; subclass `CachedApi` to override a cache.  Commit the output.
3. Use the new calls and caches from the app.

Versions come from the stack catalog: `create("lk") { from("com.lightningkite:stack-catalog:<version>") }`, then
`lk.lightningserver.client` in `apps` and `lk.lightningserver.server.client.utils` in `server`.  Libraries are on
epoch 1 (module versions `1000.x`); take the catalog version from the project, don't guess one.

## Server side: what the client needs

```kotlin
object Server : ServerBuilder() {
    val database = setting("database", Database.Settings())
    val cache = setting("cache", Cache.Settings())

    // One `module` per model.  `include`-ing two models into one object silently drops one from the SDK.
    val todos = path.path("todos") module TodoEndpoints

    // /meta/bulk (BulkFetcher batching), /meta/kschema (admin panel).  Must be mounted at "meta".
    val meta = path.path("meta") module MetaEndpoints("com.example", database, cache)

    // BulkFetcher multiplexes every live query over one socket at `?path=/multiplex`.
    val multiplex = path.path("multiplex") bind MultiplexWebSocketHandler()
    val socketRoot = path bind QueryParamWebSocketHandler()
}

object TodoEndpoints : ServerBuilder() {
    val info = Server.database.modelInfo(
        auth = UserAuth.require(),
        tableName = "Todo",
        permissions = { ModelPermissions(read = Condition<Todo> { it.owner eq auth.id }, /* ... */) },
    )
    // `+ ModelRestUpdatesWebSocket` makes ModelCache subscribe instead of polling.
    // Needs: import com.lightningkite.lightningserver.typed.ModelRestEndpointsAndUpdatesWebSocket.Companion.plus
    val rest = path include ModelRestEndpoints(info) + ModelRestUpdatesWebSocket(info)
}
```

Uploads: mount `GlobalUploadEndpoints(...)` (`UploadEarlyEndpoint` is a deprecated alias).  The SDK exposes it as a
`ClientFileUploadEndpoints`; on the client, `fileReference.toServerFile(api.<thatModule>)` uploads and returns the
`ServerFile`.

SDK generation, as a server CLI command (no settings, database or network needed):

```kotlin
fun sdk() {
    val out = KFile("apps/src/commonMain/kotlin/com/example/sdk")
    FetcherSdk("com.example.sdk").writeUsingDefaultSettings(Server, out)   // Api.kt, LiveApi.kt
    CachingSdk("com.example.sdk").writeUsingDefaultSettings(Server, out)   // CachedApi.kt
}
```

## Client side: the core pattern

```kotlin
val api = LiveApi(BulkFetcher(httpBulk = "https://api.example.com/meta/bulk", wsMultiplex = "wss://api.example.com?path=/multiplex"))

class UserSession(val api: Api, val userId: Uuid) : CachedApi(api)

val sessionToken = PersistentProperty<String?>("sessionToken", null)

val currentSession: Reactive<UserSession?> = rememberSuspending {
    val token = sessionToken() ?: return@rememberSuspending null
    val accessToken = api.userAuth.accessToken(token)                   // reused for 4 minutes
    val authApi = api.withMetadata { set("Authorization", accessToken()) }
    UserSession(authApi, authApi.userAuth.getSelf()._id)
}
```

Setting `sessionToken.value` (login or logout) rebuilds the session and every cache; screens reading
`currentSession()` follow.  The demo's `sdk/currentSession.kt` adds `currentSessionNotNull` and turning
"session terminated" errors into a sign-out.

```kotlin
@Routable("/todos")
class TodoListPage : Page {
    override fun ElementWriter.CanAddTheme.render() {
        val todos = remember { currentSessionNotNull().todos.list(Query { it.done eq false }) }
        expanding.recyclerView {
            children(items = todos) { todo ->            // com.lightningkite.lightningserver.db.children; pages on scroll
                card.text { ::content { todo().title } }
            }
        }
    }
}

val finish = Action("Done") { session.todos.item(id).modify(Modification { it.done assign true }) }
```

Install `context.exceptionHandlers.installLsError()` once at the app root so `LsErrorException`s show the server's
message.

## Rules that bite

- **Read collections through `ModelCache`** (`session.todos.list/item`), not `session.api.todo.query`.  Writes
  through the cache (`add`, `upsert`, `item(id).modify/set/delete`) update every open list and item at once.
- **Freshness is explicit.**  `maximumAge` (show cached data on arrival if younger) and `pullFrequency` (refetch
  while observed; default never).  With an update socket and `pullFrequency < 30.seconds`, the cache subscribes.
- **Deprecated on `ModelCache`:** `get(id)`, `query(q)`, `watch(...)`, the `limit = n` setter (they poll silently).
  Page with `list.limit(n)`; `skip` is rejected.
- **Edit a copy, send the diff.**  Seed a `Signal` from the cached item once, bind fields with
  `draft.lens(User.name)`, save with `modification(old, draft())` (`null` when unchanged).  Binding a form straight
  to the cache fights background refreshes.  See `model-cache.md#editing-a-record`.
- **Never hold a `CachedApi` across sessions**; build one per session as above.
- **`withHeaderCalculator` is deprecated**; use `withMetadata`.  `accessToken()` returns the bare token.
- **`AuthComponent` with several subject types:** pass `subjectType` explicitly (the default `.single()` throws).
- **Forms:** always `FormModule().apply { defaults() }`; wire `fileUpload` and `typeInfo` for files and
  `@References`.  `@AdminHidden` is presentation, not security: permissions live on the server.
- **Nothing loads until something listens**; a `reactive { }` or `await()` starts the fetch.
- **Generated names come from the server.**  Model caches are pluralized serial names (`Todo` -> `todos`); two
  endpoints with one path and different methods become overloads.  Rename on the server.
- **KSP copies imports into generated files**, so a wildcard `import kotlin.time.*` in a model file makes `Instant`
  ambiguous in the generated code.  Import `kotlin.time.Instant` and `kotlin.time.Clock` by name.
- **Capitalized builders:** `Condition { }`, `Modification { }`; lowercase `condition`/`modification { }` are
  deprecated (`modification(old, new)`, the diff function, is not).

## Testing

- Cache logic: `ClientModelRestEndpointsPlusUpdatesWebSocketMock` behind a real `ModelCache`, under a virtual clock
  (`ClockContextElement`).  Screens typed against `ModelCacheLike`: `MockModelCollection`.
- Server endpoints: `Server.test { }` with a RAM database (lightning-server skill).
- Whole stack in one JVM: the starter's `integration-tests` module (`TestRunnerFetcher` + KiteUI `uiTest`).

Details and gotchas: `docs/testing.md`.
