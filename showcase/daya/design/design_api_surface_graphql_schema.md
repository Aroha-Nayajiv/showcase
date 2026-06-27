# GraphQL Schema & Type Definitions

### 1.1 Scalar Definitions

To ensure type safety and compliance with financial and regulatory standards, the following custom scalars are defined:

- **CurrencyCode**: An ISO 4217 three-letter currency code (e.g., USD).
- **UUIDv4**: A version 4 UUID string, used for all primary identifiers to ensure distributed uniqueness and prevent enumeration attacks.
- **PositiveDecimal**: A non-negative decimal number with up to 2 decimal places, used for all monetary