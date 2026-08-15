Stand: 2026-08-15

# Zentrale TODO-Liste

Diese Datei ist die einzige Quelle für offene Entwicklungsaufgaben in Kernschmied.
Die [Roadmap](roadmap.md) beschreibt strategische Ziele, der
[Changelog](CHANGELOG.md) abgeschlossene Änderungen und die
[Release-Checkliste](development/release-checklist.md) wiederholbare
Freigabekriterien. Sie enthalten keine parallelen Aufgabenlisten.

## P0 - Laufzeit und Datenintegrität

- [ ] Alembic-Zustand mit `alembic heads` und `alembic current` dynamisch
      verifizieren; abweichende Entwicklungsdatenbanken sichern und sauber auf den
      Repository-Head migrieren oder neu erzeugen.
- [ ] Den minimalen Seed aus kanonischen Systemcontainern und Administrator
      idempotent verifizieren; fachliche Workspaces, Projekte und Chats nur über
      reguläre Anwendungsflüsse erzeugen.
- [ ] Conversation- und Message-Persistenz an reale Hierarchieknoten anbinden;
      Create, Read und History einschließlich FK-Fehlerfällen testen.
- [ ] Chat-History beim Öffnen zusätzlich im Browser-E2E absichern; Laden,
      Deduplizierung und persistente Elternbezüge sind durch Backendtests abgedeckt.

## P1 - Verträge, Konfiguration und Sicherheit

- [ ] Quotenprüfung und Hierarchieerstellung in einer atomaren Transaktion mit
      geeigneter Sperrstrategie ausführen; parallele Erstellen-Anfragen müssen
      die konfigurierte Rollenquote zuverlässig einhalten.
- [ ] Login, Selbstregistrierung, Abmeldung und erneute Anmeldung als vollständigen
      Browser-E2E-Test gegen den anonymen Bootstrap-Vertrag absichern; dabei den
      Wechsel vom Adminbaum zum ausschließlich eigenen Gastbaum sowie Profil- und
      Präferenz-Self-Service und den persönlichen Benutzerarbeitsbereich ohne
      technische Schema-/Prompt-Daten prüfen. Passwort-Policyfehler in Admin- und
      Selbstregistrierung sind bereits durch Route- und Komponententests abgedeckt.
- [ ] OpenAPI-Artefakte aus der tatsächlich laufenden FastAPI-Anwendung neu
      erzeugen und den Hierarchie-Endpunkt gegen `HierarchyTreeResponse` prüfen.
- [ ] Bootstrap als einzigen festen fachlichen Frontend-Einstieg durchsetzen und
      die Laufzeitvalidierung aller öffentlichen Frontendverträge vervollständigen.
- [ ] `ChatRequest` und SSE-Ereignisse in Backend und Frontend vereinheitlichen;
      Mention-Defaults und persistierte Assistant-Metadaten sind bereits strikt
      als `MentionReference` beziehungsweise JSON-Werte typisiert.
- [ ] Mention-Statuswechsel und Empfängerzugriffe vollständig auditieren; dabei
      die Trennung zwischen System-Autoresponder und menschlichen Administratoren
      als Regressionstest erhalten sowie Ersteller, Empfänger, Hierarchieknoten,
      vorherigen und neuen Status nachvollziehbar erfassen.
- [ ] Die umgesetzte SMTP-Outbox um Microsoft Graph, Retry und Dead-Letter
      erweitern; Credentials ausschließlich über einen Secret Store referenzieren
      und Zustellversuche sowie Provider-IDs revisionssicher auditieren.
- [ ] Config-v2 abschließen: präzise Schemas, Defaults, UI-Metadaten und
      Berechtigungen für die Platzhaltergruppen `knowledge`, `models`, `planning`,
      `tools`, `security` und `learning` definieren.
- [ ] Die einheitliche Verwendung von `models.default_model` in Registry,
      Providern und Bootstrap verifizieren; `models.default_model_id` vollständig
      entfernen.
- [ ] Den Settings-Katalog-Checker als CI-Prüfung integrieren und im Frontend
      unbekannte Keys vor `PUT /api/v1/config` ablehnen.
- [ ] Provider-/Modellabhängigkeiten im Settings-Frontend aus den
      Config-Metadaten ableiten und `model_select` vollständig anbinden.
- [ ] Administrative Systemwidgets serverseitig nach Rollen und Berechtigungen
      filtern (ADR-0034).
- [ ] Autorisierung, Auditierung und Betriebsprofile vervollständigen;
      Berechtigungsänderungen und irreversible Aktionen müssen auditierbar sein.

## P2 - Hierarchie, Suche und Dateien

- [ ] Aus dem persönlichen Eingang direkt zum zugehörigen Chatkontext navigieren;
      Antworten und Folge-Nachrichten besitzen bereits persistente Elternbezüge.
- [ ] Einen kompakten Ungelesen-Zähler-Endpunkt für Benutzeranfragen bereitstellen
      und Polling durch SSE- oder WebSocket-Aktualisierungen mit belastbarem
      Reconnect-Verhalten ersetzen.
- [ ] Das Postfach nach den umgesetzten Filtern, Sortier-, Archivierungs- und
      Löschaktionen um direkte interne Nachrichten, Volltextsuche, Pagination und einen
      vollständigen Postfacharbeitsbereich ergänzen; anschließend eingehende
      E-Mail über verifizierte Adresszuordnung und sichere Provider-Webhooks
      anbinden.
- [ ] Verbleibende Hierarchie-Mutationen im Frontend an Rename-, Move- und
      Delete-Endpunkte anbinden und lokale Zustandsaktualisierungen testen;
      Create für eigene Bereiche, Projekte und Chats ist umgesetzt.
- [ ] Metadatenbasierte `assigned_user_ids` durch relationale
      Workspace-Mitgliedschaften ersetzen und Zuweisungen im Knoten-Editor über
      Benutzernamen auswählbar machen.
- [ ] Die globale Sidebar-Suche um serverseitig indizierte Knoten- und
      Chat-Inhalte erweitern.
- [ ] `include_inherited` in `GET /files` implementieren und geerbte Dateien
      unter Beachtung der Hierarchieberechtigungen testen.
- [ ] Einen serverseitigen Context Resolver für Tenant, Benutzer,
      Hierarchiepfad und effektive Revisionen bereitstellen.

## P3 - Plattform-Backlog

- [ ] `SchemaRenderer` um Formularbindung, Aktionen und Sichtbarkeitsregeln
      vervollständigen.
- [ ] Widget-Pool und persistente Layoutverwaltung vervollständigen.
- [ ] Prompt-Revisionen, Vorschau und reproduzierbare Prompt-Testläufe ergänzen.
- [ ] Datenschutzprofile technisch durchsetzen und testen.
- [ ] Multi-Tenancy mit Memberships, Tenant-Administration und Tenant-Policies
      entwerfen und implementieren.
- [ ] Nachrichtenvolltext, semantische Suche und Indexierungsrichtlinien
      umsetzen.
- [ ] Action-Registry um Smart Actions und Risikoklassen erweitern.
- [ ] Integrationen über Webhooks und Connector-Manifeste definieren.
- [ ] PostgreSQL-Betrieb, Multi-Worker-Invalidierung und Rate-Limiting für die
      Skalierung vorbereiten.

## Pflege

- Neue Aufgaben werden ausschließlich hier eingetragen und mit Priorität sowie
  überprüfbarem Ergebnis formuliert.
- Strategische Änderungen werden zusätzlich in der Roadmap gepflegt;
  abgeschlossene wesentliche Änderungen im Changelog.
- Technische Zustandsberichte dürfen auf Aufgaben hier verweisen, aber keine
  eigene Aufgabenliste führen.
