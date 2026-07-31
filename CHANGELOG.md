name: Fehlerbericht
description: Einen reproduzierbaren Fehler in Kernschmied melden
title: "[Bug]: "
labels:

- bug
  body:
- type: markdown
  attributes:
  value: |
  Danke für den Fehlerbericht. Bitte keine Secrets, Tokens oder personenbezogenen Daten einfügen. Sicherheitsprobleme müssen gemäß SECURITY.md vertraulich gemeldet werden.
- type: input
  id: version
  attributes:
  label: Version oder Commit
  placeholder: z. B. 0.1.0 oder Commit-SHA
  validations:
  required: true
- type: dropdown
  id: area
  attributes:
  label: Betroffener Bereich
  options: - Backend - Frontend - Bootstrap - Hierarchie - UI-Schema oder SchemaRenderer - Modelle oder Modell-Registry - Tools oder Tool-Registry - Chat oder SSE - Konfiguration - Startskripte - Dokumentation - Unbekannt
  validations:
  required: true
- type: textarea
  id: description
  attributes:
  label: Fehlerbeschreibung
  description: Was ist passiert?
  validations:
  required: true
- type: textarea
  id: reproduce
  attributes:
  label: Schritte zur Reproduktion
  placeholder: | 1. Anwendung starten 2. ... 3. Fehler beobachten
  validations:
  required: true
- type: textarea
  id: expected
  attributes:
  label: Erwartetes Verhalten
  validations:
  required: true
- type: textarea
  id: actual
  attributes:
  label: Tatsächliches Verhalten
  validations:
  required: true
- type: textarea
  id: environment
  attributes:
  label: Umgebung
  placeholder: |
  Betriebssystem:
  Python:
  Node.js:
  npm:
  Betriebsprofil:
  validations:
  required: true
- type: textarea
  id: logs
  attributes:
  label: Relevante Logs
  description: Bitte Secrets, Tokens, Pfade mit persönlichen Daten und personenbezogene Inhalte entfernen.
  render: shell
- type: checkboxes
  id: checks
  attributes:
  label: Bestätigung
  options: - label: Ich habe nach bestehenden Issues gesucht.
  required: true - label: Der Bericht enthält keine Secrets oder personenbezogenen Daten.
  required: true - label: Es handelt sich nicht um eine vertraulich zu meldende Sicherheitslücke.
  required: true
