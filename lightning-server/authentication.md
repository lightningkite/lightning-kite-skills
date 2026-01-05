# Authentication

## PrincipalType Definition

Define a PrincipalType for your user model:

```kotlin
object UserAuth: PrincipalType<User, Uuid> {
    override val idSerializer = Uuid.serializer()
    override val subjectSerializer = User.serializer()
    override val name = "User"

    context(server: ServerRuntime)
    override suspend fun fetch(id: Uuid): User =
        database().table<User>().get(id) ?: throw NotFoundException()
}
```

## Basic Auth Setup

Set up ModelInfo with permissions (required auth example):

```kotlin
val userInfo: ModelInfo<User, User, Uuid> = database.modelInfo(
    auth = UserAuth.require(),  // Required auth
    permissions = {
        val userRole = auth.userRole()  // Cached role check
        val self = condition { it._id eq auth.id }
        val admin = if (userRole >= UserRole.Admin) Condition.Always else Condition.Never

        ModelPermissions(
            create = Condition.Never,
            read = Condition.Always,
            update = self or admin,
            delete = admin
        )
    }
)
```

## Proof Methods

Configure proof methods:

```kotlin
val pins = PinHandler(cache, "pins")
val proofEmail = path.path("proof").path("email") module
    EmailProofEndpoints(pins, email, { to, pin ->
        Email(subject = "Login Code", to = listOf(EmailAddressWithName(to)),
              plainText = "Your PIN is $pin")
    })
val proofPassword = path.path("proof").path("password") module
    PasswordProofEndpoints(database, cache)
```

## AuthEndpoints Setup

```kotlin
val auth = path.path("auth") module object: AuthEndpoints<User, Uuid>(
    principal = UserAuth,
    database = database
) {
    context(server: ServerRuntime)
    override suspend fun requiredProofStrengthFor(subject: User): Int = 5

    context(server: ServerRuntime)
    override suspend fun sessionExpiration(subject: User): Instant? = null
}
```

## Optional Authentication (Public + Authenticated Access)

For endpoints that allow both authenticated and unauthenticated users (e.g., public-facing APIs), use optional authentication:

**Setup:**

```kotlin
object ProjectEndpoints : ServerBuilder() {
    val info = Server.database.modelInfo(
        auth = UserAuth.require() or AuthRequirement.None,  // Optional auth
        permissions = { permissions(this) }
    )

    context(runtime: ServerRuntime)
    suspend fun permissions(auth: AuthAccess<User?>): ModelPermissions<Project> {
        // ⚠️ CRITICAL: Use authOrNull with cached userRole extension
        val userRole = auth.authOrNull?.userRole() ?: UserRole.NoOne
        val isAdmin = userRole >= UserRole.Admin

        return ModelPermissions(
            create = if (isAdmin) Condition.Always else Condition.Never,
            read = Condition.Always,  // Public read
            update = if (isAdmin) Condition.Always else Condition.Never,
            delete = if (isAdmin) Condition.Always else Condition.Never,
        )
    }

    val rest = path include ModelRestEndpoints(info)
}
```

**Required imports:**

```kotlin
import com.lightningkite.lightningserver.auth.AuthRequirement
import com.lightningkite.lightningserver.auth.or
import com.lightningkite.lightningserver.auth.require
import com.lightningkite.lskiteuistarter.UserAuth.RoleCache.userRole  // ⚠️ Essential!
```

**Key Points:**

- Type is `AuthAccess<User?>` (nullable User) when using optional auth
- Use `auth.authOrNull?.userRole()` NOT `auth.authOrNull?.fetch()`
- Must import the `userRole` extension function from your `UserAuth.RoleCache`
- Default to `UserRole.NoOne` if not authenticated
- This pattern uses cached role data - no extra database query needed

**What you get:**

- Unauthenticated users can query via `GET /projects/rest/query`
- Admin users can create/update/delete
- Single endpoint serves both use cases
- Efficient - uses cached authentication data

## Auth Caching with AuthCacheKey

Cache expensive authentication-derived data to avoid repeated database queries:

```kotlin
object UserAuth : PrincipalType<User, Uuid> {
    // ... other fields ...

    // Define what to pre-cache on session creation
    override val precache: List<AuthCacheKey<User, *>> = listOf(IsSuperUserCache, MembershipCache)

    // Simple cache example
    object IsSuperUserCache : AuthCacheKey<User, Boolean> {
        override val id: String = "super-user"
        override val serializer: KSerializer<Boolean> = Boolean.serializer()
        override val expireAfter: Duration = 5.minutes

        context(_: ServerRuntime)
        override suspend fun calculate(input: Authentication<User>): Boolean =
            input.fetch().isSuperUser

        // Extension functions for easy access
        context(_: ServerRuntime) suspend fun Authentication<User>.isSuperUser() = get(IsSuperUserCache)
        context(_: ServerRuntime) suspend fun AuthAccess<User>.isSuperUser() = auth.isSuperUser()
    }

    // Complex cache with related data
    object MembershipCache : AuthCacheKey<User, Set<ActiveMembership>> {
        override val id: String = "memberships"
        override val serializer = SetSerializer(ActiveMembership.serializer())
        override val expireAfter = 5.minutes

        context(_: ServerRuntime)
        override suspend fun calculate(input: Authentication<User>): Set<ActiveMembership> {
            val memberships = input.fetch().memberships
            val activeOrgs = OrganizationTable.getMany(memberships.map { it.organization })
                .filter { it.subscriptionActive }
                .map { it._id }
                .toSet()
            return memberships.map {
                ActiveMembership(it, it.organization in activeOrgs)
            }.toSet()
        }
    }

    // Derived caches (transform existing cache data efficiently)
    private fun <T, R : Any> AuthCacheKey<User, Set<T>>.derive(
        id: String,
        transform: (T) -> R?
    ): AuthCacheKey<User, Set<R>> = object : AuthCacheKey<User, Set<R>> {
        override val id = id
        override val serializer = SetSerializer(serializerOrContextual<R>())
        override val expireAfter = this@derive.expireAfter
        override val localOnly = true  // Not stored on token

        context(_: ServerRuntime)
        override suspend fun calculate(input: Authentication<User>) =
            input[this@derive].mapNotNullTo(HashSet(), transform)
    }

    // Chain derived caches
    val memberships = MembershipCache.derive("memberships-only") { it.membership }
    val activeMemberships = MembershipCache.derive("active") { it.takeIf { it.active }?.membership }
    val organizations = memberships.derive("orgs") { it.organization }
    val activeOrganizations = activeMemberships.derive("active-orgs") { it.organization }

    // Convenience extensions
    context(_: ServerRuntime) suspend fun AuthAccess<User>.activeOrganizations() = auth[activeOrganizations]
}
```

**Use in permissions:**

```kotlin
permissions = {
    if (auth.isSuperUser()) return@permissions ModelPermissions.allowAll()
    val orgs = auth.activeOrganizations()
    val orgCondition = condition { it.organization inside orgs }

    ModelPermissions(
        create = orgCondition,
        read = orgCondition,
        update = orgCondition,
        delete = orgCondition
    )
}
```

**Key benefits:**
- Pre-cached values stored on session token (fast access)
- Derived caches avoid redundant database queries
- `localOnly` caches save token space (computed on-demand)
- Automatic invalidation on cache expiry

## Auto-User-Creation Pattern for Signup Flows

**⚠️ IMPORTANT**: For email-based authentication, you typically don't need custom signup endpoints. Users are automatically created on first login via `fetchByProperty`.

**Automatic User Creation on First Login:**

```kotlin
object UserAuth : PrincipalType<User, Uuid> {
    // ... other fields ...

    context(server: ServerRuntime)
    override suspend fun fetchByProperty(property: String, value: String): User? = when (property) {
        "email" -> UserEndpoints.info.table()
            .run {
                // Automatically creates user if doesn't exist
                findOne(condition { it.email eq value.toEmailAddress() })
                    ?: insertOne(User(email = value.toEmailAddress()))
            }
        else -> super.fetchByProperty(property, value)
    }
}
```

**This means:**
- When a user authenticates via email for the first time, a User record is created automatically
- No need for dedicated "signup" endpoints - just use existing EmailProofEndpoints
- User is created with minimal fields (just email), additional profile info added later

## Progressive Profile Completion Pattern

After auto-creation, guide users to complete their profile:

**Backend:**
```kotlin
@Serializable
data class User(
    override val _id: Uuid = Uuid.random(),
    val email: EmailAddress,
    val name: String = "No Name Specified",  // Default value
    val phone: String? = null,                // Optional
    val emergencyContact: String? = null,     // Optional
    val role: UserRole = UserRole.User,
) : HasId<Uuid>
```

**Frontend (KiteUI):**
```kotlin
// After successful authentication, check profile completion
reactive {
    val session = currentSession()
    if(session == null) {
        pageNavigator.reset(LandingPage())
    } else {
        val user = session.api.userAuth.getSelf()
        val needsProfileCompletion = user.name == "No Name Specified" ||
                                     user.phone == null ||
                                     user.emergencyContact == null
        if (needsProfileCompletion) {
            pageNavigator.reset(ProfileCompletionScreen(user.email.raw))
        }
    }
}
```

**Updating User Profile:**
```kotlin
// In ProfileCompletionScreen
onClick {
    launch {
        val session = currentSession.awaitNotNull()

        // Modify user with ModelCache helper
        session.users[session.userId].modify(modification {
            it.name assign fullName.value
            it.phone assign phone.value
            it.emergencyContact assign emergencyContact.value
        })

        pageNavigator.reset(HomePage())
    }
}
```

**Key imports for modification:**
```kotlin
import com.lightningkite.lightningdb.modification
import com.lightningkite.lskiteuistarter.name      // Auto-generated
import com.lightningkite.lskiteuistarter.phone     // Auto-generated
import com.lightningkite.lskiteuistarter.emergencyContact  // Auto-generated
```

**Why This Pattern Works:**
- ✅ No redundant signup endpoints (reuse existing auth)
- ✅ Users can authenticate immediately (frictionless onboarding)
- ✅ Profile completed progressively (better UX)
- ✅ Standard REST endpoints for updates (consistent API)
