# Einstellungen

Die Systemeinstellungen werden über das Zahnrad in der Kopfzeile geöffnet.

## Fachkonfiguration

Fachliche Einstellungen werden validiert, versioniert und mit einer globalen Revision gespeichert. Änderungen können abhängig von der Definition nur für bestimmte Geltungsbereiche zulässig sein.

## Neustartpflichtige Werte

Technische Infrastrukturwerte können einen Neustart erfordern oder vollständig schreibgeschützt sein. Solche Werte dürfen nicht wie normale Laufzeitkonfiguration behandelt werden.

## Secrets

Geheimnisse werden niemals im Klartext über die normale Konfigurations-API ausgegeben. Ein maskierter Anzeigewert darf nicht als neuer Secret-Wert gespeichert werden.
