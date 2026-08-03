# Duplicate group duplicate-009

---
Source: docs/architecture/settings-catalog.md (sha256: 69594c72af6f865720c0f863a1067c5dd15dfbf520371e087058edae9866a089)

# Kernschmied Settings-Katalog

Der Settings-Katalog trennt vier Quellen:

- `config`: einfache, validierte und revisionspflichtige Werte aus `/api/v1/config`
- `resource`: verwaltete Ressourcen mit eigenen CRUD-Endpunkten
- `runtime`: schreibgeschützte Laufzeit- und Diagnosedaten
- `local_preference`: lokale UI-Präferenzen

Statuswerte:

- `available`: der Zielendpunkt existiert bereits oder der Wert kann über `/config` erreichbar gemacht werden
- `prepared`: Metadaten und Navigation sind vorhanden; die Ressource ist noch nicht vollständig umgesetzt
- `planned`: architektonisch vorgesehen, aber noch ohne produktiven Endpunkt

Der Katalog ist keine Berechtigungsentscheidung. Jeder Zielendpunkt autorisiert die Aktion erneut serverseitig.

## Sicherheitsgrundsatz

Kernschmied darf Erfahrungen protokollieren, Muster erkennen und Vorschläge erzeugen. Produktive Prompts, Sicherheitsgrenzen, Berechtigungen, Tools, Provider und Schemas dürfen nicht unbemerkt automatisch verändert werden.


---
Source: wiki/architecture/settings-catalog.md (sha256: 69594c72af6f865720c0f863a1067c5dd15dfbf520371e087058edae9866a089)

# Kernschmied Settings-Katalog

Der Settings-Katalog trennt vier Quellen:

- `config`: einfache, validierte und revisionspflichtige Werte aus `/api/v1/config`
- `resource`: verwaltete Ressourcen mit eigenen CRUD-Endpunkten
- `runtime`: schreibgeschützte Laufzeit- und Diagnosedaten
- `local_preference`: lokale UI-Präferenzen

Statuswerte:

- `available`: der Zielendpunkt existiert bereits oder der Wert kann über `/config` erreichbar gemacht werden
- `prepared`: Metadaten und Navigation sind vorhanden; die Ressource ist noch nicht vollständig umgesetzt
- `planned`: architektonisch vorgesehen, aber noch ohne produktiven Endpunkt

Der Katalog ist keine Berechtigungsentscheidung. Jeder Zielendpunkt autorisiert die Aktion erneut serverseitig.

## Sicherheitsgrundsatz

Kernschmied darf Erfahrungen protokollieren, Muster erkennen und Vorschläge erzeugen. Produktive Prompts, Sicherheitsgrenzen, Berechtigungen, Tools, Provider und Schemas dürfen nicht unbemerkt automatisch verändert werden.


