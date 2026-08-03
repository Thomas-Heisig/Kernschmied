Die Datei enthält nun eine strukturierte Developer-Protokollierung für die gesamte Frontend-Pipeline. Die Protokolle werden nur ausgegeben, wenn Vite im Entwicklungsmodus läuft.

F:\Kernschmied\frontend\src\components\chat\GenericChatView.tsx

Wesentliche Korrekturen:

strukturierte Protokolle mit Dateiname, Pipeline-Schritt und Kontext
Erkennung eines fehlenden complete-Events
Unterstützung für versionierte SSE-Ereignisse
Unterstützung für ältere und neue Token-Payloads
Prüfung der Content-Type-Antwort
Auswertung von request_id, conversation_id, message_id und sequence
keine doppelte Tippanzeige mehr, sobald Inhalt empfangen wurde
sauberer Umgang mit Abbruch und unvollständigem Stream
expliziter Chatstatus statt nur loading
Request-Schema wird vollständig vorbereitet
unbekannte SSE-Ereignisse werden sichtbar protokolliert
sensible Nachrichteninhalte werden nicht vollständig ins Entwicklerprotokoll geschrieben

Developer-Protokollierung dieser Datei

In der Browserkonsole erscheinen im Development-Modus unter anderem folgende Schritte:

component-mounted
submit-started
http-request-started
http-response-received
sse-stream-opened
sse-event-received
generation-started
sse-metadata-event-received
generation-completed
sse-stream-closed
submit-completed
submit-cleanup-completed

Bei Fehlern oder Abweichungen:

input-validation-failed
unexpected-response-content-type
http-error-response-parsed
http-error-json-parse-failed
sse-unsupported-event
sse-sequence-not-increasing
sse-error-event-received
submit-failed
generation-cancelled

Die Protokolle enthalten bewusst nicht den vollständigen Nachrichtentext, sondern nur technische Metadaten wie Länge, Request-ID, Conversation-ID, Eventtyp und Sequenznummer.

Für die weiteren Pipeline-Dateien sollte dieselbe Struktur verwendet werden:

{
timestamp: string;
source: string;
area: string;
step: string;
requestId?: string;
conversationId?: string;
messageId?: string;
sequence?: number;
}

// F:\Kernschmied\frontend\src\api\client.ts

ie zentrale Datei übernimmt jetzt:

strukturierte Developer-Protokollierung für jeden Transport-Schritt
einheitliche Client-Request-ID
zentrale Fehlernormalisierung
FastAPI-Validierungsfehler aus detail
normale JSON-, Text-, Blob- und Void-Antworten
eigenen apiStreamRequest() für SSE
getrenntes Verbindungs- und Stream-Timeout
saubere Weitergabe externer Abbruchsignale
sichere URL-Auflösung
Prüfung von HTTP-Methode und Request-Body
Freigabe aller Timer und Event-Listener über dispose()

Developer-Protokollierung

Normale API-Anfragen erzeugen diese Schritte:

api-client-initialized
request-started
response-headers-received
response-parsed
request-cleanup-completed

Streaming-Anfragen erzeugen:

stream-request-started
stream-response-headers-received
stream-request-disposed

Fehler werden unter anderem so protokolliert:

error-response-json-parse-failed
error-response-text-read-failed
request-failed
stream-request-failed
Notwendige Anpassung in GenericChatView.tsx

Der bisherige Import:

import { API_BASE_URL } from "../../api/client";

wird ersetzt durch:

import {
ApiError,
apiPostStream,
} from "../../api/client";

Der direkte fetch()-Block wird anschließend durch den zentralen Stream-Aufruf ersetzt:

const streamHandle =
await apiPostStream(
"/chat/stream",
requestPayload,
{
headers: {
Accept:
"text/event-stream",
},
signal:
abortController.signal,
timeoutMs: null,
expectedContentType:
"text/event-stream",
},
);

try {
await processSseStream(
streamHandle.response,
assistantMessageId,
abortController.signal,
);
} finally {
streamHandle.dispose();
}

Bei der Fehlerauswertung kann dadurch direkt auf den strukturierten Fehler zugegriffen werden:

const message =
caughtError instanceof ApiError
? caughtError.message
: caughtError instanceof Error
? caughtError.message
: "Die Nachricht konnte nicht gesendet werden.";

Damit liegt die komplette HTTP-Transportlogik nun zentral im API-Client. GenericChatView bleibt für Eingabe, SSE-Auswertung und Darstellung verantwortlich.
