# REST Endpoint Lifecycle

Understanding the full lifecycle is essential for placing business logic in the right hooks.

## Full Lifecycle for REST Operations

### POST (Create) Lifecycle

When a client calls `POST /model/rest`:

```
1. Request arrives at ModelRestEndpoints.insert
   ↓
2. Authentication checked (via info.auth)
   ↓
3. info.table(auth) called → builds Table with all wrappers
   ↓
4. Table.interceptCreate runs
   ├─ Can modify the object being created
   ├─ Can throw exceptions to reject creation
   ├─ ⚠️ Denormalized fields NOT populated yet!
   └─ Must fetch related records directly if needed
   ↓
5. Database insert occurs (actual write)
   ↓
6. Denormalization runs (.denormalize() calculations)
   ├─ Denormalized fields now populated
   └─ Source records queried and values copied
   ↓
7. Permissions.create condition checked
   ├─ If condition fails, insertion is rolled back
   └─ Returns ForbiddenException
   ↓
8. Table.postCreate runs
   ├─ Object is now in database with all fields
   ├─ Safe to trigger side effects
   └─ Cannot stop creation (already committed)
   ↓
9. Response sent to client with created object
```

**Example:**
```kotlin
signals = { table ->
    table
        .interceptCreate { reservation ->
            // 1. Validation - check conflicts
            val conflicts = info.table().find(condition {
                (it.booth eq reservation.booth) and
                (it.at lt reservation.endsAt) and
                (it.endsAt gt reservation.at) and
                it.cancelledAt.eq(null)
            }).toList()
            if (conflicts.isNotEmpty()) {
                throw BadRequestException("Time slot conflicts")
            }

            // 2. Business logic - check subscription limits
            val subscription = getActiveSubscription(reservation.user)
            subscription?.let {
                val limit = getPlanLimit(it.plan)
                val todayCount = countReservationsToday(reservation.user)
                if (todayCount >= limit) {
                    throw BadRequestException("Daily limit reached")
                }
            }

            // 3. Modify object - set expiration
            reservation.copy(expireAt = Clock.System.now() + 15.minutes)
        }
        .postCreate { created ->
            // 4. Side effects - send email notification
            emailService.sendConfirmation(created.user, created)
        }
}
```

### PATCH (Update) Lifecycle

When a client calls `PATCH /model/rest/{id}`:

```
1. Request arrives with Modification<T>
   ↓
2. Authentication checked (via info.auth)
   ↓
3. info.table(auth) called → builds Table with all wrappers
   ↓
4. Table.interceptUpdate runs (if using interceptChangePerInstance)
   ├─ Has access to BOTH old and new values
   ├─ Can modify the Modification being applied
   ├─ Can throw exceptions to reject update
   └─ Expensive - fetches existing record first
   ↓
5. Table.interceptChange / interceptModification runs
   ├─ Can validate or modify the Modification
   ├─ Can throw exceptions to reject update
   └─ Cheaper - doesn't need existing record
   ↓
6. Permissions.updateRestrictions checked
   ├─ Field-level restrictions enforced
   ├─ e.g., it.author.cannotBeModified()
   └─ Throws ForbiddenException if violated
   ↓
7. Database update occurs (actual write)
   ↓
8. Denormalization runs (if source fields changed)
   ├─ Updates denormalized fields
   └─ May trigger cascade updates to other tables
   ↓
9. Permissions.update condition checked
   ├─ Checked against OLD value
   ├─ If condition fails, update is rolled back
   └─ Returns ForbiddenException
   ↓
10. Table.postChange runs
    ├─ Has access to both old and new values
    ├─ Object already updated in database
    ├─ Safe to trigger side effects
    └─ Cannot stop update (already committed)
    ↓
11. Response sent to client with updated object
```

**Example:**
```kotlin
permissions = {
    val user = auth.fetch()
    ModelPermissions(
        // ...
        update = condition { it.user eq user._id },  // Can only update your own
        updateRestrictions = updateRestrictions {
            it.user.cannotBeModified()      // Field restriction
            it.createdAt.cannotBeModified() // Field restriction
        }
    )
},
signals = { table ->
    table
        .interceptChange { mod ->
            // Validate modifications before they're applied
            mod.vet(Reservation_booth) { fieldMod ->
                when (fieldMod) {
                    is Modification.Assign -> {
                        // Check if new booth is available
                        val newBooth = BoothEndpoints.info.table().get(fieldMod.value)
                            ?: throw BadRequestException("Booth not found")
                        if (!newBooth.available) {
                            throw BadRequestException("Booth not available")
                        }
                    }
                    else -> {}
                }
            }
            mod
        }
        .postChange { old, new ->
            // Side effect - if booth changed, send notification
            if (old.booth != new.booth) {
                notificationService.send(new.user, "Booth changed")
            }
        }
}
```

## Hook Reference Guide

### interceptCreate / interceptCreates

**When it runs:** Before database insert, after auth check

**What it can do:**
- ✅ Modify the object being created (return modified copy)
- ✅ Throw exceptions to reject creation
- ✅ Validate business rules (uniqueness, conflicts, quotas)
- ✅ Set computed fields (expiration, defaults)
- ✅ Query database for validation
- ❌ Cannot access denormalized fields (not populated yet)

**Use cases:**
- Conflict detection (time slot conflicts, unique constraints)
- Subscription/quota validation (daily limits, plan restrictions)
- Setting expiration times (tentative bookings)
- Validating related records exist
- Enforcing business rules

**Example:**
```kotlin
.interceptCreate { reservation ->
    // Validate: No conflicts
    val conflicts = findConflicts(reservation)
    if (conflicts.isNotEmpty()) throw BadRequestException("Conflict")

    // Validate: Subscription limits
    val subscription = getSubscription(reservation.user)
    validateLimits(subscription, reservation)

    // Modify: Set expiration
    reservation.copy(expireAt = now() + 15.minutes)
}
```

### interceptChange / interceptModification

**When it runs:** Before database update, after auth check, before updateRestrictions

**What it can do:**
- ✅ Modify the Modification being applied
- ✅ Throw exceptions to reject update
- ✅ Validate field changes with mod.vet()
- ✅ Query database for validation
- ❌ Cannot access old/new values (use interceptChangePerInstance for that)

**Use cases:**
- Field-level validation (enum transitions, format checks)
- Validating modifications before application
- Transforming modifications (normalize data)
- Enforcing state machine rules

**Example:**
```kotlin
.interceptChange { mod ->
    mod.vet(Reservation_status) { fieldMod ->
        when (fieldMod) {
            is Modification.Assign -> {
                // Validate status transitions
                if (!isValidTransition(currentStatus, fieldMod.value)) {
                    throw BadRequestException("Invalid status transition")
                }
            }
            else -> {}
        }
    }
    mod
}
```

### interceptChangePerInstance (expensive!)

**When it runs:** Before database update, fetches existing record first

**What it can do:**
- ✅ Access both old value and modification
- ✅ Modify the Modification based on old value
- ✅ Throw exceptions to reject update
- ⚠️ Expensive - requires extra database read

**Use cases:**
- Validation that requires old value
- State machine transitions
- Audit trail generation

**Example:**
```kotlin
.interceptChangePerInstance { old, mod ->
    // Can access old value for validation
    if (old.status == Status.Completed) {
        throw BadRequestException("Cannot modify completed reservation")
    }
    mod
}
```

### updateRestrictions (in ModelPermissions)

**When it runs:** After interceptChange, before database update

**What it can do:**
- ✅ Block specific fields from being modified
- ✅ Enforced automatically by framework
- ❌ Cannot throw custom exceptions (framework handles it)

**Use cases:**
- Prevent modification of immutable fields (author, createdAt)
- Enforce field-level access control
- Prevent tampering with computed fields

**Example:**
```kotlin
ModelPermissions(
    // ...
    updateRestrictions = updateRestrictions {
        it.user.cannotBeModified()           // User cannot change
        it.createdAt.cannotBeModified()      // Created timestamp locked
        it.organizationName.cannotBeModified() // Denormalized field locked
    }
)
```

### postChange

**When it runs:** After successful database update, after denormalization

**What it can do:**
- ✅ Access both old and new values
- ✅ Trigger side effects (notifications, cascade updates)
- ✅ Update denormalized data in other tables
- ✅ Log changes for audit trail
- ❌ Cannot stop the update (already committed)
- ❌ Should not throw exceptions (may leave inconsistent state)

**Use cases:**
- Send notifications (email, push, WebSocket)
- Cascade updates to denormalized fields in other tables
- Trigger workflows based on changes
- Audit logging
- Cache invalidation

**Example:**
```kotlin
.postChange { old, new ->
    // Cascade update denormalized fields
    if (old.name != new.name) {
        RelatedTable.updateMany(
            condition { it.projectId eq new._id },
            modification { it.projectName assign new.name }
        )
    }

    // Send notifications
    if (old.status != new.status) {
        notificationService.send(new.user, "Status changed to ${new.status}")
    }
}
```

### postCreate

**When it runs:** After successful database insert, after denormalization

**What it can do:**
- ✅ Access the created object (with all fields populated)
- ✅ Trigger side effects (notifications, related record creation)
- ✅ Create related records
- ❌ Cannot stop the creation (already committed)
- ❌ Should not throw exceptions (may leave inconsistent state)

**Use cases:**
- Send welcome emails
- Create related records (default settings, initial data)
- Trigger external systems
- Analytics tracking

**Example:**
```kotlin
.postCreate { created ->
    // Send confirmation email
    emailService.sendWelcome(created.email)

    // Create default settings
    SettingsTable.insertOne(Settings(userId = created._id))
}
```

### postDelete

**When it runs:** After successful database deletion

**What it can do:**
- ✅ Access the deleted object
- ✅ Clean up related records
- ✅ Trigger external cleanup
- ❌ Cannot stop the deletion (already committed)
- ❌ Should not throw exceptions (may leave inconsistent state)

**Use cases:**
- Delete related records (cascade delete)
- Clean up uploaded files
- Notify external systems
- Audit logging

**Example:**
```kotlin
.postDelete { deleted ->
    // Clean up related records
    RelatedTable.deleteMany(condition { it.projectId eq deleted._id })

    // Delete uploaded files
    deleted.avatarFile?.let { fileService.delete(it) }
}
```

## Decision Tree: Which Hook to Use?

**Need to validate before creation?**
→ Use `interceptCreate`

**Need to validate before update?**
→ Use `interceptChange` (or `interceptModification`)

**Need old value for validation?**
→ Use `interceptChangePerInstance` (expensive!)

**Need to prevent specific fields from being modified?**
→ Use `updateRestrictions` in `ModelPermissions`

**Need to send notifications after change?**
→ Use `postChange` or `postCreate`

**Need to cascade updates to other tables?**
→ Use `postChange`

**Need to clean up after deletion?**
→ Use `postDelete`

## Signal Hook Execution Order

Understanding the exact execution order is crucial for correct implementation:

1. **interceptCreates / interceptChange** - Validation (can throw exceptions)
   - ⚠️ **Denormalized fields are NOT populated yet!**
   - Must fetch source records directly if needed
2. **Database write occurs** - Record inserted/updated
3. **Denormalization updates** - `.denormalize()` calculations run, fields populated
4. **postChange / postCreate / postDelete** - Side effects (cascade updates, notifications)

**Example showing timing:**

```kotlin
.denormalize2(
    BoothDividerOpenRequest_fromReservation,
    ReservationEndpoints.info.table(),
    DenormalizationCalculation(BoothDividerOpenRequest_proposedBy, Uuid.fromLongs(0, 0)) { it.user },
    DenormalizationCalculation(BoothDividerOpenRequest_from, Instant.DISTANT_PAST) { it.at }
).interceptCreate { request ->
    // ⚠️ request.proposedBy and request.from are NOT set yet!
    // Denormalization hasn't run - still have default values

    // ✅ Must fetch source directly:
    val fromReservation = ReservationEndpoints.info.table().get(request.fromReservation)
        ?: throw BadRequestException("fromReservation not found")

    val proposedBy = fromReservation.user  // Get from source, not request.proposedBy
    val timeRange = fromReservation.at .. fromReservation.endsAt

    // Validate and potentially modify the request
    val toReservation = findToReservation(request.toBooth, timeRange)
    request.copy(toReservation = toReservation._id, proposedTo = toReservation.user)
}
```

## Complete Example: Reservation System

Putting it all together:

```kotlin
val reservationInfo = database.modelInfo(
    auth = UserAuth.require(),
    permissions = {
        val user = auth.fetch()
        ModelPermissions(
            create = condition { it.user eq user._id },
            read = condition { it.user eq user._id },
            update = condition { it.user eq user._id },
            delete = condition { it.user eq user._id },
            updateRestrictions = updateRestrictions {
                it.user.cannotBeModified()      // Can't change owner
                it.createdAt.cannotBeModified() // Can't change timestamp
                it.booth.cannotBeModified()     // Can't change booth after creation
            }
        )
    },
    signals = { table ->
        table
            // 1. VALIDATION ON CREATE
            .interceptCreate { reservation ->
                // Check for time slot conflicts
                val conflicts = info.table().find(condition {
                    (it.booth eq reservation.booth) and
                    (it.at lt reservation.endsAt) and
                    (it.endsAt gt reservation.at) and
                    it.cancelledAt.eq(null)
                }).toList()
                if (conflicts.isNotEmpty()) {
                    throw BadRequestException("Time slot conflicts with existing reservation")
                }

                // Check subscription limits (if subscription exists)
                val subscription = findActiveSubscription(reservation.user, reservation.organization)
                subscription?.let { sub ->
                    val restrictions = getPlanRestrictions(sub.plan)
                    val duration = reservation.endsAt - reservation.at

                    if (duration < restrictions.minimumDuration) {
                        throw BadRequestException("Duration too short")
                    }
                    if (duration > restrictions.maximumDuration) {
                        throw BadRequestException("Duration too long")
                    }

                    val todayCount = countReservationsToday(reservation.user, reservation.booth)
                    if (todayCount >= restrictions.perDay) {
                        throw BadRequestException("Daily limit reached")
                    }
                }

                // Set expiration for tentative booking
                reservation.copy(expireAt = Clock.System.now() + 15.minutes)
            }

            // 2. VALIDATION ON UPDATE
            .interceptChange { mod ->
                // Validate status transitions
                mod.vet(Reservation_status) { fieldMod ->
                    when (fieldMod) {
                        is Modification.Assign -> {
                            if (!isValidStatusTransition(fieldMod.value)) {
                                throw BadRequestException("Invalid status transition")
                            }
                        }
                        else -> {}
                    }
                }
                mod
            }

            // 3. SIDE EFFECTS AFTER CHANGE
            .postChange { old, new ->
                // Send notification if status changed
                if (old.status != new.status) {
                    notificationService.send(
                        new.user,
                        "Reservation status changed to ${new.status}"
                    )
                }

                // If confirmed (expireAt cleared), send confirmation email
                if (old.expireAt != null && new.expireAt == null) {
                    emailService.sendConfirmation(new.user, new)
                }
            }

            // 4. SIDE EFFECTS AFTER CREATE
            .postCreate { created ->
                // Send tentative booking notification
                emailService.sendTentativeBooking(created.user, created)
            }

            // 5. CLEANUP AFTER DELETE
            .postDelete { deleted ->
                // Cancel any related services
                if (deleted.checkedInAt != null) {
                    serviceIntegration.releaseResources(deleted.booth)
                }
            }
    }
)
```

## Common Pitfalls

**Accessing denormalized fields in interceptCreate:**
```kotlin
.interceptCreate { request ->
    // ❌ WRONG - proposedBy is not set yet!
    if (request.proposedBy == request.proposedTo) {
        throw BadRequestException("Cannot propose to yourself")
    }

    // ✅ CORRECT - fetch source data directly
    val fromReservation = ReservationTable.get(request.fromReservation)
        ?: throw BadRequestException("Not found")
    if (fromReservation.user == toReservation.user) {
        throw BadRequestException("Cannot propose to yourself")
    }
}
```

**Throwing exceptions in postChange:**
```kotlin
.postChange { old, new ->
    // ❌ WRONG - may leave inconsistent state
    if (new.invalidField) {
        throw BadRequestException("Invalid")
    }

    // ✅ CORRECT - validate in interceptChange instead
}
```

**Forgetting updateRestrictions:**
```kotlin
// ❌ WRONG - client can modify createdAt!
ModelPermissions(
    update = condition { it.user eq user._id }
)

// ✅ CORRECT - lock immutable fields
ModelPermissions(
    update = condition { it.user eq user._id },
    updateRestrictions = updateRestrictions {
        it.createdAt.cannotBeModified()
        it.user.cannotBeModified()
    }
)
```

**interceptCreate doesn't bypass serialization requirements:**
```kotlin
// ❌ WRONG - ownerId has no default, so client MUST provide it
// even though interceptCreate will override it
data class Project(
    override val _id: Uuid = Uuid.random(),
    val name: String,
    @References(User::class) val ownerId: Uuid,  // Required in request!
    val createdAt: Instant = Clock.System.now()
) : HasId<Uuid>

// API call fails with: "Field 'ownerId' is required"
POST /projects {"name": "My Project"}

// ✅ CORRECT - provide a placeholder default for server-set fields
data class Project(
    override val _id: Uuid = Uuid.random(),
    val name: String,
    @References(User::class) val ownerId: Uuid = Uuid.nil(),  // Default allows omission
    val createdAt: Instant = Clock.System.now()
) : HasId<Uuid>

// Server sets ownerId in interceptCreate:
postPermissionsForUser = {
    it.interceptCreate { project: Project ->
        project.copy(ownerId = auth.id)  // Overrides the default
    }
}

// Now API call works:
POST /projects {"name": "My Project"}  // ownerId set by server
```

**Key Insight:** Serialization (JSON → Kotlin object) happens BEFORE `interceptCreate` runs. If a field has no default value, the request body must include it, even if the server will immediately override it. Provide placeholder defaults like `Uuid.nil()` or `Instant.DISTANT_PAST` for fields that will be server-set.
