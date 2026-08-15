Stand: 2026-08-15

# Zentrale TODO-Liste

Diese Datei ist die einzige Quelle für offene Entwicklungsaufgaben in Kernschmied.
Die [Roadmap](roadmap.md) beschreibt strategische Ziele, der
[Changelog](CHANGELOG.md) abgeschlossene Änderungen und die
[Release-Checkliste](development/release-checklist.md) wiederholbare
Freigabekriterien. Sie enthalten keine parallelen Aufgabenlisten.

## P0 - Laufzeit und Datenintegrität

- [x] Alembic-Zustand mit `alembic heads` und `alembic current` dynamisch
      verifizieren; abweichende Entwicklungsdatenbanken sichern und sauber auf den
      Repository-Head migrieren oder neu erzeugen.
- [x] Den minimalen Seed aus kanonischen Systemcontainern und Administrator
      idempotent verifizieren; fachliche Workspaces, Projekte und Chats nur über
      reguläre Anwendungsflüsse erzeugen.
- [x] Conversation- und Message-Persistenz an reale Hierarchieknoten anbinden;
      Create, Read und History einschließlich FK-Fehlerfällen testen.
- [x] Persistierte Gesprächsergebnisse übergeordneter Chats als begrenzten,
      nicht-instruktiven Kontext an Unterchat-Generierungen übergeben.
- [ ] Chat-History beim Öffnen zusätzlich im Browser-E2E absichern; Laden,
      Deduplizierung und persistente Elternbezüge sind durch Backendtests abgedeckt.
      Ein manueller Browser-Roundtrip einschließlich Knotenwechsel und Reload ist
      verifiziert; die repository-eigene E2E-Automatisierung fehlt noch.
- [ ] Eine kanonische Runtime-Konfigurationsauflösung außerhalb des `ChatService`
      einführen und mit Vertragstests für die Priorität
      `Request > Node > geerbte Hierarchie > globale Settings > Manifest > Bootstrap-Fallback`
      absichern; Fachservices und Provider konsumieren ausschließlich das
      unveränderliche effektive Ergebnis.
- [ ] Redundante Defaults zwischen Config-Definitionen, Hierarchie-Overrides,
      Manifesten, Bootstrap und Service-Konstruktoren entfernen. Insbesondere
      `models.max_output_tokens` darf pro Wert nur eine Source of Truth besitzen.
- [ ] Historische Widget-Registry-Duplikate einmalig, transaktional und
      verlustfrei konsolidieren; anschließend Eindeutigkeit in Datenbank und
      Registry erzwingen, statt Mehrdeutigkeiten nur im Resolver abzufedern.

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
- [ ] Benutzerstatus als zentralen Backend-Vertrag für `available`, `away`,
      `busy`, `dnd` und `offline` einschließlich Statusquelle, Zeitstempel,
      Persistenz- beziehungsweise Ablaufregeln und Berechtigungen modellieren;
      Sitzungs-Presence und UI verwenden ausschließlich diesen Vertrag.
- [ ] Die serverseitige Mention-Pipeline für `@Name` als verbindlichen Vertrag
      vervollständigen und testen: Benutzerauflösung, Hierarchiesichtbarkeit,
      Berechtigung und Erzeugung von Nachricht, Aufgabe oder Frage erfolgen vor
      dem Modellaufruf; das Modell darf Mentions nicht simulieren.
- [ ] Die umgesetzte SMTP-Outbox um Microsoft Graph, Retry und Dead-Letter
      erweitern; Credentials ausschließlich über einen Secret Store referenzieren
      und Zustellversuche sowie Provider-IDs revisionssicher auditieren.
- [ ] Config-v2 abschließen: präzise Schemas, Defaults, UI-Metadaten und
      Berechtigungen für die Platzhaltergruppen `knowledge`, `models`, `planning`,
      `tools`, `security` und `learning` definieren.
- [ ] Alle aktuellen Config-Definitionen fachlich mit genau einem Zustand
      `ACTIVE`, `PREPARED`, `RESTART_REQUIRED`, `UNSUPPORTED` oder `DEPRECATED`
      klassifizieren. Dabei die Abweichung zwischen der ursprünglichen
      147-Key-Inventur und derzeit 153 Definitionen auflösen; nur `ACTIVE` darf
      ohne Neustart editierbar sein und benötigt einen nachgewiesenen
      Runtime-Consumer.
- [ ] Config-Definitionen, Settings-Katalog, Frontend-Schema und
      Runtime-Consumer auf eine kanonische Definitionsquelle reduzieren. Der
      daraus generierte Katalog muss jeden Key genau einmal enthalten und darf
      keine nicht definierten Keys veröffentlichen.
- [ ] Den Settings-Katalog-Checker als CI-Prüfung integrieren, Zustands- und
      Consumer-Abdeckung erzwingen und im Frontend unbekannte, nicht aktive oder
      nicht editierbare Keys vor `PUT /api/v1/config` ablehnen.
- [ ] Die einheitliche Verwendung von `models.default_model` in ConfigService,
      Registry, Manifesten, Providern und Bootstrap verifizieren;
      `models.default_model_id` vollständig entfernen und ausschließlich
      kanonische Registry-IDs übergeben.
- [ ] Provider-/Modellabhängigkeiten im Settings-Frontend aus den
      Config-Metadaten ableiten und `model_select` vollständig anbinden.
- [ ] Ollama, OpenAI, Anthropic, Gemini und weitere Provider konsequent als
      Adapter ausführen: Sie übersetzen den bereits aufgelösten Request, ohne
      konfigurierte Werte durch eigene fachliche Defaults zu überschreiben.
- [ ] Sämtliche `tools.*`-Definitionen bis zur Tool-Ausführung verdrahten,
      insbesondere Timeout, Retry, Confirmation und Result-Processing; nicht
      konsumierte Werte bis zur Umsetzung als `PREPARED` oder `UNSUPPORTED`
      kennzeichnen und nicht editierbar ausliefern.
- [ ] Administrative Systemwidgets serverseitig nach Rollen und Berechtigungen
      filtern (ADR-0034).
- [ ] Autorisierung, Auditierung und Betriebsprofile vervollständigen;
      Berechtigungsänderungen und irreversible Aktionen müssen auditierbar sein.
      Eigentümeraktionen für Prompt, Konfiguration, Werkzeuge, Verschieben und
      Chat-Export sind serverseitig geprüft und im Hierarchiemenü angebunden;
      Benutzerprompts und Sidebar-Befehle folgen der effektiven Berechtigung.

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
- [ ] Einen `SelfKnowledgeService` für relativ stabile, berechtigungssicher
      freigegebene Benutzerinformationen bereitstellen, darunter Benutzername,
      Rollen, Sprache, Präferenzen und aktueller Hierarchiepfad; Herkunft und
      Revision jedes Fragments müssen nachvollziehbar sein.
- [ ] Einen `LiveContextService` für flüchtige, pro Chat-Anfrage neu ermittelte
      Daten bereitstellen, darunter Datum, Uhrzeit, Zeitzone, Präsenzstatus,
      Standort, Wetter und Kalenderstatus; fehlende oder nicht freigegebene
      Quellen werden explizit ausgelassen statt erfunden.
- [ ] `SelfKnowledgeService` und `LiveContextService` in den bestehenden
      `PromptResolver` integrieren, ohne zweite Prompt-Pipeline. Die deterministische
      Fragmentfolge lautet
      `settings → system_root → user → area → project → chat → subchat → self_knowledge → live_context`
      und wird mit Herkunfts-, Berechtigungs- und Reihenfolgetests abgesichert.

## P3 - Plattform-Backlog

- [x] Knotenoberflächen von System Root über Benutzer, Bereich und Projekt bis
      Chat auf einen gemeinsamen responsiven `NodeWorkspaceOverview` mit
      kontrastreicher Neutral-/Salbeipalette, einheitlichen Aktionen,
      Kennzahlen und Widget-Abschnitten konsolidieren.
- [x] Eigenen Benutzerknoten als persönliches Dashboard mit Profil- und
      Sicherheitsaktionen, sichtbaren Bereichen/Projekten, letzten Chats,
      Kontingenten und kompatiblen Registry-Widgets ausbauen; Dateien-Widget an
      den verpflichtenden `node_id`-Vertrag anbinden.
- [x] Live-Chat und Chat-Historie auf einen sicheren CommonMark-/GFM-Renderer
      vereinheitlichen, Lightmode-Kontrast gesendeter Nachrichten erhöhen,
      Roh-HTML sperren und Bild-, Audio- sowie Videoausgabe mit fokussierten
      Frontendtests vorbereiten.
- [x] Kontextbezogene letzte Projekte, Chats und Unterchats je Hierarchieebene
      aus dem bestehenden Recent-Speicher ableiten und ausschließlich gegen den
      aktuell sichtbaren, berechtigungsprojizierten Teilbaum anzeigen.
- [x] Bereiche und Projekte um vollständige direkte Projekt-/Chat-Sammlungen im
      gemeinsamen Kartenaufbau des Benutzerarbeitsbereichs ergänzen und die
      kontextbezogenen Recents als zusätzliche Schnellzugriffe erhalten.
- [x] Bereichs-, Projekt- und Chatkontingente pro Benutzer mit Rollenstandard,
      festem Limit und unbegrenzter Nutzung administrierbar, persistierbar und
      in der serverseitigen Hierarchieerstellung wirksam machen.
- [x] Persistente Chat-History berechtigungsgeprüft vollständig leeren, einzelne
      Nachrichten löschen und nach einem gewählten Stand kürzen; Antwortbezüge
      und monotone Sequenzen durch Repository- und API-Tests absichern.
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
- [ ] Temporäre `tmp_*`-, Diagnose- und Analyse-Skripte nach Abschluss der
      Config-/Runtime-Konsolidierung inventarisieren, benötigte Werkzeuge nach
      `tools/` überführen und rein temporäre Dateien samt sensiblen Ausgaben
      sicher entfernen.

## Pflege

- Neue Aufgaben werden ausschließlich hier eingetragen und mit Priorität sowie
  überprüfbarem Ergebnis formuliert.
- Strategische Änderungen werden zusätzlich in der Roadmap gepflegt;
  abgeschlossene wesentliche Änderungen im Changelog.
- Technische Zustandsberichte dürfen auf Aufgaben hier verweisen, aber keine
  eigene Aufgabenliste führen.
