# Testing

## Practical Testing Patterns

```kotlin
class ServerTest {
    init {
        TestSettings  // Initialize test database, settings
    }

    @Test
    fun basicTest(): Unit = runBlocking {
        // Direct table access for test setup
        val org = Server.organizations.info.table()
            .insertOne(Organization(name = "Test"))!!

        val user = Server.users.info.table()
            .insertOne(User(
                email = "${Random.nextInt()}@test.com",
                memberships = setOf(Membership(org._id, UserRole.Owner))
            ))!!

        val project = Server.projects.info.table()
            .insertOne(Project(
                name = "Test Project",
                organization = org._id
            ))!!

        // Test endpoint with .test() helper
        val result = Server.projects.someEndpoint.test(user, ProjectInput(...))

        // Verify denormalized fields work correctly
        assertEquals("Test Project", result.name)
        assertEquals(org.name, result.organizationName)
    }

    @Test
    fun testFcmTokenRegistration(): Unit = runBlocking {
        val user = createTestUser()
        Server.fcmTokens.registerEndpoint.test(user, "some-fcm-token")
        assertEquals(user._id, Server.fcmTokens.info.table().get("some-fcm-token")!!.user)
    }
}
```

## Build Server Once Per Test Suite

**⚠️ CRITICAL:** When writing tests, ensure `Server.build()` is only called once across all tests to avoid `DuplicateRegistrationError`. Create a shared `TestHelper`:

```kotlin
// TestHelper.kt - shared across all test files
object TestHelper {
    val testRunner by lazy { TestRunner(Server.build()) }
}

// In your test file
class ServerTest {
    init {
        JsonFileDatabase  // Ensure mock implementations are loaded
    }

    @Test
    fun testEndpoint() = runBlocking {
        with(TestHelper.testRunner) {
            val response = Server.someEndpoint.test()
            assertEquals("expected", response.body!!.text())
        }
    }
}
```

## Test Method Signatures

For basic `HttpHandler` endpoints:
```kotlin
// No path args
Server.endpoint.test(
    queryParameters = QueryParameters(listOf("key" to "value")),
    body = TypedData.text("content", MediaType.Text.Plain)
)

// With path args
Server.endpoint.test(
    "pathArg1",
    42,  // pathArg2
    queryParameters = QueryParameters.EMPTY
)
```

For `ApiHttpHandler` endpoints:
```kotlin
// No path args
Server.typedEndpoint.test(auth = null, input = RequestData(...))

// With path args
Server.typedEndpoint.test("pathArg", auth = null, input = RequestData(...))
```

## Common Testing Pitfalls

### Duplicate UploadEarlyEndpoint Declarations

If you create multiple instances of `UploadEarlyEndpoint` (e.g., in different modules or endpoints), they will have **conflicting declarations for how `ServerFile` is serialized**. This causes runtime serialization errors that manifest as `500 Internal Server Error` responses in tests, even though the code compiles successfully.

**Solution:** Only instantiate `UploadEarlyEndpoint` once in your server definition:

```kotlin
object Server : ServerBuilder() {
    // ✅ Good - single instance
    val uploadEarly = path.path("upload") module
        UploadEarlyEndpoint(files, database, Runtime.Constant(listOf()))

    // ❌ Bad - creates duplicate with conflicting ServerFile serialization
    // val anotherUpload = path.path("upload2") module
    //     UploadEarlyEndpoint(files, database, Runtime.Constant(listOf()))
}
```

If you need multiple upload endpoints, reuse the same `UploadEarlyEndpoint` instance or use different endpoint patterns.

## Testing Infrastructure Setup

### Port Configuration

Use isolated ports for each project to avoid conflicts. Document ports in testing configuration files.

```json
// testing/settings.testing.json
{
  "general": {
    "publicUrl": "http://localhost:8082",
    "wsUrl": "ws://localhost:8082",
    "debug": true
  },
  "ktorRunConfig": {
    "host": "0.0.0.0",
    "port": 8082
  }
}
```

```javascript
// apps/vite.config.mjs (for frontend)
export default {
  server: {
    port: 8942,
    proxy: {
      '/api': {
        target: 'http://localhost:8082',
        ws: true
      }
    }
  }
}
```

**Shell Scripts:**
- Update all testing scripts with correct ports
- Create start-backend.sh, start-frontend.sh, stop-all.sh, start-all.sh
- Document in testing/README.md

### Debug Admin Token Feature

Auto-generate admin session token when debug mode is enabled for testing:

```kotlin
import com.lightningkite.lightningserver.definition.generalSettings
import kotlin.uuid.Uuid

object Server : ServerBuilder() {
    // ... other code ...

    // Debug admin token - prints on server startup when debug=true
    val debugAdminToken = path.path("debug-admin-token") bind StartupTask {
        if (generalSettings().debug) {
            // Create session for a specific admin user (ID: 0L, 10L)
            val token = UserAuth.session.createSession(Uuid.fromLongs(0L, 10L)).second
            println("Admin token: '$token'")
        }
    }
}
```

**Key points:**
- Import is `com.lightningkite.lightningserver.definition.generalSettings`, NOT `settings.generalSettings`
- Use `StartupTask` to run code once on server startup
- Token is printed to console for easy capture and use in testing

**Testing workflow:**
1. Start backend server
2. Script captures printed token from logs (e.g., `grep "Admin token:"`)
3. Save to `.admin-token` file
4. Browser testing script injects token into localStorage

### Custom Endpoints on ModelRestEndpoints

Add custom endpoints to the REST path structure using `bind ApiHttpHandler`:

```kotlin
object PendingInputEndpoints : ServerBuilder() {
    val info = Server.database.modelInfo<User, PendingInput, Uuid>(...)

    val rest = path include ModelRestEndpoints(info)

    // Custom endpoint: POST /pendingInput/respond
    val respond = path.path("respond").post bind ApiHttpHandler(
        summary = "Respond to Input",
        description = "Provides a response to a pending input request",
        auth = UserAuth.require(),
        implementation = { request: RespondInputRequest ->
            // Validation
            val input = info.table().get(request.inputId)
                ?: throw NotFoundException("Input request not found")

            // Security check
            val isAdmin = auth.userRole() >= UserRole.Admin
            if (input.ownerId != auth.id && !isAdmin) {
                throw ForbiddenException("You do not own this input request")
            }

            // Business logic
            if (input.status != InputStatus.PENDING) {
                throw BadRequestException("Input already resolved")
            }

            // Update database
            info.table().updateOneById(request.inputId, modification<PendingInput> {
                it.status assign InputStatus.RESOLVED
                it.response assign request.response
                it.resolvedAt assign Clock.System.now()
            })

            Unit
        }
    )
}
```

**Request data class in shared models:**
```kotlin
@Serializable
data class RespondInputRequest(
    val inputId: Uuid,
    val response: String
)
```

**After adding custom endpoint:**
1. Regenerate SDK: `./gradlew :server:generateSdk`
2. Generated method will be available in frontend SDK (e.g., `api.pendingInput.respondToInput(...)`)
3. Frontend can call the endpoint through type-safe SDK

### Common Pitfalls

**Wrong generalSettings import:**
```kotlin
// ❌ WRONG - compile error
import com.lightningkite.lightningserver.settings.generalSettings

// ✅ CORRECT
import com.lightningkite.lightningserver.definition.generalSettings
```

**Frontend MJS reference mismatch:**

When using Kotlin/JS with Vite, the generated JavaScript bundle name is based on the **project name**, not the template name.

```html
<!-- index.html -->
<!-- ❌ WRONG - if project name is "claude-coordinator" -->
<script src="/ls-kiteui-starter-apps.mjs" type="module"></script>

<!-- ✅ CORRECT - must match project name from settings.gradle.kts -->
<script src="/claude-coordinator-apps.mjs" type="module"></script>
```

**Debugging frontend blank page:**
1. Check browser console for "Failed to load url /xxx-apps.mjs" errors
2. Verify project name in `settings.gradle.kts` (rootProject.name)
3. Update index.html to reference `/${projectName}-apps.mjs`
4. Generated MJS file will match the rootProject.name

**Calling non-existent SDK methods:**

After adding custom endpoints, you MUST regenerate the SDK before using them in the frontend:

```bash
# Always regenerate after changing server endpoints
./gradlew :server:generateSdk
```

SDK generation creates type-safe methods in the frontend API client. Without regeneration, you'll get compilation errors when trying to call new endpoints.

### Browser Testing with Chrome MCP

For end-to-end testing, use Claude's Chrome MCP tools rather than separate Playwright/Selenium setups:

```bash
# testing/prepare-browser-test.sh
#!/bin/bash

# Start backend
./testing/start-backend.sh

# Wait for backend
while ! curl -s http://localhost:8082 > /dev/null; do
    sleep 1
done

# Capture admin token from logs
TOKEN=$(grep "Admin token:" server.log | cut -d"'" -f2)
echo "$TOKEN" > testing/.admin-token

# Start frontend
./testing/start-frontend.sh

echo "Ready for browser testing at http://localhost:8942"
```

**Testing workflow:**
1. Run prepare script to start servers and capture token
2. Use Chrome MCP tools to navigate and test
3. Inject token into localStorage for authenticated testing
4. Take screenshots to verify UI rendering
