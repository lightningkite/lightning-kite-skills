---
name: KiteUI Development
description: This skill should be used when the user asks about KiteUI, Kotlin Multiplatform UI development, or mentions KiteUI-specific components and patterns
version: 2.1.0
---

# KiteUI Development Skill

KiteUI is a Kotlin Multiplatform UI framework using native view components and fine-grained reactivity (inspired by Solid.js).

## Primary References

**Always check these first for full examples:**
- `~/Projects/kiteui/CLAUDE.md` - Build commands, project structure, architecture
- `~/Projects/kiteui/GoodKiteuiCode.md` - Component patterns, full examples
- `~/Projects/kiteui/example-app/` - Working code examples

## Topic Documentation

This skill folder contains detailed documentation on specific topics:

| File | Topics Covered |
|------|----------------|
| [layout.md](layout.md) | Containers (col, row, frame), modifiers, CSS equivalents, scrolling, sizing |
| [components.md](components.md) | Text, buttons, inputs, checkboxes, radio buttons, icons, images, reusable widgets |
| [reactivity.md](reactivity.md) | Signal, remember, rememberSuspending, reactiveScope, forEach, bindings, lens extensions |
| [navigation.md](navigation.md) | Pages, @Routable, pageNavigator, links, URL parameters |
| [theming.md](theming.md) | Semantics (important, danger), custom themes, dynamic theming |
| [forms.md](forms.md) | Form patterns, field validation, local vs server validation |
| [dialogs.md](dialogs.md) | Toast, alert, confirm, custom dialog, bottom sheet, menus |
| [model-cache.md](model-cache.md) | Lightning Server caching, queries, modifications, server-side search |
| [advanced-patterns.md](advanced-patterns.md) | Keyboard shortcuts, drag-drop, dual-pane navigation, recyclerView |
| [error-handling.md](error-handling.md) | ExceptionHandler, ExceptionToMessage, automatic error display |
| [testing.md](testing.md) | Frontend config, SDK regeneration, browser testing, troubleshooting |

## Quick Reference

### V7 vs V6 Syntax (CRITICAL)

**KiteUI v7 uses dot notation (`.`)**. The dash operator (`-`) is **v6 only**.

```kotlin
// ✅ V7 - Dot notation
expanding.scrolling.card.col { }
important.button { text("Save") }

// ❌ V6 - Dash notation (DO NOT USE in v7)
expanding - scrolling - card - col { }
```

### Essential Patterns

```kotlin
// Layout
col { }                              // Vertical stack
row { }                              // Horizontal stack
frame { centered.text("Overlay") }   // Z-stack with positioning
expanding.scrolling.col { }          // Scrollable, fills space

// Reactivity
val count = Signal(0)                // Mutable state
val doubled = remember { count() * 2 } // Computed value
text { ::content { "Count: ${count()}" } } // Reactive binding
textInput { content bind email }     // Two-way binding

// Components
button { text("Click"); onClick { } }
button { text("Save"); action = Action("Save") { /* async */ } }
important.button { }                 // Themed
radioToggleButton { checked bind selected.equalTo(0) }

// Conditional visibility
shownWhen { showAdvanced() }.card.col { }

// Lists
forEach(items) { item -> text(item) }
```

### Critical Rules

1. **Nothing scrolls without `scrolling` or `scrollingHorizontally`**
2. **reactiveScope adds views on every rerun** - use `clearChildren()` first, or prefer `shownWhen`/`forEach`
3. **Theme switches create backgrounds** - apply to containers, not elements
4. **Use server-side filtering** - never client-side `.filter()` on ModelCache
5. **Always use ModelCache** for Lightning Server APIs

### Common Imports

```kotlin
import com.lightningkite.reactive.core.*
import com.lightningkite.reactive.context.*
import com.lightningkite.reactive.extensions.*
import com.lightningkite.kiteui.views.*
import com.lightningkite.kiteui.views.direct.*
import com.lightningkite.kiteui.views.l2.*
import com.lightningkite.kiteui.navigation.*
import com.lightningkite.lightningdb.*
import kotlinx.coroutines.launch
```

## Resources

- **Live Example**: https://kiteui.cs.lightningkite.com/
- **Maven**: https://lightningkite-maven.s3.us-west-2.amazonaws.com
