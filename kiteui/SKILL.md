---
name: KiteUI Development
description: This skill should be used when you are using KiteUI.
version: 3.0.0
---

# KiteUI Development Skill

KiteUI is a Kotlin Multiplatform UI framework using native view components and fine-grained reactivity (inspired by Solid.js).

**🔑 KEY CONCEPT: `render()` runs ONCE, not on every state change (unlike React).** Using `launch` in render is fine for one-time setup. Only reactive bindings (`::content { }`, `reactive { }`) re-execute when signals change.

## Agent Instructions

**Before answering complex questions, READ the relevant sub-file:**
- Layout/sizing/scrolling → [layout.md](layout.md)
- Signals/reactive/forEach → [reactivity.md](reactivity.md)
- ModelCache/server queries → [model-cache.md](model-cache.md)
- Text/buttons/inputs/icons → [components.md](components.md)
- Form validation patterns → [forms.md](forms.md)
- Pages/@Routable/navigation → [navigation.md](navigation.md)
- Toast/dialog/bottomSheet → [dialogs.md](dialogs.md)
- Semantic themes/dynamicTheme → [theming.md](theming.md)
- ExceptionHandler/Actions → [error-handling.md](error-handling.md)
- Setup/SDK regen/browser testing → [testing.md](testing.md)
- Keyboard shortcuts/drag-drop/recyclerView → [advanced-patterns.md](advanced-patterns.md)

---

## General Tips

- `scrolling` modifier makes views scroll vertically; will clip content otherwise
- `onClick {}`'s lambda is already suspending; no need to launch
- Avoid creating components unless significantly useful; layers of abstraction have cost
- Avoid custom spacing with `gap = x` - default spacing almost always looks good already
- 

## Using KiteUI with Lightning Server

- `./gradlew :server:generateSdk` will regenerate the SDK from the server definition
- Use ModelCache for CRUD, direct API for actions
```kotlin
// ❌ WRONG for data display - bypasses caching, no reactivity
val users = session.api.user.query(Query(...))

// ✅ CORRECT for CRUD - cached, reactive, auto-updates across all views
val users = remember { session.users.list(Query(...))() }

// ✅ CORRECT for non-CRUD actions (no caching needed)
session.api.door.unlock(doorId)
session.api.email.send(emailRequest)
```

- Prefer using server-side filtering

```kotlin
// ❌ WRONG - loads ALL data then filters client-side
val filtered = remember { allUsers().filter { it.name.contains(query()) } }

// ✅ CORRECT - server filters, only matching records sent
val filtered = remember {
    session.users.list(Query(condition {
        it.name.contains(query(), ignoreCase = true)
    }))()
}
```

### ModelCache (Lightning Server)

```kotlin
// Setup: wrap endpoints in CachedApi
class UserSession(val api: Api) : CachedApi(api) { }

// Individual item (reactive)
val user = remember { session.users[userId]() }
text { ::content { user()?.name ?: "Loading..." } }

// Query (reactive list)
val activeUsers = remember {
    session.users.list(Query(condition { it.active eq true }))()
}
forEach(activeUsers) { user -> text { ::content { user().name } } }

// Modify (updates all views automatically)
launch {
    session.users[userId].modify(modification { it.name assign "New Name" })
}

// Search with debounce
val searchDebounced = searchQuery.debounce(500)
val results = remember {
    session.users.list(Query(condition {
        if (searchDebounced().isEmpty()) Condition.Always
        else it.name.contains(searchDebounced(), ignoreCase = true)
    }))()
}
```

## ⚠️ CRITICAL PITFALLS (Read First!)

### 1. V7 uses DOT notation, NOT dash
```kotlin
// ✅ V7 CORRECT
expanding.scrolling.card.col { }

// ❌ V6 WRONG - dash doesn't exist in v7
expanding - scrolling - card - col { }
```

### 3. reactive DUPLICATES views on rerun
```kotlin
// ❌ WRONG - adds new text view on every signal change!
reactive {
    text { content = userData()?.name ?: "Loading" }
}

// ✅ CORRECT - use shownWhen for conditional visibility
shownWhen { showAdvanced() }.card.col { advancedSettings() }

// ✅ CORRECT - use reactive binding for dynamic content
text { ::content { userData()?.name ?: "Loading..." } }

// ✅ CORRECT - if you MUST use reactive, ALWAYS clearChildren first
col {
    reactive {
        clearChildren()  // ⚠️ CRITICAL - must be first line
        items().forEach { item -> text(item.name) }
    }
}
```

### 4. clearChildren() clears SIBLINGS if not isolated
```kotlin
// ❌ WRONG - each reactive clears the parent col's children
col {
    h2("Projects")
    reactive { clearChildren(); /* ... */ }  // Clears h2 above!
    h2("Tasks")
    reactive { clearChildren(); /* ... */ }  // Clears everything above!
}

// ✅ CORRECT - wrap each reactive in its own container
col {
    h2("Projects")
    col { reactive { clearChildren(); /* ... */ } }  // Isolated
    h2("Tasks")
    col { reactive { clearChildren(); /* ... */ } }  // Isolated
}
```

### 7. Use labeled returns in reactive/launch
```kotlin
// ❌ WRONG - "return is prohibited here"
reactive { val item = signal() ?: return }

// ✅ CORRECT
reactive { val item = signal() ?: return@reactive }
launch { val session = currentSession.await() ?: return@launch }
```

### 8. Calculate derived values with `remember`, don't store them
```kotlin
// ❌ WRONG - storing derived value in Signal + manual sync
val firstName = Signal("John")
val lastName = Signal("Doe")
val fullName = Signal("")  // Unnecessary Signal

reactive {
    fullName.value = "${firstName()} ${lastName()}"  // Manual update
}

// ✅ CORRECT - calculate with remember (auto-recomputes, shows loading, propagates errors)
val firstName = Signal("John")
val lastName = Signal("Doe")
val fullName = remember { "${firstName()} ${lastName()}" }

// ✅ CORRECT - async derived values with rememberSuspending
val userId = Signal<String?>(null)
val userDetails = rememberSuspending {
    val id = userId() ?: return@rememberSuspending null
    session.users.get(id).await()  // Loading state shown automatically
}
```

### 10. Theme switches create backgrounds
```kotlin
// Creates background (switches from default to important)
important.button { text("Save") }

// ✅ Apply themes to containers, not individual elements
card.col {
    text("Title")
    text("Content")
}

// ❌ Avoid multiple theme switches
card.text("Title")
card.text("Content")  // Two separate cards!
```

---

## Recommended Imports - Use * imports (add to all KiteUI files)

```kotlin
import com.lightningkite.kiteui.*
import com.lightningkite.kiteui.models.*
import com.lightningkite.kiteui.navigation.*
import com.lightningkite.kiteui.reactive.*
import com.lightningkite.kiteui.views.*
import com.lightningkite.kiteui.views.direct.*
import com.lightningkite.kiteui.views.l2.*
import com.lightningkite.reactive.*
import com.lightningkite.reactive.context.*
import com.lightningkite.reactive.core.*
import com.lightningkite.reactive.extensions.*
import com.lightningkite.reactive.lensing.*
import com.lightningkite.reactive.lensing.validation.*
import com.lightningkite.serialization.*
import kotlinx.coroutines.*
```

---

## Layout

```kotlin
// Containers
col { }                    // Vertical stack (flex-direction: column)
row { }                    // Horizontal (flex-direction: row)
frame { }                  // Z-stack (position: relative with absolute children)
rowCollapsingToColumn(70.rem) { }  // Horizontal if screen larger than input, vertical otherwise.  Vertical mode ignores weights.

// Modifiers chain BEFORE container
expanding.scrolling.card.col { }

// Sizing
expanding.someView                  // flex: 1 (takes available space)
weight(2f).someView                 // flex: 2
sizeConstraints(width = 20.rem, height = 10.rem).someView
sizeConstraints(minWidth = 10.rem, maxWidth = 30.rem).someView

// Frame positioning
frame {
    centered.text("Center")
    atTop.text("Top edge")
    atBottomEnd.text("Bottom right corner")
}

// Responsive
rowCollapsingToColumn(70.rem) { /* row on wide, col on narrow */ }
scrollingHorizontally.row { /* horizontal scroll */ }
```

---

## Reactivity

- `Reactive<T>` is a watchable, changing value
- `MutableReactive<T>` is one that can be changed with '.set(x)' (suspending)
- `Signal<T>(startingValue)` is a concrete implementation that can be changed with `.value = x`
- `reactive {}` runs the given block as often as dependencies change
- `someReactive()` will retrieve the value of a reactive AND set the dependency
- Reactives already hold their own loading / error states; using `reactive {}` in a view will automatically show loading states in UI if it's still being calculated
- `remember {}` is a reactive value that is calculated from the given reactive block, automatically recalculated when a dependency changes

```kotlin
// Mutable state
val count = Signal(0)
count.value = 5
count.value++

// Computed (auto-updates when dependencies change)
val doubled = remember { count() * 2 }

// Async data loading (preferred over Signal + launch)
val user = rememberSuspending {
    val session = currentSession() ?: return@rememberSuspending null
    session.users.get(userId).await()
}

// Reactive text binding
text { ::content { "Count: ${count()}" } }

// Two-way binding - binds two MutableReactive<T>
textInput { content bind email }

// Conditional visibility (PREFERRED over reactive creation / destruction of views)
shownWhen { showAdvanced() }.card.col { advancedSettings() }

// Reactive list rendering
val items = Signal(listOf("A", "B", "C"))
col {
    forEachById(items, id = { it } /*used to distinguish rows*/) { item: Reactive<String> ->
        card.text { ::content { item() } }
    }
}
recyclerView {  // handles its own scrolling, needs a size controlled by the outside.  Similar to Android's RecyclerView.
    children(items, id = { it } /*used to distinguish rows*/) { item: Reactive<String> ->
        card.text { ::content { item() } }
    }
}

// Reactive lens extensions
radioButton { checked bind selected.equalTo(1) }  // Radio groups
checkbox { checked bind tags.contains("featured") }  // Set membership
textInput { content bind nullableString.nullToBlank() }  // Null handling
numberInput { content bind ageStr.asInt() }  // String↔Number
```

---

## Components

```kotlin
// Text
h1("Heading"); h2("Subheading"); text("Body"); subtext("Muted")

// Buttons
button {
    text("Click")
    onClick { doSomething() }
}

// Button with async action (shows loading, handles errors automatically)
button {
    text("Save")
    action = Action("Save") {
        api.save(data())
        toast("Saved!")
    }
}

// Themed buttons
important.button { text("Primary") }
danger.button { text("Delete") }

// Inputs
textInput {
    hint = "Email"
    keyboardHints = KeyboardHints.email  // Don't forget this!  You need to tell it what kind of keyboard to use.
    content bind email
}
textArea {
    keyboardHints = KeyboardHints.email  // Don't forget this!  You need to tell it what kind of keyboard to use.
    content bind notes 
}

// Keyboard hint options
KeyboardHints.paragraph
KeyboardHints.title
KeyboardHints.id
KeyboardHints.integer
KeyboardHints.integerWithNegative
KeyboardHints.decimal
KeyboardHints.decimalWithNegative
KeyboardHints.phone
KeyboardHints.email
KeyboardHints.password
KeyboardHints.newPassword
KeyboardHints.oneTimeCode

// Selection
checkbox { checked bind isEnabled }
switch { checked bind isEnabled }
radioToggleButton { checked bind selected.equalTo(0) }
select { bind(selectedValue, options) { it } }

// Icons (from Material Design paths, though a limited subset)
icon(Icon.home, "Home")
icon { source = AppIcons.custom; description = "Custom" }
icon(Icon.home.copy(width = 3.rem, height = 3.rem), "Home")  // Huge icon
```

---

## Navigation

```kotlin
// Page definition
@Routable("users/{userId}")
class UserPage(val userId: String) : Page {
    override fun ViewWriter.render() {
        col { h1("User: $userId") }
    }
}

// Navigation
pageNavigator.navigate(UserPage("123"))
pageNavigator.goBack()
pageNavigator.replace(LoginPage)

// Links
link { text("Settings"); to = { SettingsPage } }
externalLink { text("Docs"); to = "https://example.com" }

// URL query parameters (persisted in URL)
@QueryParameter val searchQuery = Signal("")
```

---

## Dialogs

```kotlin
// Toast
toast("Success!")

// Confirm
val confirmed = confirm("Delete item?")
if (confirmed) deleteItem()

// Custom dialog
dialog { close ->
    card.col {
    card.col {
        h2("Title")
        text("Content")
        button { text("OK"); onClick { close() } }
    }
}

// Bottom sheet
openBottomSheet {
    col {
        h3 { content = "Options" }
        button { text("Option 1"); onClick { dismissBackground() } }
    }
}

// Destructive confirmation
confirmDanger("Delete", "Cannot be undone") { api.delete(id) }
```

---

## Theming

```kotlin
// Semantic modifiers
important.button { }  // Primary action
danger.button { }     // Destructive
warning.text("!")     // Warning
card.col { }          // Card background

// Make a field
field("Label") { 
    // fieldTheme automatically applied
    textInput { /*...*/ }
}

// Dynamic theme based on state
link {
    dynamicTheme {
        if (isSelected()) SelectedSemantic else null
    }
    text("Item")
}
```

---

## Error Handling

Actions automatically catch and display errors:

```kotlin
button {
    action = Action("Save") {
        // Errors thrown here show in dialog automatically
        api.save(data())
        // Custom error
        throw PlainTextException("Custom message", "Title")
    }
}

// Custom exception handler for a view tree
col {
    this += ExceptionToMessage<NetworkException>(priority = 5f) {
        ExceptionMessage(
            title = "Connection Error",
            body = "Check your internet connection."
        )
    }
    // Children inherit this handler
}
```

---

## Advanced Patterns

```kotlin
// Keyboard shortcuts
onKeyCode(keyCode { shortcut + it.letter('s') }) { saveAction.startAction(this) }

// Permission-based visibility
shownWhen { session().role != UserRole.Guest }.button { text("Admin") }

// Animated transitions
swapView(remember { if (advanced()) "adv" else "simple" }) { mode ->
    when (mode) { "adv" -> advancedUI(); "simple" -> simpleUI() }
}
```

---

## Resources

- **Live Example**: https://kiteui.cs.lightningkite.com/
- **Maven**: https://lightningkite-maven.s3.us-west-2.amazonaws.com
