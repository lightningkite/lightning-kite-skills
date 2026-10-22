---
name: service-abstractions-1.4-migration
description: Use when upgrading a project to Service Abstractions 1.4 (and the Lightning Server 5.4 / LS-KiteUI versions built on it). Lists every deprecation and removal in 1.4 — the DataClassPath → Optic rename, top-level `User_email` fields becoming `User.email`, lowercase condition/modification builders, removed Condition/Modification types, data-shared serializer changes — with the replacement for each and a procedure for migrating a repo.
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

1. Bump `serviceAbstractions` (and `lightningServer` / `lightningServerKiteui` if used) in `gradle/libs.versions.toml`.
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
- **LS-KiteUI `lensPath` → `lens`**: bind through a path with `draft.lens(User.address.city)` (`com.lightningkite.serialization.lens`). A `Lens` path gives a non-null `MutableReactive<T>`; an `Optic` path gives `MutableReactive<T?>`, and writing `null` through a non-nullable target is ignored. It keeps the receiver's kind: `MutableReactiveValue`, `MutableValidated`, `MutableValidatedValue`, `ReactiveValue` and `Reactive` each get their own type back. `lensPath(path)` is deprecated with a `ReplaceWith`. The lambda form `lensPath { it.address.city }` is deprecated with no `lens` equivalent (`lens { … }` is the reactive library's read-only getter lens); it only accepts lambdas that return a `Lens`, so paths ending in `notNull`, `asType` or `elements` must be passed directly.
- **LS-KiteUI `ensureTotal`** and `SortPart` take fields directly: `SortPart(User._id)`.

## Mechanical-rewrite tips

- Generated-field renames (`User_email` → `User.email`) need the imports fixed in the same pass, or files in other packages lose the field.
- Most renames are safe with `sed -E` on word boundaries (`\bDataClassPath\b` → `Optic`, `\bSerializableProperty\b` → `Field`, `\bserializableProperties\b` → `fields`). Do the specific names (`DataClassPathPartial`, `DataClassPathSelf`, …) before `DataClassPath`.
- `DataClassPathAccess(a, b)` needs a paren-aware rewrite to `a + b`; when `a` is `DataClassPathSelf(…)`, the result is just `b`.
- Capitalize builder calls only where they're calls, not declarations, and leave `modification(old, new)` alone: that's `lightningdb`'s diff function, not the builder.
- Position-exact fixes: warnings are `w: file://PATH:LINE:COL '<signature>' is deprecated`, so a script can rewrite exactly the reported token.
- Check line endings before scripted edits: some checkouts have CRLF working files over LF in git; normalize files you touch back to what git stores, or diffs show every line changed.
