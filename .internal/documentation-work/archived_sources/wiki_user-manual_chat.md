# Chat verwenden

## Nachricht senden

1. Wähle in der Hierarchie einen Chat aus.
2. Schreibe deine Nachricht in das Eingabefeld.
3. Sende die Nachricht über den Senden-Button.
4. Die Antwort wird während der Erzeugung schrittweise angezeigt.

## Modell auswählen

Ist die Modellauswahl sichtbar, verwende ausschließlich ein registriertes und verfügbares Modell. Die angezeigte Modell-ID ist die logische Kernschmied-ID; der technische Providername kann davon abweichen.

## Streaming

Kernschmied verwendet Server-Sent Events. Ein HTTP-Status `200` bedeutet, dass der Stream geöffnet wurde. Ein späterer Modellfehler kann innerhalb des Streams als strukturiertes Fehlerereignis eintreffen.

## Fehlerhinweise

Bei einem Fehler sollte die Meldung zusammen mit der Request-ID notiert werden. Die Request-ID ermöglicht die Zuordnung zum Backend-Log.
