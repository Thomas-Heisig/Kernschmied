name: Funktionsvorschlag
description: Eine neue Funktion oder Verbesserung für Kernschmied vorschlagen
title: "[Feature]: "
labels:

- enhancement
  body:
- type: markdown
  attributes:
  value: |
  Beschreibe möglichst den Anwendungsfall statt nur eine technische Lösung. Größere Änderungen müssen die stabilen Verträge und Sicherheitsgrenzen von Kernschmied berücksichtigen.
- type: textarea
  id: problem
  attributes:
  label: Problem oder Anwendungsfall
  description: Welches konkrete Problem soll gelöst werden?
  validations:
  required: true
- type: textarea
  id: solution
  attributes:
  label: Gewünschte Lösung
  validations:
  required: true
- type: dropdown
  id: area
  attributes:
  label: Betroffener Bereich
  options: - Backend - Frontend - Bootstrap - Hierarchie - UI-Schema oder SchemaRenderer - Modelle - Tools - Chat oder SSE - Konfiguration - Sicherheit - Dokumentation - Mehrere Bereiche
  validations:
  required: true
- type: textarea
  id: contracts
  attributes:
  label: Auswirkungen auf Verträge
  description: Werden API-, Schema-, Manifest- oder SSE-Verträge verändert?
- type: textarea
  id: security
  attributes:
  label: Sicherheits- und Autorisierungsaspekte
  description: Welche serverseitigen Prüfungen oder Sicherheitsgrenzen sind betroffen?
- type: textarea
  id: alternatives
  attributes:
  label: Alternativen
  description: Welche anderen Lösungen wurden betrachtet?
- type: checkboxes
  id: checks
  attributes:
  label: Bestätigung
  options: - label: Ich habe nach ähnlichen Vorschlägen gesucht.
  required: true - label: Die vorgeschlagene Funktion setzt keine automatische Freigabe dynamisch erkannter Typen voraus.
  required: true
