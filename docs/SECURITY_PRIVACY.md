# Security and Privacy

Persistent memory increases capability and also increases privacy risk. Treat the database as sensitive user data.

## Defaults

- no API secrets in memories;
- no raw camera/microphone recording by this package;
- no automatic cloud upload;
- local database by default;
- portable memory is unencrypted unless the owner encrypts the volume;
- integrity checks detect file changes but do not provide confidentiality.

## Recommended production controls

Use full-disk or full-volume encryption, OS user permissions, application authentication, per-user stores or strong row-level authorization, a secret manager for credentials, signed backups, retention policies, explicit deletion controls, audit logging for exports, and consent before storing personal/biometric information.

## Prompt injection and memory poisoning

Do not automatically treat every model-generated sentence as a durable fact. Separate raw conversation evidence, verified facts, inferred summaries, and external untrusted content. Store provenance in `metadata` and rank verified information appropriately.

## USB loss

A lost unencrypted drive exposes the database. Encryption is mandatory for sensitive deployments.

## Data deletion

SQLite deletion semantics and flash-media wear leveling mean high-assurance physical erasure may require destroying the encryption key or media, depending on the threat model. This project does not claim forensic secure deletion from commodity flash storage.
