# Troubleshooting

## Common Import Errors

When you see "Unresolved reference" errors for database operations or datetime utilities, you're likely missing imports:

```kotlin
// Database operation imports
import com.lightningkite.services.database.get
import com.lightningkite.services.database.find
import com.lightningkite.services.database.lt
import com.lightningkite.services.database.lte
import com.lightningkite.services.database.gte
import com.lightningkite.services.database.eq
import com.lightningkite.services.database.neq
import com.lightningkite.services.database.condition
import com.lightningkite.services.database.modification

// DateTime operation imports (kotlinx.datetime, not kotlin.time)
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.toLocalDateTime
import kotlinx.datetime.atStartOfDayIn
import kotlinx.datetime.plus
import kotlinx.datetime.minus

// Flow operations
import kotlinx.coroutines.flow.toList
```

**Common mistakes:**
- Using `kotlin.time.DateTimeUnit` instead of `kotlinx.datetime.DateTimeUnit`
- Using `.value` on `DayOfWeek` (doesn't exist) - use `.ordinal` instead (0-6 where Monday=0)
- Forgetting to import database query operators like `lt`, `gte`, etc.

## Type Inference Issues with DataClassPath

If you see "Cannot infer type parameter 'ROOT'" errors, ensure you're using generated path constants correctly:

```kotlin
// ✅ Correct - using generated path constant
condition { it.user eq userId }

// ❌ Wrong - missing context or incorrect path usage
condition { User_email eq "test@example.com" }  // Need it.email, not User_email
```

## Denormalization Not Working

If denormalized fields aren't updating:
1. Check that denormalize is in the `signals` block
2. Verify the source table and field are correct
3. Remember: fields aren't populated in `interceptCreate` - they update after insert

## Build System

Lightning Server uses Gradle with Kotlin Multiplatform:

### Common Commands

```bash
# Build all modules
./gradlew build

# Run tests
./gradlew check

# Run demo server
./gradlew :demo:run --args="serve"

# Generate SDK
./gradlew :demo:run --args="sdk"

# Publish to local Maven
./gradlew publishToMavenLocal
```

### Module Structure

Projects typically have paired modules:
- `module` - JVM-only code (server implementation)
- `module-shared` - Multiplatform code (shared models, DTOs)

## Deployment

### Engines

Lightning Server supports multiple engines:

- `engine-local` - For unit testing
- `engine-ktor` - Ktor HTTP server (dev/prod)
- `engine-netty` - Netty HTTP server
- `engine-jdk-server` - Pure JDK HTTP server
- `engine-aws-serverless` - AWS Lambda with Terraform generation

### AWS Deployment

The AWS engine auto-generates Terraform:

```kotlin
fun main() {
    val built = Server.build()
    AwsHandler(built).apply {
        settings.loadFromFile(KFile("settings.json"))
        // Generates terraform/ directory
    }
}
```

### Settings Management

First run generates `settings.json`:

```json
{
  "database": {
    "url": "mongodb://localhost:27017/mydb"
  },
  "cache": {
    "url": "redis://localhost:6379"
  }
}
```

## Anti-Patterns

❌ **Don't manually create CRUD endpoints** - Use ModelRestEndpoints instead
❌ **Don't create multiple UploadEarlyEndpoint instances** - Causes ServerFile serialization conflicts
❌ **Don't call Server.build() multiple times in tests** - Use shared TestHelper with lazy initialization
❌ **Don't assume denormalized fields are set in interceptCreate** - They're not populated yet!
❌ Don't access database implementations directly
❌ Don't hardcode configuration
❌ Don't skip endpoint reference storage
❌ Don't forget @GenerateDataClassPaths
❌ Don't use plain HttpHandler for APIs (use typed endpoints)
❌ Don't test against real services
❌ Don't write manual list/get/create/update/delete endpoints when ModelRestEndpoints can do it
❌ Don't use `kotlin.time.DateTimeUnit` - use `kotlinx.datetime.DateTimeUnit`

## Best Practices

1. **Use ModelRestEndpoints for CRUD** - Don't manually create database CRUD endpoints; use ModelRestEndpoints
2. **Settings File Works Out-of-Box** - Generated settings should allow immediate running
3. **Use Service Abstractions** - Don't depend on specific implementations
4. **Test with Mocks** - Use JsonFileDatabase, RAM cache for tests
5. **Store Endpoint References** - Keep constants for all endpoints
6. **Group Endpoints Logically** - Use ServerBuilder objects
7. **Type Safety** - Use @GenerateDataClassPaths on all database models
8. **Document Typed Endpoints** - Add summaries and descriptions
9. **Read This Skill First** - When working on Lightning Server files, read this skill to understand patterns

## Key Files to Reference

- `demo/src/main/kotlin/.../Server.kt` - Comprehensive example
- `docs/setup.md` - Project setup
- `docs/endpoints.md` - Endpoint patterns
- `docs/typed-endpoints.md` - Typed API docs
- `docs/database.md` - Database usage
- `docs/authentication.md` - Auth setup

## Getting Help

When stuck:
1. **Read this skill** - Most common patterns are documented here
2. Check the demo server for examples
3. Review relevant docs in `/docs`
4. Look at existing endpoint implementations
5. Check test files for usage patterns
6. Examine the CLAUDE.md file for project-specific guidance
