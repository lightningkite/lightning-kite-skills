# Model Files Index - @GenerateDataClassPaths
<!-- by Claude -->

This index catalogs Kotlin files using `@GenerateDataClassPaths` across Lightning Kite projects.

## Production Application Models

### ls-kiteui-starter (Starter Template)
- `~/Projects/ls-kiteui-starter/shared/src/commonMain/kotlin/com/lightningkite/lskiteuistarter/models.kt`
- `~/Projects/ls-kiteui-starter/shared/src/commonMain/kotlin/com/lightningkite/lightningserver/ai/SystemChatModels.kt`

### BeeMee (AI Wellness App)
- `~/Projects/BeeMee/shared/src/commonMain/kotlin/com/beemee/models.kt` (referenced in exploration)

### Blackstone (IoT Pellet Grill)
- `~/Projects/blackstone/shared/src/commonMain/kotlin/com/blackstone/models.kt` (referenced in exploration)

### CrowPay (Payment Platform)
- `~/Projects/crowpay/shared/src/commonMain/kotlin/com/crowpay/databaseModels.kt` (referenced in exploration)

### Circadia Admin (Business Management)
- `~/Projects/circadia-admin/shared/src/commonMain/kotlin/com/circadia/lkautomate/databaseModels/authmodels.kt`
- `~/Projects/circadia-admin/shared/src/commonMain/kotlin/otherModels.kt`
- `~/Projects/circadia-admin/server/src/main/kotlin/com/circadia/lkautomate/CustomerLicenseVerifier.kt`

### Hammer Price (Auction Platform)
- `~/Projects/hammer-price-lightning-server/shared/src/commonMain/kotlin/com/hammerprice/lk/models.kt` (referenced in exploration)

### Connect v4 (Camp Chef Grill)
- `~/Projects/connect-v4/shared/src/main/kotlin/com/campchef/models.kt` (referenced in exploration)

### Lightning Credit (Store Credit/Rewards)
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/Users.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/Customers.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/Transactions.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/StoreCreditTransactions.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/Rewards.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/CustomerRewards.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/Promotions.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/PromotionLog.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/MerchantStore.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/MerchantIntegrations.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/ImportJobs.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/BulkOperationLogs.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/WebhookLogs.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/QueuedGiftCardMutations.kt`
- `~/Projects/lightning-credit/src/main/kotlin/databaseModels/DataDeletionLog.kt`

### Monetime (Financial App)
- `~/Projects/monetime-lightning-server/src/main/kotlin/ai/monetime/models.kt`
- `~/Projects/monetime-lightning-server/src/main/kotlin/ai/monetime/google/GoogleEndpoints.kt`
- `~/Projects/monetime-lightning-server/src/main/kotlin/ai/monetime/stripe/StripeWebhookSecret.kt`

### Shopify Referral Linker
- `~/Projects/shopify-referral-linker-app/shared/src/commonMain/kotlin/deals/srp/models.kt`

### Phoodle Backend
- `~/Projects/PhoodleBackend/server/src/main/kotlin/net/phoodle/models.kt`

### Party Hardy
- `~/Projects/partyhardy/shared/src/commonMain/kotlin/com/lightningkite/rock/template/models.kt`

### Ilusso BSA
- `~/Projects/ilusso-bsa/shared/src/commonMain/kotlin/com/ilussobsa/models.kt`

---

## Framework/Library Code

### Service Abstractions (Database Layer)
- `~/Projects/service-abstractions copy/database/src/commonMain/kotlin/com/lightningkite/services/database/Database.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonMain/kotlin/com/lightningkite/services/database/DataClassPath.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonMain/kotlin/com/lightningkite/services/database/ModelPermissions.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonMain/kotlin/com/lightningkite/services/database/Mask.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonMain/kotlin/com/lightningkite/services/database/VectorIndex.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonMain/kotlin/com/lightningkite/services/database/UpdateRestrictions.kt`
- `~/Projects/service-abstractions copy/database-processor/src/main/kotlin/com/lightningkite/serviceabstractions/database/processor/AnnotationProcessor.kt`

### Lightning Server (Main Framework)
- `~/Projects/lightning-server-cc/shared/src/main/kotlin/com/lightningkite/lightningserver/exceptions/ReportedException.kt`
- `~/Projects/lightning-server-cc/shared/src/main/kotlin/com/lightningkite/lightningserver/files/UploadEarlyEndpointModels.kt`
- `~/Projects/lightning-server-cc/server-core/src/main/kotlin/com/lightningkite/lightningserver/metrics/MetricSpanStats.kt`
- `~/Projects/lightning-server-cc/server-core/src/main/kotlin/com/lightningkite/lightningserver/tasks/dsl.kt`
- `~/Projects/lightning-server-cc/server-core/src/main/kotlin/com/lightningkite/lightningserver/externalintegration/ExternalAsyncTaskRequest.kt`
- `~/Projects/lightning-server-cc/server-core/src/main/kotlin/com/lightningkite/lightningdb/Database.kt`

### Lightning Server AI Observability
- `~/Projects/lightning-server-ai-observability/ai-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/ai/SystemChatModels.kt`
- `~/Projects/lightning-server-ai-observability/typed-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/typed/models.kt`
- `~/Projects/lightning-server-ai-observability/files-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/files/models.kt`
- `~/Projects/lightning-server-ai-observability/media-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/media/models.kt`
- `~/Projects/lightning-server-ai-observability/notifications-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/notifications/notificationModels.kt`
- `~/Projects/lightning-server-ai-observability/notifications-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/notifications/subscriptions/subscriptionModels.kt`
- `~/Projects/lightning-server-ai-observability/notifications-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/notifications/events/eventModels.kt`
- `~/Projects/lightning-server-ai-observability/sessions-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/sessions/sessionModels.kt`
- `~/Projects/lightning-server-ai-observability/sessions-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/sessions/proofs/oauth/models.kt`
- `~/Projects/lightning-server-ai-observability/sessions-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/sessions/proofs/WebAuthN.kt`
- `~/Projects/lightning-server-ai-observability/sessions-shared/src/commonMain/kotlin/com/lightningkite/lightningserver/sessions/AuthSecrets.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/main/kotlin/com/lightningkite/lightningserver/ai/ConditionExpression.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/main/kotlin/com/lightningkite/lightningserver/ai/ModificationExpression.kt`

### Lightning Server KiteUI Client
- `~/Projects/lightning-server-kiteui/client/src/commonTest/kotlin/com/lightningkite/lightningserver/db/models.kt`
- `~/Projects/lightning-server-kiteui/client/src/commonTest/kotlin/com/lightningkite/lightningserver/db/test.kt`
- `~/Projects/lightning-server-kiteui/client/src/commonTest/kotlin/com/lightningkite/specialtest/models.kt`

---

## Test Models

### Service Abstractions Tests
- `~/Projects/service-abstractions copy/database/src/commonTest/kotlin/com/lightningkite/serviceabstractions/database/FieldGenerationTest.kt`
- `~/Projects/service-abstractions copy/database-test/src/commonMain/kotlin/com/lightningkite/services/database/test/models.kt`
- `~/Projects/service-abstractions copy/database-shared/src/jvmTest/kotlin/KxSerializationFieldAccessTest.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonTest/kotlin/com/lightningkite/serviceabstractions/database/KxSerializationFieldAccessTest.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonTest/kotlin/com/lightningkite/serviceabstractions/database/FieldGenerationTest.kt`
- `~/Projects/service-abstractions copy/database-shared/src/commonTest/kotlin/com/lightningkite/serviceabstractions/database/GeneratedPropertyTests.kt`
- `~/Projects/service-abstractions copy/database-mongodb/src/test/kotlin/com/lightningkite/services/database/mongodb/BsonTest.kt`
- `~/Projects/service-abstractions copy/data/src/commonTest/kotlin/com/lightningkite/serviceabstractions/data/ValidationTest.kt`

### Lightning Server Tests
- `~/Projects/lightning-server-cc/demo/src/main/kotlin/models.kt`
- `~/Projects/lightning-server-cc/server-testing/src/main/kotlin/com/lightningkite/lightningdb/test/models.kt`
- `~/Projects/lightning-server-cc/shared/src/test/kotlin/models.kt`
- `~/Projects/lightning-server-cc/server-core/src/test/kotlin/com/lightningkite/lightningserver/jsonschema/models.kt`
- `~/Projects/lightning-server-cc/server-core/src/test/kotlin/com/lightningkite/lightningserver/db/testmodels/TestThing.kt`
- `~/Projects/lightning-server-cc/server-mongo/src/test/kotlin/com/lightningkite/lightningdb/TextConditionTest.kt`
- `~/Projects/lightning-server-cc/server-mongo/src/test/kotlin/com/lightningkite/lightningdb/UniqueTest.kt`
- `~/Projects/lightning-server-cc/server-dynamodb/src/test/kotlin/com/lightningkite/lightningserver/db/DynamoDatabaseTests.kt`

### AI Observability Tests
- `~/Projects/lightning-server-ai-observability/demo/src/main/kotlin/com/lightningkite/lightningserver/demo/models/Comment.kt`
- `~/Projects/lightning-server-ai-observability/demo/src/main/kotlin/com/lightningkite/lightningserver/demo/models/BlogPost.kt`
- `~/Projects/lightning-server-ai-observability/demo/src/main/kotlin/com/lightningkite/lightningserver/demo/models/User.kt`
- `~/Projects/lightning-server-ai-observability/demo/src/main/kotlin/com/lightningkite/lightningserver/demo/models.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/ModificationExpressionTest.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/LLMChatEndpointsTest.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/ConditionExpressionTest.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/ConditionExpressionErrorMessageTest.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/ExternalChannelSupportTest.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/SystemChatEndpointsTest.kt`
- `~/Projects/lightning-server-ai-observability/ai/src/test/kotlin/com/lightningkite/lightningserver/ai/ConditionSerializationTest.kt`
- `~/Projects/lightning-server-ai-observability/typed/src/test/kotlin/com/lightningkite/lightningserver/typed/ModelRestUpdatesWebsocketTest.kt`

---

## Priority Files for Pattern Analysis

These files are especially valuable for learning model design patterns:

1. **ls-kiteui-starter/models.kt** - Clean starter template patterns
2. **lightning-credit/databaseModels/** - Rich domain models (transactions, rewards, promotions)
3. **circadia-admin/databaseModels/authmodels.kt** - Auth patterns
4. **service-abstractions/database-shared/** - Framework internals showing how paths work
5. **lightning-server-ai-observability/sessions-shared/** - Session/auth model patterns
6. **lightning-server-ai-observability/notifications-shared/** - Notification model patterns
