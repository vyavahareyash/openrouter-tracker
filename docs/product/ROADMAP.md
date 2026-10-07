# Product Roadmap

---

## Current Release: v1.0.0 (Foundation)
- [x] Native macOS 14 Sonoma Desktop Widget (`systemSmall` & `systemMedium`).
- [x] Zero-Daemon background architecture using macOS `chronod`.
- [x] Interactive 1-click in-widget refresh via `AppIntents`.
- [x] Multi-key management companion app with custom nicknames.
- [x] Retina DMG distribution packaging.

---

## Upcoming Releases

### v1.1.0 (Menu Bar Companion & Status Item)
- [ ] Lightweight Menu Bar extra (`NSStatusItem`) showing live balance in the macOS system tray.
- [ ] Dropdown popover with quick key switching and instant refresh.
- [ ] Dockless option (run as menu-bar only utility).

### v1.2.0 (Proactive Desktop Notifications)
- [ ] Background depletion checks alerting when remaining credits fall below \$5.00 or key limit reaches 95%.
- [ ] Rate limit warning notification when token quotas are saturated.

### v1.3.0 (Analytics & Spend Forecasting)
- [ ] Weekly and daily spend velocity calculation.
- [ ] Burn-rate forecasting: estimate days remaining based on recent agent/script velocity.
- [ ] Exportable CSV/JSON usage audits.
