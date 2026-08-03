# ADR-0004: Sicherheitsprofile und Betriebsmodi

* **Status:** Angenommen – konsolidiert
* **Datum der ursprünglichen Entscheidung:** 2026-07-27
* **Letzte Überarbeitung:** 2026-08-03
* **Entscheidungsträger:** Kernschmied-Architekturteam
* **Ersetzt:** Keine
* **Ersetzt durch:** Keine
* **Verwandte Dokumente:**

  * `documentation/leitkonzept.md`
  * `documentation/architecture/contracts.md`
  * `documentation/architecture/contract-refactoring.md`
  * `documentation/architecture/bootstrap.md`
  * `documentation/architecture/security.md`
  * `documentation/architecture/decisions/ADR-0002-configuration-architecture-and-runtime-initialization.md`
  * `documentation/architecture/decisions/ADR-0003-registry-based-extension-architecture.md`

---

# 1. Entscheidung in Kurzform

Kernschmied verwendet drei klar definierte Betriebsprofile mit unterschiedlichen Sicherheitsanforderungen.

Die Anwendung bleibt funktional identisch, während ausschließlich die Sicherheits- und Betriebsrichtlinien an das jeweilige Einsatzszenario angepasst werden.

Die drei unterstützten Betriebsprofile sind:

* **development**
* **intranet**
* **internet**

Die Auswahl des Profils erfolgt ausschließlich über die Bootstrap-Konfiguration.

Das aktive Profil bestimmt unter anderem:

* Authentifizierung,
* Autorisierung,
* Transportverschlüsselung,
* Sessionverwaltung,
* Sicherheitsrichtlinien,
* Logging,
* Auditierung,
* Rate Limiting,
* verfügbare Debugfunktionen,
* Standardkonfigurationen.

Geschäftslogik und Fachkonfiguration gehören ausdrücklich **nicht** zum Sicherheitsprofil.

---

# 2. Kontext

Kernschmied soll über viele Jahre in unterschiedlichen Umgebungen betrieben werden.

Die gleiche Anwendung kann eingesetzt werden:

* lokal auf einem Entwicklerrechner,
* in einem geschützten Unternehmensnetz,
* als interne Unternehmensplattform,
* in einer DMZ,
* als Internetanwendung,
* später auch mandantenfähig.

Diese Umgebungen unterscheiden sich erheblich hinsichtlich:

* Bedrohungslage,
* Benutzeranzahl,
* Compliance-Anforderungen,
* Administrationsaufwand,
* Infrastruktur,
* Verfügbarkeit.

Ein einziges Sicherheitsmodell würde entweder:

* lokale Entwicklung unnötig erschweren,

oder

* produktive Systeme unzureichend absichern.

---

# 3. Problemstellung

Ohne klar definierte Betriebsprofile entstehen häufig inkonsistente Installationen.

## 3.1 Entwicklung und Produktion unterscheiden sich zufällig

Entwickler deaktivieren Sicherheitsmechanismen temporär.

Diese Änderungen gelangen später versehentlich in produktive Umgebungen.

---

## 3.2 Sicherheitsregeln werden im Code verteilt

Beispiele:

```python
if DEBUG:
    ...

if os.getenv("LOCAL"):
    ...

if profile == "internet":
    ...
```

Mit der Zeit entstehen widersprüchliche Regeln.

---

## 3.3 Fachlogik wird mit Infrastruktur vermischt

Beispiele:

* Modellauswahl
* Firmenname
* Branding
* Workflowdefinitionen

werden über `.env` gesteuert, obwohl sie eigentlich Laufzeitkonfiguration darstellen.

---

## 3.4 Unterschiedliche Installationen

Jede Installation entwickelt eigene Sonderfälle.

Dadurch entstehen:

* schwer reproduzierbare Fehler,
* unterschiedliche Sicherheitsniveaus,
* hoher Supportaufwand.

---

## 3.5 Fehlende Mindeststandards

Ohne verbindliche Profile können sicherheitskritische Funktionen versehentlich deaktiviert werden.

Beispiele:

* HTTPS
* Sessionverwaltung
* CSRF-Schutz
* Rate Limiting
* Auditierung

---

# 4. Aktueller Zustand – IST

Kernschmied besitzt bereits die grundlegende Trennung zwischen Bootstrap- und Laufzeitkonfiguration.

## 4.1 Bereits vorhanden

* Bootstrap-Konfiguration
* Runtime-Konfiguration
* Development-Profil
* Capability-System
* zentrale Konfigurationsverwaltung
* serverseitige Autorisierung
* strukturierte Fehlerantworten
* SSE-Kommunikation
* revisionsbasierte Konfiguration

---

## 4.2 Teilweise implementiert

* DevelopmentIdentityMiddleware
* Authentifizierungsstrategie je Profil
* Health- und Readiness-Prüfungen
* Audit-Logging
* Rate Limiting
* Sessionverwaltung
* Sicherheitsheader
* HTTPS-Zwang
* CSRF-Schutz
* Rollenmodell

---

## 4.3 Noch nicht vollständig umgesetzt

* vollständige Profilvalidierung
* automatische Mindestanforderungen
* Sicherheitsdiagnose
* Compliance-Prüfung
* Profilmigration
* Security Self Check
* zentrale Security Policy Engine

---

# 5. Zielzustand – SOLL

Das aktive Betriebsprofil bestimmt ausschließlich sicherheitsrelevante Infrastrukturregeln.

```text
Bootstrap

        │

        ▼

Deployment Profile

        │

        ▼

Security Policy

        │

        ▼

Infrastructure Services

        │

        ▼

Runtime
```

Geschäftslogik bleibt davon vollständig getrennt.

---

# 6. Entscheidung

Kernschmied definiert dauerhaft drei Betriebsprofile.

## 6.1 Development

Lokale Entwicklung.

Ziel:

* maximale Entwicklerproduktivität
* einfache Inbetriebnahme
* reproduzierbare Tests

---

### Eigenschaften

* lokale Identität möglich
* vereinfachte Anmeldung
* HTTP erlaubt
* reduzierte Sicherheitsmechanismen
* Debugfunktionen verfügbar
* detaillierte Fehlermeldungen
* lokale Datenbank zulässig
* Hot Reload
* vereinfachte Zertifikate

---

### Einschränkungen

Auch im Development gelten weiterhin:

* serverseitige Autorisierung
* Vertragsvalidierung
* strukturierte Fehler
* Registry-Validierung
* Manifestvalidierung
* keine dynamische Codeausführung
* keine Umgehung technischer Sicherheitsgrenzen

---

## 6.2 Intranet

Geschützter Unternehmensbetrieb.

Ziel:

* komfortable Nutzung
* Unternehmenssicherheit
* zentrale Verwaltung

---

### Eigenschaften

* verpflichtende Authentifizierung
* Rollenmodell
* Auditierung
* Unternehmensidentitäten
* Sessionverwaltung
* TLS innerhalb der Infrastruktur
* Backupstrategie
* zentrale Konfiguration

---

### Typische Identitätsquellen

* Active Directory
* LDAP
* OpenID Connect
* Unternehmens-SSO
* zukünftige Authentifizierungsprovider

---

## 6.3 Internet

Öffentlich erreichbare Installation.

Ziel:

* maximale Sicherheit
* minimale Angriffsfläche
* vollständige Nachvollziehbarkeit

---

### Eigenschaften

* HTTPS verpflichtend
* sichere Sessions
* Rate Limiting
* CSRF-Schutz
* Security Header
* vollständiges Audit
* Härtung
* sichere Cookies
* verschlüsselte Kommunikation
* restriktive CORS-Regeln

---

# 7. Architekturprinzip

Die ursprüngliche Aussage

> unterschiedliche Umgebungen benötigen unterschiedliche Sicherheit

wird verbindlich präzisiert zu:

> Das Betriebsprofil definiert ausschließlich Infrastruktur- und Sicherheitsrichtlinien.
> Geschäftslogik, Hierarchien, Modelle, Tools und UI-Schemas bleiben profilunabhängig.

---

# 8. Bootstrap-Verantwortung

Das aktive Profil gehört zur Bootstrap-Konfiguration.

Beispiel:

```text
deployment_profile = development
deployment_profile = intranet
deployment_profile = internet
```

Eine Änderung des Profils erfordert einen Neustart der Anwendung.

---

# 9. Was NICHT profilabhängig ist

Folgende Bereiche gehören ausdrücklich zur Runtime-Konfiguration:

* Modelle
* Tools
* Promptdefinitionen
* Ressourcen
* Widgets
* Workflows
* Branding
* Firmeninformationen
* Hierarchien
* Knotentypen
* Ressourcentypen
* Benutzeroberfläche

Diese Informationen werden nicht über `.env` gesteuert.

---

# 10. Sicherheitsrichtlinien

Das Profil aktiviert definierte Sicherheitsrichtlinien.

Beispiele:

* Authentifizierung
* Sessionverwaltung
* Passwortregeln
* HTTPS
* TLS
* CORS
* CSP
* HSTS
* Auditierung
* Logging
* Tokenverwaltung
* Cookie-Richtlinien

---

# 11. Identitätsmodell

Die Identität wird über austauschbare Authentifizierungsprovider bereitgestellt.

Beispiele:

```text
Development Identity
LDAP
Active Directory
OIDC
Azure AD
Keycloak
```

Die Authentifizierungsimplementierung wird über die Registry bereitgestellt.

Die Sicherheitsregeln des Profils bestimmen, welche Provider zulässig sind.

---

# 12. Autorisierung

Die Autorisierung bleibt unabhängig vom Betriebsprofil.

Alle Benutzeraktionen werden serverseitig geprüft.

Beispiele:

* Toolaufrufe
* Ressourcenänderungen
* Hierarchieänderungen
* Modellauswahl
* Workflowausführung
* Registryverwaltung

Development reduziert niemals die serverseitige Berechtigungsprüfung.

---

# 13. HTTPS

## Development

HTTP erlaubt.

HTTPS optional.

---

## Intranet

TLS empfohlen.

Unternehmenszertifikate zulässig.

---

## Internet

HTTPS verpflichtend.

Unsichere Verbindungen werden abgelehnt.

---

# 14. Sessionverwaltung

Development:

* vereinfachte Sessions möglich.

Intranet:

* sichere Unternehmenssessions.

Internet:

* sichere Cookies,
* HttpOnly,
* SameSite,
* Sessionrotation,
* Timeout,
* Logout-Invalidierung.

---

# 15. Logging

Development:

* ausführliche Logs,
* Debugausgaben,
* Stacktraces.

Intranet:

* strukturierte Logs,
* Benutzerbezug.

Internet:

* sicherheitsorientierte Logs,
* Datenschutz,
* keine sensitiven Informationen.

---

# 16. Auditierung

Development:

Audit optional.

Intranet:

Änderungen werden protokolliert.

Internet:

vollständige Auditierung sicherheitsrelevanter Aktionen.

Audit umfasst unter anderem:

* Konfigurationsänderungen,
* Registryänderungen,
* Rollenänderungen,
* Ressourcenänderungen,
* Workflowänderungen.

---

# 17. Rate Limiting

Development:

deaktiviert oder stark gelockert.

Intranet:

angepasste Unternehmensgrenzen.

Internet:

verpflichtend.

---

# 18. Sicherheitsheader

Internet aktiviert standardmäßig:

* CSP
* HSTS
* X-Content-Type-Options
* Referrer Policy
* Permissions Policy
* Frame Options

Development kann diese lockern.

---

# 19. Geheimnisse

Secrets gehören ausschließlich zur Bootstrap-Konfiguration.

Beispiele:

* API-Schlüssel
* Datenbankkennwörter
* Signaturschlüssel
* Zertifikate
* OAuth-Secrets

Secrets werden niemals:

* in Runtime-Konfigurationen,
* Registrydefinitionen,
* Ressourcen,
* Promptdefinitionen,
* Widgets

gespeichert.

---

# 20. Sicherheitsdiagnose

Health- und Readiness-Endpunkte dürfen den Sicherheitszustand anzeigen.

Beispiele:

* aktives Profil
* HTTPS aktiv
* Datenbank erreichbar
* Registries initialisiert
* Konfigurationsrevision
* erforderliche Dienste verfügbar

Nicht ausgegeben werden:

* Passwörter
* Tokens
* API-Schlüssel
* Zertifikatsinhalte

---

# 21. Deploymentwechsel

Ein Wechsel zwischen Profilen erfolgt ausschließlich über die Bootstrap-Konfiguration.

Migration:

```text
development
        │
        ▼
intranet
        │
        ▼
internet
```

Die Runtime-Datenbank bleibt dabei unverändert.

---

# 22. Auswirkungen auf Registries

Registries bleiben profilunabhängig.

Das Profil entscheidet lediglich,

* welche Registries aktiviert werden,
* welche Provider zulässig sind,
* welche Integrationen verwendet werden dürfen.

---

# 23. Auswirkungen auf den Effective Context

Der Effective Context enthält keine sicherheitskritischen Bootstrap-Geheimnisse.

Er kann jedoch Informationen enthalten wie:

* aktives Deploymentprofil,
* verfügbare Capabilities,
* Sicherheitsstufe,
* erlaubte Aktionen.

---

# 24. Positive Konsequenzen

## Klare Verantwortlichkeiten

Bootstrap startet die Plattform.

Runtime definiert ihr Verhalten.

---

## Sichere Standardwerte

Produktionssysteme erhalten automatisch strengere Mindestanforderungen.

---

## Einheitliche Installationen

Alle Installationen desselben Profils verhalten sich konsistent.

---

## Bessere Wartbarkeit

Sicherheitslogik bleibt zentral.

---

## Höhere Testbarkeit

Jedes Profil kann gezielt getestet werden.

---

## Zukunftssicherheit

Neue Authentifizierungs- oder Sicherheitsmechanismen können ergänzt werden, ohne Geschäftslogik zu verändern.

---

# 25. Negative Konsequenzen

## Höherer Initialaufwand

Alle Profile müssen definiert und getestet werden.

---

## Mehr Konfigurationsregeln

Bootstrap und Runtime müssen sauber getrennt bleiben.

---

## Zusätzliche Dokumentation

Jedes Profil benötigt klare Betriebsrichtlinien.

---

# 26. Verworfene Alternativen

## Eine einzige Sicherheitskonfiguration

### Vorteile

* einfach.

### Nachteile

* unflexibel,
* ungeeignet für unterschiedliche Einsatzszenarien.

**Entscheidung:** Verworfen.

---

## Vollständig frei konfigurierbare Sicherheit

### Vorteile

* maximale Flexibilität.

### Nachteile

* inkonsistente Installationen,
* schwer prüfbar,
* erhöhte Fehlerrisiken.

**Entscheidung:** Verworfen.

---

## Sicherheitsregeln ausschließlich über `.env`

### Vorteile

* schnell umzusetzen.

### Nachteile

* unübersichtlich,
* fehleranfällig,
* keine klaren Mindeststandards.

**Entscheidung:** Verworfen.

---

# 27. Migrationsstrategie vom IST zum SOLL

## Phase 1

Bootstrap-Profil konsolidieren.

## Phase 2

Security Policies zentralisieren.

## Phase 3

Authentifizierungsprovider vereinheitlichen.

## Phase 4

Auditierung vervollständigen.

## Phase 5

Rate Limiting und Sessionverwaltung abschließen.

## Phase 6

Internet-Härtung vervollständigen.

---

# 28. Abnahmekriterien

Die Entscheidung gilt als umgesetzt, wenn:

* genau drei unterstützte Betriebsprofile existieren,
* Bootstrap und Runtime vollständig getrennt sind,
* Geschäftslogik profilunabhängig bleibt,
* Sicherheitsrichtlinien zentral verwaltet werden,
* HTTPS im Internetprofil verpflichtend ist,
* serverseitige Autorisierung immer aktiv bleibt,
* Secrets ausschließlich in der Bootstrap-Konfiguration liegen,
* Auditierung und Logging profilgerecht arbeiten,
* Sicherheitsdiagnosen verfügbar sind,
* neue Sicherheitsprovider über Registries integriert werden können.

---

# 29. Auswirkungen auf Kernschmied

## Backend

Zielbereiche:

```text
backend/app/bootstrap/
backend/app/security/
backend/app/auth/
backend/app/contracts/
backend/app/config/
backend/app/api/
```

## Frontend

Zielbereiche:

```text
frontend/src/api/
frontend/src/auth/
frontend/src/security/
frontend/src/contracts/
```

## Dokumentation

Zielbereiche:

```text
documentation/architecture/security.md
documentation/architecture/bootstrap.md
documentation/architecture/contracts.md
```

---

# 30. Verbindliche Architekturregeln

1. Genau drei offizielle Betriebsprofile werden unterstützt.
2. Das Profil gehört ausschließlich zur Bootstrap-Konfiguration.
3. Geschäftslogik ist profilunabhängig.
4. Runtime-Konfiguration wird nicht über `.env` gesteuert.
5. Secrets werden niemals in Runtime-Daten gespeichert.
6. Serverseitige Autorisierung ist immer verpflichtend.
7. HTTPS ist im Internetprofil verpflichtend.
8. Discovery bedeutet niemals Freigabe.
9. Registry- und Sicherheitsregeln bleiben getrennt.
10. Sicherheitsmechanismen dürfen durch Runtime-Konfiguration nicht abgeschwächt werden.
11. Health-Endpunkte geben keine sensitiven Informationen preis.
12. Neue Sicherheitsprovider werden über Registries integriert.
13. Auditierung ist revisions- und rollenbasiert.
14. Sicherheitsprofile besitzen dokumentierte Mindestanforderungen.
15. Bootstrap und Runtime bleiben dauerhaft klar getrennt.

---

# 31. Endgültige Entscheidung

Kernschmied verwendet dauerhaft klar definierte Sicherheitsprofile und Betriebsmodi.

Die Plattform kombiniert:

```text
Bootstrap-Konfiguration
+
Deployment-Profil
+
Security Policies
+
Registry-basierte Authentifizierungsprovider
+
Serverseitige Autorisierung
+
Auditierung
+
Revisionsverwaltung
+
Runtime-Konfiguration
```

Dadurch kann dieselbe Anwendung sicher als lokale Entwicklungsumgebung, als Unternehmensplattform oder als öffentlich erreichbares Produktionssystem betrieben werden, ohne die Geschäftslogik oder die Architektur verändern zu müssen.
