---
name: Model Design
description: This skill should be used when designing data models for Lightning Server / Kotlin applications. Covers domain modeling patterns, database schema design, and Lightning Kite conventions.
version: 1.0.0
---
<!-- by Claude -->

# Model Design Skill

This skill guides the design of data models for Lightning Server applications, based on patterns used across Lightning Kite projects.

## Core Philosophy

**Models are not just data bags.** They encode business rules, enforce invariants, and reflect the domain language. Good model design makes invalid states unrepresentable and derives computed state from stored facts.

---

## Critical Design Principles

### 1. Store Facts, Compute State (NO STATE ENUMS)

**This is the most important principle.** Never use status/state enums. Instead, store timestamps and facts from which state can be derived.

```kotlin
// ❌ BAD: State enum
enum class OrderStatus { Draft, Submitted, Paid, Shipped, Delivered, Cancelled }

data class Order(
    val _id: UUID,
    val status: OrderStatus,  // WRONG - backs you into a corner
)

// ✅ GOOD: Facts with timestamps
data class Order(
    override val _id: UUID = UUID.random(),
    val submitted: Instant? = null,
    val paid: Instant? = null,
    val shipped: Instant? = null,
    val delivered: Instant? = null,
    val cancelled: Instant? = null,
) : HasId<UUID> {
    // Compute "status" for display if needed
    val currentStatus: String get() = when {
        cancelled != null -> "Cancelled"
        delivered != null -> "Delivered"
        shipped != null -> "Shipped"
        paid != null -> "Paid"
        submitted != null -> "Submitted"
        else -> "Draft"
    }

    val isActive: Boolean get() = submitted != null && cancelled == null && delivered == null
}
```

**Why state enums are a trap:**
- Can't know *when* state changed
- States are mutually exclusive (but real life isn't: "submitted AND has counter offer")
- Adding new states breaks existing code and migrations
- Transition rules become complex state machines
- No audit trail

**Why facts/timestamps win:**
- You know exactly when each thing happened
- Multiple facts can be true simultaneously
- Adding new facts is purely additive
- The "current state" is computed, not stored
- Timestamps ARE the audit trail

### 2. Immutable Events vs Mutable Entities

Separate append-only event records from mutable entity state:

```kotlin
// Event/Transaction - IMMUTABLE, append-only
@Serializable
@GenerateDataClassPaths
data class Transaction(
    override val _id: UUID = UUID.random(),
    @Index @References(Account::class) val accountId: UUID,
    val type: TransactionType,
    val amount: Int,
    val balanceAfter: Int,
    val createdAt: Instant = now(),
    // NO modifiedAt - events are immutable
) : HasId<UUID>

// Entity - MUTABLE state
@Serializable
@GenerateDataClassPaths
data class Account(
    override val _id: UUID = UUID.random(),
    val balance: Int = 0,
    val createdAt: Instant = now(),
    val modifiedAt: Instant = now(),  // Updated on changes
) : HasId<UUID>
```

The event stream is the source of truth; entity state is a projection/cache.

### 3. Type Aliases for Domain Language

Make code read like the business domain:

```kotlin
typealias PriceInCents = Int
typealias EmailAddress = String
typealias MakeName = String
typealias VehicleColor = String
typealias Meters = Double

data class Vehicle(
    val price: PriceInCents,           // Clear intent
    val exteriorColor: VehicleColor,
    val make: MakeName,
)
```

### 4. Value Classes for Domain Concepts with Behavior

Business logic belongs in value objects:

```kotlin
@Serializable
@JvmInline
value class Temperature(val celsius: Double) : Comparable<Temperature> {
    val fahrenheit: Double get() = celsius * 9/5 + 32
    fun isBoiling() = celsius >= 100
    override fun compareTo(other: Temperature) = celsius.compareTo(other.celsius)

    companion object {
        fun fromFahrenheit(f: Double) = Temperature((f - 32) * 5/9)
    }
}

@Serializable
@JvmInline
value class Money(val cents: Int) {
    val dollars: Double get() = cents / 100.0
    operator fun plus(other: Money) = Money(cents + other.cents)
    operator fun minus(other: Money) = Money(cents - other.cents)
    fun format(): String = "$${dollars}"
}
```

### 5. Behavior Lives in Models

Models aren't just data containers - they encode business rules:

```kotlin
data class Promotion(
    override val _id: UUID = UUID.random(),
    val bonusPoints: Int,
    val config: PromotionConfig,
    val startsAt: Instant,
    val endsAt: Instant? = null,
) : HasId<UUID> {

    suspend fun qualifiesFor(customer: Customer, subtotal: Double): Boolean = when {
        config.cashThreshold != null -> subtotal >= config.cashThreshold
        config.birthday == true -> customer.birthday?.let {
            it.month == today.month && it.dayOfMonth == today.dayOfMonth
        } ?: false
        else -> false
    }

    val isActive: Boolean get() {
        val now = now()
        return now >= startsAt && (endsAt == null || now <= endsAt)
    }
}
```

---

## Model Structure Patterns

### Basic Model Template

```kotlin
@Serializable
@GenerateDataClassPaths
data class ModelName(
    override val _id: UUID = UUID.random(),
    // Required fields (no defaults)
    val requiredField: String,
    // Optional fields with sensible defaults
    val optionalField: String? = null,
    val listField: List<Item> = emptyList(),
    val setField: Set<UUID> = emptySet(),
    val flag: Boolean = false,
    val createdAt: Instant = now(),
) : HasId<UUID>
```

### ID Type Selection

| ID Type | Use Case | Example |
|---------|----------|---------|
| `UUID` | Default for internal entities | `User`, `Order`, `Vehicle` |
| `String` | External system IDs or semantic keys | `MerchantStore._id = "shop.myshopify.com"` |
| `String` | Human-readable composite keys | `Firmware._id = "$type-$version"` |
| `LocalDate` | Date-keyed singleton records | `DailyStats._id: LocalDate` (one per day) |
| Composite type | Relationship entities | `DealershipVehiclePair` for join tables |

### Composite ID Pattern (Relationship Entities)

When a relationship itself has data:

```kotlin
@Serializable
@GenerateDataClassPaths
data class DealershipVehiclePair(
    @References(Dealership::class) val dealership: UUID,
    @References(Vehicle::class) val vehicle: UUID,
) : Comparable<DealershipVehiclePair> {
    override fun compareTo(other: DealershipVehiclePair): Int =
        compareValuesBy(this, other, { it.dealership }, { it.vehicle })
}

@Serializable
@GenerateDataClassPaths
data class VehicleRelationship(
    override val _id: DealershipVehiclePair,  // Composite ID
    val favorite: Boolean = false,
    val autobid: Int? = null,
    val personalNotes: String = "",
) : HasId<DealershipVehiclePair>
```

---

## Relationship Patterns

### References (Foreign Keys)

```kotlin
// Single reference
@References(User::class) val createdBy: UUID

// Multiple references (Set)
@MultipleReferences(Tag::class) val tags: Set<UUID> = emptySet()

// Indexed reference (for frequent queries)
@Index @References(MerchantStore::class) val merchantStoreId: String
```

### Denormalization for Query Performance

Copy data from related entities to avoid joins:

```kotlin
@Serializable
@GenerateDataClassPaths
data class Lot(
    override val _id: UUID = UUID.random(),
    @References(AuctionDay::class) val auctionDay: UUID,

    // Denormalized copies - updated when source changes
    @Denormalized @References(Auction::class) val auction: UUID,
    @Denormalized @References(Venue::class) val venue: UUID,
    @Denormalized val auctionDate: LocalDate,
    @Denormalized val city: String? = null,
    @Denormalized val state: String? = null,
) : HasId<UUID>
```

### Projection Pattern (Lightweight Views)

Create summary models for list/search views:

```kotlin
// Full model with all details
@Serializable
@GenerateDataClassPaths
data class Vehicle(
    override val _id: UUID = UUID.random(),
    val vin: String,
    val make: String,
    val model: String,
    val year: Int,
    val description: String,
    val images: List<ServerFile> = emptyList(),
    val inspectionReport: InspectionReport? = null,
    // ... many more fields
) : HasId<UUID>

// Lightweight projection for lists
@Serializable
@GenerateDataClassPaths
data class ShortVehicle(
    override val _id: UUID,
    val vin: String,
    val make: String,
    val model: String,
    val year: Int,
) : HasId<UUID>

// Extension to create projection
fun Vehicle.short() = ShortVehicle(
    _id = _id,
    vin = vin,
    make = make,
    model = model,
    year = year,
)
```

---

## Configuration Patterns

### Discriminated Union (One-of-N Config)

When exactly one option should be selected:

```kotlin
@Serializable
@GenerateDataClassPaths
data class PromotionConfig(
    val cashThreshold: Double? = null,
    val returningCustomer: ReturningCustomerConfig? = null,
    val productQuantity: ProductQuantityConfig? = null,
    val birthday: Boolean? = null,
    val anniversary: Boolean? = null,
    // Exactly ONE of these should be non-null
)

@Serializable
@GenerateDataClassPaths
data class ReturningCustomerConfig(
    val timeFrameDays: Int,
)

@Serializable
@GenerateDataClassPaths
data class ProductQuantityConfig(
    val productId: String,
    val minQuantity: Int,
)
```

Validate in interceptCreate that exactly one is set.

### Explicit Settings (Not Generic Maps)

Prefer explicit typed fields over flexible maps:

```kotlin
// ❌ BAD: Generic map
data class User(
    val notificationSettings: Map<String, Boolean> = emptyMap()
)

// ✅ GOOD: Explicit fields
data class User(
    val notifyOrderShipped: NotificationSettings = NotificationSettings(),
    val notifyOrderDelivered: NotificationSettings = NotificationSettings(),
    val notifyPriceDrops: NotificationSettings = NotificationSettings(),
    val notifyNewArrivals: NotificationSettings = NotificationSettings(),
) {
    fun settingsFor(topic: NotificationTopic): NotificationSettings = when(topic) {
        NotificationTopic.OrderShipped -> notifyOrderShipped
        NotificationTopic.OrderDelivered -> notifyOrderDelivered
        // ...
    }
}

@Serializable
@GenerateDataClassPaths
data class NotificationSettings(
    val push: Boolean = true,
    val email: Boolean = false,
    val sms: Boolean = false,
)
```

---

## Embedded vs Top-Level Models

### Top-Level (Has own collection)
- Has `HasId<T>` interface
- Gets `@GenerateDataClassPaths`
- Queried independently
- Has its own lifecycle

### Embedded (Nested in other models)
- Has `@GenerateDataClassPaths` (for path access)
- Does NOT implement `HasId`
- Lives inside parent document
- Lifecycle tied to parent

```kotlin
// Top-level: Own collection
@Serializable
@GenerateDataClassPaths
data class Order(
    override val _id: UUID = UUID.random(),
    val items: List<OrderItem> = emptyList(),  // Embedded list
    val shippingAddress: Address,              // Embedded object
) : HasId<UUID>

// Embedded: Lives inside Order
@Serializable
@GenerateDataClassPaths
data class OrderItem(
    val productId: UUID,
    val quantity: Int,
    val priceAtPurchase: Int,
)

// Embedded: Reusable value object
@Serializable
@GenerateDataClassPaths
data class Address(
    val street: String,
    val city: String,
    val state: String,
    val zip: String,
    val country: String = "US",
)
```

---

## Multi-Tenancy Pattern

Scope all tenant data with a reference:

```kotlin
@Serializable
@GenerateDataClassPaths
data class Product(
    override val _id: UUID = UUID.random(),
    @Index @References(MerchantStore::class) val merchantStoreId: String,
    val name: String,
    val price: Int,
) : HasId<UUID>

// In permissions, always scope by tenant:
// condition { it.merchantStoreId eq currentTenantId }
```

---

## Companion Object Patterns

### Empty/Default Instances for Forms

```kotlin
@Serializable
@GenerateDataClassPaths
data class Auction(
    override val _id: UUID = UUID.random(),
    val name: String,
    @References(Venue::class) val venue: UUID,
    val startDate: LocalDate,
    val endDate: LocalDate,
) : HasId<UUID> {
    companion object {
        val EMPTY = Auction(
            name = "",
            venue = nullUuid,
            startDate = today(),
            endDate = today(),
        )
    }
}
```

### Factory Methods

```kotlin
data class Subscription(
    override val _id: UUID = UUID.random(),
    @References(User::class) val user: UUID,
    val productId: String,
    val expires: Instant,
    val startTime: Instant,
) : HasId<UUID> {
    companion object {
        fun freeTier(userId: UUID) = Subscription(
            user = userId,
            productId = "FREE_TIER",
            expires = Instant.DISTANT_FUTURE,
            startTime = now(),
        )

        fun trial(userId: UUID, days: Int = 14) = Subscription(
            user = userId,
            productId = "TRIAL",
            expires = now().plus(days.days),
            startTime = now(),
        )
    }
}
```

---

## Field Annotation Reference

| Annotation | Purpose | Example |
|------------|---------|---------|
| `@Index` | Query optimization | `@Index val email: String` |
| `@Unique` | Unique constraint | `@Unique val email: String` |
| `@References(T::class)` | Foreign key | `@References(User::class) val owner: UUID` |
| `@MultipleReferences(T::class)` | Set of foreign keys | `@MultipleReferences(Tag::class) val tags: Set<UUID>` |
| `@Denormalized` | Copied/cached data | `@Denormalized val ownerName: String` |
| `@MaxLength(storage, display)` | String length limit | `@MaxLength(256, 64) val name: String` |
| `@MaxSize(n)` | Collection size limit | `@MaxSize(20) val tags: Set<UUID>` |
| `@IntegerRange(min, max)` | Numeric bounds | `@IntegerRange(0, 1_000_000) val odometer: Int` |
| `@MimeType(types, maxSize)` | File upload constraints | `@MimeType("image/*", maxSize = 10_000_000) val photo: ServerFile?` |
| `@Description(text)` | API documentation | `@Description("User's display name") val name: String` |
| `@IndexSet([fields])` | Compound index | `@IndexSet(["user", "timestamp"])` |
| `@TextIndex([fields])` | Full-text search | `@TextIndex(["title", "description"])` |
| `@UniqueSet([fields])` | Compound unique | `@UniqueSet(["make", "model", "year"])` |
| `@AdminTableColumns` | Admin UI columns | `@AdminTableColumns(["name", "email"])` |
| `@AdminSearchFields` | Admin search | `@AdminSearchFields(["name", "email"])` |
| `@AdminTitleFields` | Admin title display | `@AdminTitleFields(["name"])` |

---

## Common Interfaces

```kotlin
interface HasId<ID : Comparable<ID>> {
    val _id: ID
}

interface HasEmail {
    val email: String
}

interface HasMaybeEmail {
    val email: String?
}

interface HasMaybePhoneNumber {
    val phoneNumber: String?
}
```

---

## Enum Guidelines

Enums are appropriate for:
- **Categorical types** that won't change: `FuelType`, `Transmission`, `UserRole`
- **Event types** within an event record: `TransactionType.Credit`, `TransactionType.Debit`

Enums are NOT appropriate for:
- **Lifecycle states** - use timestamps instead
- **Status that changes over time** - use facts/timestamps

```kotlin
// ✅ GOOD: Categorical enum
@Serializable
enum class UserRole {
    Anonymous, Customer, Manager, Admin, Developer, Root
}

// ✅ GOOD: Event type enum (used in immutable event records)
@Serializable
enum class TransactionType {
    Credit, Debit, Adjustment, Refund
}

// ❌ BAD: Status enum (use timestamps instead)
@Serializable
enum class OrderStatus {
    Draft, Submitted, Processing, Shipped, Delivered, Cancelled
}
```

---

## Example: Complete Domain Model

```kotlin
@file:UseContextualSerialization(Instant::class, UUID::class, ServerFile::class, LocalDate::class)

package com.example.shop

// Type aliases for domain language
typealias PriceInCents = Int
typealias Quantity = Int

// Value object with behavior
@Serializable
@JvmInline
value class Money(val cents: PriceInCents) {
    operator fun plus(other: Money) = Money(cents + other.cents)
    operator fun times(qty: Quantity) = Money(cents * qty)
    fun format() = "$${cents / 100}.${(cents % 100).toString().padStart(2, '0')}"
}

// Categorical enum (won't change)
@Serializable
enum class UserRole { Customer, Staff, Admin, Root }

// Entity with timestamps for state
@Serializable
@GenerateDataClassPaths
data class Order(
    override val _id: UUID = UUID.random(),
    @Index @References(User::class) val customer: UUID,
    val items: List<OrderItem> = emptyList(),
    val shippingAddress: Address,

    // Facts/timestamps - NOT a status enum
    val createdAt: Instant = now(),
    val submitted: Instant? = null,
    val paid: Instant? = null,
    val shipped: Instant? = null,
    val delivered: Instant? = null,
    val cancelled: Instant? = null,
    val cancelReason: String? = null,
) : HasId<UUID> {

    // Computed state
    val status: String get() = when {
        cancelled != null -> "Cancelled"
        delivered != null -> "Delivered"
        shipped != null -> "Shipped"
        paid != null -> "Processing"
        submitted != null -> "Awaiting Payment"
        else -> "Draft"
    }

    val isEditable: Boolean get() = submitted == null && cancelled == null
    val canCancel: Boolean get() = shipped == null && cancelled == null

    // Business logic in model
    val total: Money get() = items.fold(Money(0)) { acc, item ->
        acc + (Money(item.priceAtPurchase) * item.quantity)
    }

    companion object {
        val EMPTY = Order(
            customer = nullUuid,
            shippingAddress = Address.EMPTY,
        )
    }
}

// Embedded value object
@Serializable
@GenerateDataClassPaths
data class OrderItem(
    @References(Product::class) val productId: UUID,
    val quantity: Quantity,
    val priceAtPurchase: PriceInCents,  // Captured at order time
)

// Embedded value object
@Serializable
@GenerateDataClassPaths
data class Address(
    val street: String,
    val city: String,
    val state: String,
    val zip: String,
    val country: String = "US",
) {
    companion object {
        val EMPTY = Address("", "", "", "")
    }
}

// Immutable event record
@Serializable
@GenerateDataClassPaths
data class OrderEvent(
    override val _id: UUID = UUID.random(),
    @Index @References(Order::class) val orderId: UUID,
    val type: OrderEventType,
    val at: Instant = now(),
    @References(User::class) val by: UUID? = null,
    val notes: String? = null,
) : HasId<UUID>

@Serializable
enum class OrderEventType {
    Created, Submitted, PaymentReceived, Shipped, Delivered, Cancelled
}
```

---

## Checklist for Model Review

- [ ] No status/state enums - using timestamps for lifecycle instead?
- [ ] Facts stored, state computed?
- [ ] Type aliases for domain concepts?
- [ ] Value classes for concepts with behavior?
- [ ] Business logic in models, not scattered in services?
- [ ] Appropriate ID type chosen?
- [ ] References properly annotated?
- [ ] Denormalized fields marked and kept in sync?
- [ ] Sensible defaults for optional fields?
- [ ] Companion object with EMPTY/factory methods if needed?
- [ ] Embedded vs top-level decision correct?
