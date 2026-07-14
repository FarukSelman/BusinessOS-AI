# ADR-0005 - Multi-Tenant Membership

## Status

Accepted

## Decision

A user may belong to multiple businesses.

Relationships between users and businesses will be managed through a Membership entity.

## Motivation

This approach enables:

- Multi-business accounts
- Future team collaboration
- Flexible role management
- Better scalability

## Consequences

Business permissions will be evaluated through memberships rather than directly from users.