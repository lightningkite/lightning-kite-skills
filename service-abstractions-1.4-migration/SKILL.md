---
name: service-abstractions-1.4-migration
description: Use when upgrading a project to Service Abstractions 1.4 (and the Lightning Server 5.4 / LS-KiteUI versions built on it). Lists every deprecation and removal in 1.4 — the DataClassPath → Optic rename, top-level `User_email` fields becoming `User.email`, lowercase condition/modification builders, removed Condition/Modification types, data-shared serializer changes, `withHeaderCalculator` → `withMetadata` — with the replacement for each and a procedure for migrating a repo.
version: 1.0.0
---

# Migrating to Service Abstractions 1.4

1.4 replaces `DataClassPath` with **optics** (`Optic`, `Lens`, `Field` in `com.lightningkite.services.database.optics`), renames the builders to match Kotlin conventions, and trims the Condition/Modification vocabulary. Most renames keep a `@Deprecated` alias with a `ReplaceWith`, so old code still compiles; removed types do not.

The biggest idea change: **generated fields are paths**. `User.age` is a `Field<User, Int>`, which is a `Lens`, which is an `Optic`. You no longer need `User.path.age` or a `condition<User> { it.age ... }` lambda just to get a path:

```kotlin
// 1.3
table.find(condition<User> { it.age gte 18 })
val city = User.path.address.notNull.city

// 1.4
table.find(User.age gte 18)
val city = User.address.notNull.city          // Optic<User, String>
val name = User.name                           // Lens<User, String> (Field)
```

## Procedure

1. Bump `serviceAbstractions` (and `lightningServer` / `lightningServerKiteui` if used) in `gradle/libs.versions.toml`. Going straight to epoch 1 (`1000.x`)? Import the stack catalog instead (`~/Projects/service-abstractions/docs/index.md#installing`) and also apply "Epoch 1" below.
2. Delete stale generated code, since KSP caches by a hash of the models, not of the processor: `rm -rf */build/generated/ksp`.
3. Compile everything (`./gradlew compileTestKotlinJvm compileTestKotlin compileKotlinJs --continue`). Fix **errors** first — they are the removed APIs below.
4. Fix **deprecation warnings** using the tables below. Gradle only re-prints warnings for tasks that actually run, so do a `clean` before the final sweep.
5. Grep for leftovers the compiler can't flag: serialized names in strings, docs, and the `.md` files in the repo.

## Imports

Optic types and helpers moved to `com.lightningkite.services.database.optics`. A file that imports only `com.lightningkite.services.database.*` will fail with errors like `Unresolved reference 'notNull' on receiver of type 'Lens<…>'`.

```kotlin
import com.lightningkite.services.database.*
import com.lightningkite.services.database.optics.*   // add this
```

Things that live in `optics` now: `Optic`, `AnyOptic`, `Lens`, `IdentityLens`, `Field`, `fields`, `notNull`, `elements`, `asType`, `plus`, `NotNullOptic`, `ComposedOptic`, `OpticOfType`, `ListElementsOptic`, `SetElementsOptic`, `AnyOpticSerializer`, `OpticSerializer`, `coerceToOptic`, `raw`/`meters`/… value-class paths.

**Trap:** a wildcard `optics.*` import shadows any local class named `Field` (forms code often has one). Rename the local class, or import the optics names explicitly in that file.

Explicit imports of the old lowercase builders must change too, or the call sites stop resolving:

| Old import | New import |
|---|---|
| `com.lightningkite.services.database.condition` | `com.lightningkite.services.database.Condition` |
| `com.lightningkite.services.database.modification` | `com.lightningkite.services.database.Modification` |
| `com.lightningkite.services.database.notNull` | `com.lightningkite.services.database.optics.notNull` |
| `com.lightningkite.services.database.path` | `com.lightningkite.services.database.optics.Lens` |
| `com.lightningkite.services.data.GenerateDataClassPaths` | `com.lightningkite.services.data.Queryable` |

## Deprecated renames (still compile, with ReplaceWith)

### Types

| 1.3 | 1.4 |
|---|---|
| `DataClassPath<K, V>` | `Optic<K, V>` |
| `DataClassPathPartial<K>` | `AnyOptic<K>` |
| `DataClassPathSelf<K>` | `IdentityLens<K>` |
| `DataClassPathAccess<K, M, V>` | `ComposedOptic<K, M, V>` |
| `DataClassPathNotNull<K, V>` | `NotNullOptic<K, V>` |
| `DataClassPathOfType<K, T, V>` | `OpticOfType<K, T, V>` |
| `DataClassPathList<K, V>` | `ListElementsOptic<K, V>` |
| `DataClassPathSet<K, V>` | `SetElementsOptic<K, V>` |
| `DataClassPathSerializer<T>` | `AnyOpticSerializer<T>` |
| `DataClassPathWithValue<A, V>` | `OpticWithValue<A, V>` |
| `SerializableProperty<A, B>` | `Field<A, B>` |

### Functions and properties

| 1.3 | 1.4 |
|---|---|
| `condition<T> { … }` | `Condition<T> { … }` |
| `condition(true)` | `Condition(true)` — no longer generic; returns `Condition<Any?>` (assignable to any `Condition<T>`) |
| `modification<T> { … }` | `Modification<T> { … }` |
| `modification(path) { … }` | `Modification(path) { … }` |
| `path<T>()` | `Lens<T>()` |
| `path(serializer)` | `IdentityLens(serializer)` |
| `User.path` (generated) | `Lens<User>()`, or usually nothing: `User.path.age` → `User.age` |
| `User.path(a, b)` (generated, generic models) | `IdentityLens(User.serializer(a, b))` |
| `it.always` / `it.never` | `it.always()` / `it.never()` (or `Condition.Always` / `Condition.Never`) |
| `DataClassPathAccess(a, b)` | `a + b` (and `IdentityLens(s) + field` is just `field`) |
| `path[field]` | `path + field` |
| `serializer.serializableProperties` | `serializer.fields` |
| `optic.properties` | `optic.fields` |
| `field.inline` | `field.isInline` |
| `field.setCopy(receiver, value)` | `field.set(receiver, value)` |
| `optic.getAny(model)` | `optic.get(model)` |
| `optic.setAny(model, value)` (now an error) | `(optic.coerceToOptic() as Optic<K, Any?>).set(model, value)` |
| `optic.serializerAny` | `optic.coerceToOptic().serializer` |
| `modification.forDataClassPath(path)` | `modification.forOptic(path)` |
| `modification.valueSetForDataClassPath(path)` | `modification.valueSetForOptic(path)` |
| `@Serializable @GenerateDataClassPaths` | `@Queryable` (applies both) |
| `table.insertMany(items)` | `table.insert(items)` |

### Changed without a deprecation

| 1.3 | 1.4 |
|---|---|
| `path.condition { … }` (map a condition onto a sub-path) | `path.mapCondition { … }` |
| `DataClassPathSerializer.inner` | `AnyOpticSerializer.root` |
| `Table.aggregate<N : Number?>(…, property: Optic<T, N>)` | `aggregate(…, property: Optic<T, out Number?>)` — same for `groupAggregate`; update overrides and casts |
| `SerializableProperty` was an open interface | `Field` is **sealed**. Code (often tests) that implemented it must use a real field; for runtime/kschema shapes use `Field.FromVirtualField(VirtualField(…), SerializationRegistry(…), mapOf())` |
| `notNull` on any path | `notNull` builds a `NotNullOptic`, whose `serializer` throws on a non-nullable target. Only apply it when `serializer.descriptor.isNullable` |

## Optic vs Lens

`Lens` paths always reach their target (`get` returns `B`); `Optic` paths may not (`get` returns `B?`). Fields compose into lenses; `notNull`, `asType`, and `elements` produce plain optics.

```kotlin
val a: Lens<User, String> = User.address.city     // field + field
val b: Optic<User, String> = User.backup.notNull.city
```

APIs downstream use this to type results: e.g. LS-KiteUI's `signal.lens(User.name)` is a `MutableReactive<String>`, while `signal.lens(User.backup.notNull.city)` is a `MutableReactive<String?>`.

## Removed (compile errors)

### Conditions

| Removed | Replacement |
|---|---|
| `Condition.ListAllElements`, `Condition.SetAllElements` | `Condition.CollectionAllElements` (`path.all { … }`) |
| `Condition.ListAnyElements`, `Condition.SetAnyElements` | `Condition.CollectionAnyElements` (`path.any { … }`) |
| `Condition.ListSizesEquals`, `Condition.SetSizesEquals` (`sizesEquals`) | none |
| `Condition.Exists` (`containsKey`), `Condition.OnKey` (`map[k] …`) | none — map fields are no longer queryable |
| `Condition.RawStringContains` (`contains` on an `IsRawString`) | `path.raw contains "x"` (`StringContains` on the `.raw` path) |
| `Condition.FullTextSearch` (`fullTextSearch`) | `Table.findByTextIndex(query, condition, skip, limit)` on the server; there is no condition form, so clients search string fields with `contains` instead |
| `GeoDistance(greaterThanKilometers, lessThanKilometers)` | `GeoDistance(greaterThan: Length, lessThan: Length)`; display with `.kilometers` |

Old serial names for `ListAllElements`/`SetAllElements`/`ListAnyElements`/`SetAnyElements` still decode.

### Vector search

`Table.findSimilar`/`findSimilarSparse`, `@VectorIndex`, `SparseEmbedding` and `VectorSearchParams` are gone. Embeddings no longer live on models: a `VectorIndex` from a `VectorDatabase` (`InMemoryDatabase`, `MongoDatabase` on Atlas, `PostgresDatabase` with pgvector) holds `VectorIndexEntry(_id, embedding)` per row, and `table.vectorIndexed(index, VectorProjection(condition, embed, reembedWhen))` keeps it in step. `index.search(query, limit)` returns `ScoredResult<ID>`s (the ID is `.model`) with no filtering or score threshold; choose the indexed rows with the projection's `condition` instead, then load the models by ID. Backfill existing rows with `index.rebuild(table, projection)`. See `~/Projects/service-abstractions/docs/database.md#vector-search`.

### Modifications

| Removed | Replacement |
|---|---|
| `Modification.AppendString`, `Modification.AppendRawString` (`+=` on strings) | `assign` the new value |
| `Modification.ListDropFirst/ListDropLast`, `SetDropFirst/SetDropLast` | `assign` the new list/set |
| `Modification.Combine` (`map += …`), `Modification.RemoveKeys`, `modifyByKey` | `assign` the whole map |

Code that enumerates these types (form renderers, `friendly()` text, condition-implication logic, mocks) needs its cases deleted or merged into the `Collection*` versions. Map-key tests go away entirely.

### data-shared

| Removed / changed | Replacement |
|---|---|
| `TrimmedStringSerializer`, `CaselessStringSerializer`, `TrimmedCaselessStringSerializer`, `EmailAddressSerializer`, `PhoneNumberSerializer` | `TrimmedString.serializer()` etc. Serial names are unchanged |
| Decoding un-normalized strings (`" Bob@X.com "`) normalized them | now throws `SerializationException`; normalize with `toEmailAddress()`, `toPhoneNumber()`, `trimmed()`, `caseless()`, `trimmedCaseless()` |
| `EmailAddress("…")`, `PhoneNumber("…")`, `TrimmedString("…")`… constructors (deprecated) | the `String.to…()` / `.trimmed()` functions; constructors throw on un-normalized input |

New: value classes have paths to their wrapped value — `.raw` (`IsRawString`, `UuidV7`), `.meters` (`Length`), `.bytes` (`DataSize`), `.kilograms`, `.celsius`, etc. — so they support `gt`, `contains`, `coerceAtMost`, …

## Generated code (KSP)

- Each field is `public val User.Companion.age: Field<User, Int>`, plus `Optic`/`Lens` extensions so `User.address.city` chains.
- **Top-level fields are gone.** 1.3 generated each field as a top-level value joined by an underscore (`public val User_email: SerializableProperty<User, String>`) plus `User__properties`. Those no longer exist and have no deprecated alias, so every use is a compile error:

  | 1.3 | 1.4 |
  |---|---|
  | `User_email` | `User.email` |
  | `User__properties` | `User.fields` |
  | `import com.example.User_email` | `import com.example.email` (only needed outside the model's package) |
  | `it[User_email]`, `User.path[User_email]` | `it.email`, `User.email` |

  The companion extensions are top-level declarations in the model's package, so a file in another package needs to import them by field name (or `import com.example.*`). One `import com.example.email` covers the `email` field of every model in that package.

  Rewrite: `\b([A-Z]\w+)_([a-z]\w*)\b` → `$1.$2` catches the uses (skip `_id`-style names that aren't fields), then change the imports and de-duplicate them. Generic models still get serializer extensions (`Box.serializer(T.serializer()).fieldValue`); those keep their names.
- `User.Companion.fields` lists all fields; it is skipped when the model has its own property named `fields`. (Before `1.4.0-prerelease-73-832ca291` a model with a `fields` property failed to compile with "Conflicting declarations" in `ModelFields*.kt`.)
- `User.Companion.path` is still generated but deprecated.
- **From 1000.0.0 (epoch 1), multiplatform modules need task wiring.** Only `kspCommonMainKotlinMetadata` writes commonMain's fields; `kspKotlinJvm` and the other target tasks no longer do. A module that adds the processor only to `kspJvm`, or lacks the stanza below, fails with "The generated sources for commonMain are missing" or with every `User.email` unresolved and an empty `build/generated/ksp/common/commonMain/kotlin`. Add the processor to every `ksp*` configuration (so `kspCommonMainMetadata` has it) and:

  ```kotlin
  tasks.matching { (it.name.startsWith("ksp") || it.name.startsWith("compile")) && it.name != "kspCommonMainKotlinMetadata" }
      .configureEach { dependsOn("kspCommonMainKotlinMetadata") }
  ```

  JVM-only modules (`ksp(...)` with `kotlin("jvm")`) need nothing. Details: "Build setup" in `~/Projects/service-abstractions/docs/database-queries.md`.

## Lightning Server 5.4 / LS-KiteUI alongside 1.4

These ship together with 1.4 and usually show up in the same migration:

- **`SDK.Format.write`** takes `context(server: Engine)` instead of `context(ServerRuntime)`; custom formats and their helpers must switch.
- **`TestRunner` is an `Engine`, not a `ServerRuntime`.** Inside endpoint handlers nothing changes, but test code that does server work directly — sending to a topic, touching a table through `info.table()`, reading `serverRuntime`, calling a `context(ServerRuntime)` helper — no longer has a runtime in scope and fails with missing-context errors. Wrap that work in `execute { }`, which runs it as its own execution with interceptors applied:

  ```kotlin
  // 5.3
  Server.testBlocking(settings = { database set Database.Settings("ram") }) {
      chatTopic.send("Pong.")
      val user = users.info.table().get(id)
  }

  // 5.4
  Server.testBlocking(settings = { database set Database.Settings("ram") }) {
      execute { chatTopic.send("Pong.") }
      val user = execute { users.info.table().get(id) }
  }
  ```

  (`test { }` works the same, but its block isn't `suspend`, so it needs `runBlocking` around suspending calls.)

  `execute` returns the block's value, so it can wrap a single expression.
- **TOTP proofs** moved to their own artifact: add `com.lightningkite.lightningserver:sessions-totp` if you use `TimeBasedOTPProofEndpoints`.
- The TS SDK still names optics `DataClassPath` / `DataClassPathPartial` (it maps the new serial names), so generated TypeScript is unchanged.
- **LS-KiteUI `lensPath` → `lens`**: bind through a path with `draft.lens(User.address.city)` (`import com.lightningkite.optics.lens`). A `Lens` path gives a non-null `MutableReactive<T>`; an `Optic` path gives `MutableReactive<T?>`, and writing `null` through a non-nullable target is ignored. It keeps the receiver's kind: `MutableReactiveValue`, `MutableValidated`, `MutableValidatedValue`, `ReactiveValue` and `Reactive` each get their own type back. A mutable receiver holding a nullable model (`Signal<User?>`) can lens too and gives `T?`: reads are `null` while the model is `null`, and writes are dropped. Read-only nullable receivers (`Reactive<User?>`) have no `lens(path)`.
- **LS-KiteUI lens helpers moved to `com.lightningkite.optics`**: `lens`, `asString` used to live in `com.lightningkite.serialization`, with no alias left behind, so old imports fail with `Unresolved reference 'lens'`. Rewrite `import com.lightningkite.serialization.(lens|asString|withStringBuffer)` to `import com.lightningkite.optics.$1`. The deprecated `lensPath` overloads stay in `com.lightningkite.serialization`. `lensPath(path)` is deprecated with a `ReplaceWith`. The lambda form `lensPath { it.address.city }` is deprecated with no `lens` equivalent (`lens { … }` is the reactive library's read-only getter lens); it only accepts lambdas that return a `Lens`, so paths ending in `notNull`, `asType` or `elements` must be passed directly.
- **LS-KiteUI `ensureTotal`** and `SortPart` take fields directly: `SortPart(User._id)`.

- **Header calculators became `RequestMetadata`.** `Fetcher.withHeaderCalculator(suspend () -> List<Pair<String, String>>)` is deprecated in favour of `withMetadata(block: suspend RequestMetadata.() -> Unit)`, which edits a copy of the fetcher's existing metadata before every request instead of replacing it. Metadata goes out as headers over HTTP and as URL-encoded query parameters over WebSockets. `RequestMetadata` (`com.lightningkite.lightningserver.typed`) has `set`, `append`, `remove`, `get`, `getAll`, `has`, `clear`; names ignore case. Use `set` unless you really want a second value: `append("Authorization", …)` on an authenticated API sends two tokens and the server reads only the first.

  ```kotlin
  // 5.3
  val authApi = api.withHeaderCalculator(api.userAuth.accessToken(token, invalidateToken))
  val masked = api.withHeaderCalculator { listOf("X-Masquerade" to "User/$id") + accessToken() }
  val raw: String = api.userAuth.accessToken(token)().first().second

  // 5.4
  val accessToken = api.userAuth.accessToken(token, invalidateToken)   // now returns the bare token
  val authApi = api.withMetadata { set("Authorization", accessToken()) }
  val masked = authApi.withMetadata { set("X-Masquerade", "User/$id") }
  val raw: String = api.userAuth.accessToken(token)()
  ```

  Things that follow from it:
  - **`AuthClientEndpoints.accessToken(sessionToken, forceInvalidate, maxAge)` changed return type with no deprecation** (compile errors). It returns `AccessToken` (`suspend () -> String`), the bare token, not `suspend () -> List<Pair<String, String>>`. Every use needs one of the rewrites above: passed to `withHeaderCalculator(…)` → `withMetadata { set("Authorization", accessToken()) }`; `accessToken(t)().first().second` → `accessToken(t)()`; combined with other headers → several `set` calls in one `withMetadata`. `maxAge` (default 4 minutes) controls how long a token is reused. `LightningServerAuthentication.accessToken` is an `AccessToken` too.
  - **Anything implementing `Fetcher` must implement `withMetadata`** (compile error), usually a project's `TestRunnerFetcher`: store `metadata: suspend RequestMetadata.() -> Unit = {}`, implement `withMetadata(block) = TestRunnerFetcher(runtime) { metadata(); block() }`, and send `RequestMetadata().apply { metadata() }.toList()` as headers. Drop its `withHeaderCalculator` override.
  - `ConnectivityFetcher(…, calculator = …)` / `BulkFetcher(…, calculator = …)` are deprecated; pass `metadata = { set(…) }`. Name the argument: a trailing lambda can resolve to the deprecated `calculator` overload.
  - Regenerate the SDK. An old generated `Api`/`LiveApi` still compiles, with deprecation warnings.
  - The server now reads `X-Masquerade` from the query too, so masquerading works over WebSockets. Before, it was silently ignored there.
- **KiteUI `HttpHeaders.delete` → `remove`** (deprecated, with `ReplaceWith`).

- **Full-text search moved from a condition to its own query.** `Condition.FullTextSearch` / `it.fullTextSearch(s)` is gone, so a search can no longer be AND-ed into a `Condition`. Use LS-KiteUI's `MaybeTextIndexQuery` (`com.lightningkite.lightningserver.db`) and `ModelCache.listOrTextSearch`:

  ```kotlin
  // 1.3
  cache.list(Query(Condition.And(listOfNotNull(filter, search.takeUnless { it.isBlank() }?.let { c -> Condition { it.fullTextSearch(c) } })), orderBy, limit = 20), …)

  // 1.4: keep the search out of the condition; query = null means a plain filter query
  val query = MaybeTextIndexQuery(
      query = search.takeUnless { it.isBlank() },
      condition = filter,
      orderBy = orderBy,   // ignored when searching: results come back by relevance
      limit = 20,
  )
  val items = cache.listOrTextSearch(query, maximumAge, pullFrequency)   // Reactive<List<T>>
  ```

  Things that follow from it:
  - A `Query` becomes `MaybeTextIndexQuery.Filter`, a `TextIndexQuery` becomes `MaybeTextIndexQuery.Search`. Code that takes a per-search-string query lambda (pickers, autocompletes) should return `MaybeTextIndexQuery` instead of `Query`.
  - `listOrTextSearch` returns a `Reactive<List<T>>`. A filter query gives the cache's live `LimitReactiveList`; a text search skips the cache (`skipCache.textQuery`) and gives a plain reactive list that is *not* a `LimitReactiveList`, so it has no growable limit. UI built on that list (infinite scroll, `limit` bumps) must check `is LimitReactiveList` and treat the text-search case as a single fixed page.
  - Manual paging against `skipCache.query(Query(…, skip, limit))` has a text equivalent: `skipCache.textQuery(TextIndexQuery(search, condition, skip, limit))`, which returns `ScoredResult`s (`.model`).
  - Text queries ignore sort. Drop any sort that only existed to order search results.
  - Search strings that can't match a text index (a pure number looked up against a numeric id) should still become a normal condition on that field, with `query = null`. Some databases also forbid text search inside `$or`, so don't combine them.
  - Only `fullTextSearch` is affected. Search done with `contains` on string fields is still a normal condition.

- **Reactive `validateReactive` / `assertReactive` / `auditReactive` must be used.** They used to attach the check to the receiver in place, so a bare `x.validateReactive { … }` statement worked. They now return a new `MutableValidated` that carries the check, and the receiver is untouched. A statement-position call compiles with no warning and silently does nothing: no issue text, no gated writes.

  ```kotlin
  // 1.3 (worked), now a silent no-op
  val credits = course.lens(Course.usbeCredits).nullToZero()
  credits.validateReactive { … }

  // 1.4: validate where the value is declared, or chain it just before binding
  val credits = course.lens(Course.usbeCredits).nullToZero().validateReactive { … }
  ```

  Find them with `grep -rnE '^\s*\w+\.(validate|assert|audit)Reactive\b'` (a match at the start of a line is a discarded result), then move each onto the declaration of the value that gets bound or passed to `validate(...)` / `issueText(...)`. If the lambda reads values declared after the receiver, move the receiver's declaration down instead. A script that appends the call to "the preceding declaration" is wrong when other declarations sit in between (it attached two checks to one value and dropped the other); pair by name and review each diff.

## Epoch 1 (1000.0.0) on top of 1.4 / 5.4

Found moving an app from 1.4.0 / LS 5.4.0 to the stack catalog at 1000.0.0:

- **`modelInfo(...)` requires `tableName`.** The old default was the model's serial name after the last `.` and before any `<` (so the class name: `"Task"`, `"Notification"`, `"NotificationSendMethods"`). Pass exactly that, or existing data is orphaned.
- **Engines aren't a `ServerRuntime`.** Work a launcher did directly on the engine (`MigrateActions.runMigrations()` inside `KtorEngine.apply { }`) fails with "No context argument for ServerRuntime". Bind it as a `PreDeployTask` (`dependencies = { listOf(X.info.registration.preDeployTask) }`) and have the CLI call `runPreDeploy()`, or `runPreDeployTasksBlocking()` before `start()` for a local "prepare then serve". Tables' collections and indexes are prepared by pre-deploy tasks too, so a server that never runs them has no indexes.
- **Settings files need edits**, because every setting is constructed at startup: `"telemetry": {"url": "dev"}` has no handler (the default is `"noop"`; other schemes need `otel-jvm`), and an empty `"llm": ""` fails ("No handler"). A new setting without `optional = true` fails every existing settings file with "Missing keys".
- **Lightning Bot** (`com.lightningkite.lightningbot:*`, own catalog and bucket): `LLMChatEndpoints` → `Chat`, `McpServerEndpoints` → `McpServer`, `LLMTask` → `Agent.task`, `ChatScreen` → `chatView`, `LLMClientAndModel.Settings` → `LlmAccess.Settings` plus a separate `LlmModelId` setting (a legacy `bedrock://<model>?…` URL still parses; its model is ignored). Provider modules (`services:ai-bedrock`, `ai-openai`) must be added and `XLlmSettings.ensureRegistered()` called. Chat storage is new tables. See `~/Projects/lightning-bot/docs/guide.md`.
- **SDK**: `uploadEarlyEndpoint` → `globalUpload` (`getFileUploadUrl()`, then `verifyUpload(token)`).
- **KiteUI**: `dialogPageNavigator` and the second navigator of `appBase` are gone; open dialogs with `context.dialog { close -> … }`.
- KSP plugin must match the libraries' (2.3.13), `compileSdk = 37`.

## Mechanical-rewrite tips

- Generated-field renames (`User_email` → `User.email`) need the imports fixed in the same pass, or files in other packages lose the field.
- Most renames are safe with `sed -E` on word boundaries (`\bDataClassPath\b` → `Optic`, `\bSerializableProperty\b` → `Field`, `\bserializableProperties\b` → `fields`). Do the specific names (`DataClassPathPartial`, `DataClassPathSelf`, …) before `DataClassPath`.
- `DataClassPathAccess(a, b)` needs a paren-aware rewrite to `a + b`; when `a` is `DataClassPathSelf(…)`, the result is just `b`.
- Capitalize builder calls only where they're calls, not declarations, and leave `modification(old, new)` alone: that's `lightningdb`'s diff function, not the builder.
- Position-exact fixes: warnings are `w: file://PATH:LINE:COL '<signature>' is deprecated`, so a script can rewrite exactly the reported token.
- Check line endings before scripted edits: some checkouts have CRLF working files over LF in git; normalize files you touch back to what git stores, or diffs show every line changed.
