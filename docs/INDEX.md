# OpenRouter Tracker Documentation Hub

Welcome to the documentation hub for **OpenRouter Tracker**. This index organizes guides for users, engineers, security auditors, and contributors.

---

## 📖 User Documentation

- [User Feature Guide](user/FEATURE_GUIDE.md) — Comprehensive walkthrough of the Companion App, `systemSmall` & `systemMedium` desktop widgets, key management, and in-widget 1-click refresh.
- [Onboarding & FAQ](user/FAQ_AND_ONBOARDING.md) — 3-step setup guide, adding widgets to macOS desktop, resolving blank widgets, and common questions.
- [Security & API Key Management](user/SECURITY_AND_KEYS.md) — How OpenRouter keys are handled, Apple Keychain encryption, read-only vs. provisioned keys, and rate limits.

---

## 🛠️ Engineering & Architecture

- [System Architecture](engineering/ARCHITECTURE.md) — Deep architectural specification, App Group IPC container (`SharedStorage`), `AppIntents` execution lifecycle, WidgetKit timeline providers, and Mermaid dataflow diagrams.
- [Calculations & Formulas](engineering/CALCULATIONS.md) — Formal mathematical formulas for Usable Balance, Credit Limit burn percentage, and rate-limit headroom.
- [Development & Testing Guide](engineering/DEVELOPMENT.md) — Local Xcode & CLI build instructions, unit testing with coverage, automated retina screenshot pipeline, and DMG generation.

---

## 🏛️ Architecture Decision Records (ADRs)

- [ADR-0001: App Group Shared Storage](../adr/0001-app-group-shared-storage.md) — Rationale for IPC between the main companion app, widget extension, and intents via sandboxed App Group container.
- [ADR-0002: AppIntents Interactive Refresh](../adr/0002-app-intents-interactive-refresh.md) — Zero-daemon in-widget refresh architecture utilizing macOS `chronod` scheduling and `AppIntent`.

---

## 📋 Product & Planning

- [Product Specification](product/SPECIFICATION.md) — Locked behavioral contracts, OpenRouter API v1 endpoint specifications, payload schemas, and offline cache invariants.
- [Product Roadmap](product/ROADMAP.md) — Strategic roadmap (v1.1 Menu Bar status item, v1.2 Low-credit desktop notifications, v1.3 Burn pace forecasting).

---

## 🤖 Agent & Contributor Guidance

- [Domain Glossary (GLOSSARY.md)](../../GLOSSARY.md) — Ubiquitous language, OpenRouter metric nomenclature, and design invariants.
- [Agent Guidelines (AGENTS.md)](../../AGENTS.md) — Issue tracker and triage conventions for AI agents.
