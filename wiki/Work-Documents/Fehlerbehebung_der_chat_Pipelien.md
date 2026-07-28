Wir prüfen die komplette Chat-Pipeline **vom Absenden der Eingabe bis zur Darstellung der Antwort**. Dabei beheben wir nicht nur einzelne Fehler, sondern ergänzen fehlende Schemas, Verträge und Funktionen sofort so, dass Backend und Frontend weiterhin gemeinsam startbar bleiben.

## Prüfreihenfolge

### 1. Eingabe im Frontend

Zuerst prüfen wir:

* Eingabefeld und lokalen State
* Absenden per Formular oder Button
* Verhinderung leerer Nachrichten
* Sperre bei laufender Anfrage
* Erzeugung des vollständigen `ChatRequest`
* Übergabe von:

  * `message`
  * `conversation_id`
  * `hierarchy_node_id`
  * `model_id`
  * `tool_ids`
  * `metadata`

Zielvertrag:

```ts
export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
  hierarchy_node_id?: string | null;
  model_id?: string | null;
  tool_ids?: string[];
  metadata?: Record<string, unknown>;
}
```

Zusätzlich sollte das Frontend vor dem Versand validieren:

```ts
export function validateChatRequest(
  request: ChatRequest,
): void {
  const message = request.message.trim();

  if (!message) {
    throw new Error(
      "Eine leere Chat-Nachricht kann nicht gesendet werden.",
    );
  }

  if (message.length > 50_000) {
    throw new Error(
      "Die Chat-Nachricht überschreitet die zulässige Länge.",
    );
  }

  if (
    request.tool_ids &&
    !request.tool_ids.every(
      (toolId) =>
        typeof toolId === "string" &&
        toolId.trim().length > 0,
    )
  ) {
    throw new Error(
      "Die Tool-IDs sind ungültig.",
    );
  }
}
```

---

### 2. Zentraler API-Client

Der API-Client muss ausschließlich für Transport, Fehlernormalisierung und SSE-Verbindungsaufbau zuständig sein.

Zu prüfen:

* korrekte Backend-URL
* korrekter API-Pfad
* `Content-Type: application/json`
* `Accept: text/event-stream`
* `AbortSignal`
* Behandlung von Nicht-200-Antworten
* strukturierte Backend-Fehler
* Stream-Reader und UTF-8-Decodierung

Erforderliche Fehlerstruktur:

```ts
export interface ApiErrorResponse {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string | null;
}
```

Normalisierte Client-Fehlerklasse:

```ts
export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly requestId: string | null;

  constructor({
    status,
    code,
    message,
    details,
    requestId,
  }: {
    status: number;
    code: string;
    message: string;
    details?: unknown;
    requestId?: string | null;
  }) {
    super(message);

    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId ?? null;
  }
}
```

---

### 3. FastAPI-Request-Schema

Das Backend-Schema muss dem TypeScript-Vertrag entsprechen.

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    message: str = Field(
        min_length=1,
        max_length=50_000,
    )

    conversation_id: str | None = Field(
        default=None,
        max_length=200,
    )

    hierarchy_node_id: str | None = Field(
        default=None,
        max_length=200,
    )

    model_id: str | None = Field(
        default=None,
        max_length=200,
    )

    tool_ids: list[str] = Field(
        default_factory=list,
        max_length=100,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("message")
    @classmethod
    def validate_message(
        cls,
        value: str,
    ) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "Die Nachricht darf nicht leer sein.",
            )

        return normalized_value

    @field_validator("tool_ids")
    @classmethod
    def validate_tool_ids(
        cls,
        value: list[str],
    ) -> list[str]:
        normalized_tool_ids: list[str] = []
        seen_tool_ids: set[str] = set()

        for tool_id in value:
            normalized_tool_id = tool_id.strip()

            if not normalized_tool_id:
                raise ValueError(
                    "Tool-IDs dürfen nicht leer sein.",
                )

            if normalized_tool_id in seen_tool_ids:
                continue

            seen_tool_ids.add(
                normalized_tool_id,
            )
            normalized_tool_ids.append(
                normalized_tool_id,
            )

        return normalized_tool_ids
```

Wichtig: `extra="forbid"` verhindert, dass unbekannte Request-Felder stillschweigend akzeptiert werden.

---

### 4. Chat-Router

Der Router darf keine Fachlogik enthalten. Er übernimmt:

1. Request-Validierung
2. Benutzer- und Berechtigungskontext
3. Erstellung des Stream-Kontexts
4. Aufruf des `ChatService`
5. Rückgabe als `StreamingResponse`

Zielstruktur:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.chat.dependencies import get_chat_service
from app.chat.schemas import ChatRequest
from app.chat.service import ChatService
from app.chat.stream import encode_sse_stream
from app.contracts.request_context import RequestContext
from app.dependencies.request_context import get_request_context


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post(
    "/stream",
    response_class=StreamingResponse,
)
async def stream_chat(
    payload: ChatRequest,
    request: Request,
    request_context: RequestContext = Depends(
        get_request_context,
    ),
    chat_service: ChatService = Depends(
        get_chat_service,
    ),
) -> StreamingResponse:
    stream = chat_service.stream_chat(
        request=payload,
        request_context=request_context,
        disconnect_checker=request.is_disconnected,
    )

    return StreamingResponse(
        encode_sse_stream(stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_context.request_id,
        },
    )
```

---

### 5. Stream-Kontext

Ein häufiger Fehler ist, dass Informationen im Router vorhanden sind, aber nicht vollständig an den Service oder Provider weitergegeben werden.

Der Kontext sollte ausdrücklich typisiert sein:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StreamContext:
    request_id: str
    user_id: str
    environment: str

    conversation_id: str | None = None
    hierarchy_node_id: str | None = None
    requested_model_id: str | None = None

    requested_tool_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
```

Dabei muss klar getrennt werden zwischen:

* angefordertem Modell
* tatsächlich aufgelöstem Modell
* angeforderten Tools
* tatsächlich autorisierten Tools

---

### 6. Autorisierung vor Fachlogik

Jede Benutzeraktion muss serverseitig geprüft werden.

Zu prüfen:

* Darf der Benutzer den Hierarchieknoten verwenden?
* Darf er den Chat öffnen?
* Darf er das gewünschte Modell verwenden?
* Darf er die angeforderten Tools verwenden?
* Sind Modell und Tools aktiviert?
* Sind sie im aktuellen Betriebsprofil erlaubt?

Zielstruktur:

```python
authorized_tool_ids = await authorization_service.authorize_tools(
    user_id=request_context.user_id,
    hierarchy_node_id=payload.hierarchy_node_id,
    requested_tool_ids=payload.tool_ids,
)

authorized_model_id = await authorization_service.authorize_model(
    user_id=request_context.user_id,
    hierarchy_node_id=payload.hierarchy_node_id,
    requested_model_id=payload.model_id,
)
```

Wichtig:

> Dynamische Erkennung oder Registrierung bedeutet niemals automatische Freigabe.

---

### 7. Konfigurationsauflösung und Prompt-Vererbung

Vor dem Modellaufruf müssen alle fachlichen Einstellungen reproduzierbar aufgelöst werden.

Reihenfolge:

```text
System
→ Benutzer
→ Hierarchieknoten
→ Projekt
→ Chat
→ Request
```

Das Ergebnis sollte ein unveränderlicher Laufzeitvertrag sein:

```python
@dataclass(frozen=True, slots=True)
class ResolvedChatConfiguration:
    revision: int
    model_id: str
    system_prompt: str
    temperature: float
    max_tokens: int
    tool_ids: tuple[str, ...]
    metadata: dict[str, object]
```

Zu prüfen:

* Config-Revision wird mitgeführt
* ungültige Konfiguration führt zu strukturiertem Fehler
* Secrets werden nicht aus Fachkonfiguration gelesen
* unbekannte Prompt-Ebenen werden abgelehnt
* keine globale Cache-Magie
* Cache berücksichtigt die Config-Revision

---

### 8. Modellauflösung über Registry

Der Service darf keinen Provider direkt importieren oder fest verdrahten.

Ziel:

```python
model_backend = model_registry.require_backend(
    resolved_configuration.model_id,
)
```

Fehlerfälle:

* Modell nicht gefunden
* Modell deaktiviert
* Manifest ungültig
* Provider konnte nicht initialisiert werden
* Provider unterstützt Chat nicht
* Provider unterstützt Streaming nicht
* Modell ist im Betriebsprofil nicht erlaubt

Beispiel:

```python
class ModelNotAvailableError(RuntimeError):
    def __init__(
        self,
        model_id: str,
    ) -> None:
        super().__init__(
            f'Das Modell "{model_id}" ist nicht verfügbar.',
        )
        self.model_id = model_id
```

---

### 9. GenerationRequest

Der interne Modellvertrag sollte nicht mit dem externen API-Request identisch sein.

```python
generation_request = GenerationRequest(
    messages=messages,
    model_id=resolved_configuration.model_id,
    system_prompt=resolved_configuration.system_prompt,
    temperature=resolved_configuration.temperature,
    max_tokens=resolved_configuration.max_tokens,
    tools=resolved_tools,
    metadata={
        **payload.metadata,
        "request_id": request_context.request_id,
        "config_revision": resolved_configuration.revision,
        "conversation_id": conversation.id,
        "hierarchy_node_id": payload.hierarchy_node_id,
    },
)
```

Dadurch bleiben API-Vertrag, Fachlogik und Provider-Vertrag sauber getrennt.

---

### 10. SSE-Ereignisschema

Alle Stream-Ereignisse müssen eindeutig typisiert sein.

Empfohlene Ereignisse:

```text
start
token
message
reasoning
tool_call
tool_result
usage
complete
error
heartbeat
```

Python-Vertrag:

```python
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StreamEventType(StrEnum):
    START = "start"
    TOKEN = "token"
    MESSAGE = "message"
    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    USAGE = "usage"
    COMPLETE = "complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class ChatStreamEvent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: str = "1.0"
    event: StreamEventType
    sequence: int = Field(
        ge=0,
    )
    request_id: str
    conversation_id: str | None = None
    message_id: str | None = None
    data: dict[str, Any] = Field(
        default_factory=dict,
    )
```

Jedes Ereignis sollte besitzen:

* `schema_version`
* `event`
* `sequence`
* `request_id`
* `conversation_id`
* optional `message_id`
* typisierte Nutzdaten

---

### 11. SSE-Codierung

Die SSE-Codierung muss zentral erfolgen.

```python
from __future__ import annotations

import json
from collections.abc import AsyncIterator

from app.chat.schemas import ChatStreamEvent


def encode_sse_event(
    event: ChatStreamEvent,
) -> str:
    payload = event.model_dump(
        mode="json",
        exclude_none=True,
    )

    return (
        f"event: {event.event.value}\n"
        f"id: {event.sequence}\n"
        f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    )


async def encode_sse_stream(
    events: AsyncIterator[ChatStreamEvent],
) -> AsyncIterator[str]:
    async for event in events:
        yield encode_sse_event(event)
```

Häufige Fehler:

* fehlende Leerzeile nach einem Ereignis
* JSON über mehrere unzulässig verarbeitete Zeilen
* Vermischung von Eventname und Payload
* nicht serialisierbare Objekte
* `None` an unerwarteten Stellen
* fehlende Sequenznummer
* Stream endet ohne `complete` oder `error`

---

### 12. Fehlerbehandlung im Stream

Nach Beginn einer Streaming-Antwort kann FastAPI keinen normalen JSON-Fehler mehr senden. Fehler müssen dann selbst als SSE-Ereignis übertragen werden.

```python
except Exception as exc:
    logger.exception(
        "Fehler während des Chat-Streams.",
        extra={
            "request_id": request_context.request_id,
        },
    )

    yield ChatStreamEvent(
        event=StreamEventType.ERROR,
        sequence=sequence,
        request_id=request_context.request_id,
        conversation_id=conversation_id,
        data={
            "code": "chat_stream_failed",
            "message": (
                "Die Chat-Antwort konnte nicht vollständig "
                "erstellt werden."
            ),
            "details": {},
        },
    )
```

Interne Fehlermeldungen, Stacktraces, Tokens oder Provider-Secrets dürfen nicht an das Frontend gelangen.

---

### 13. SSE-Parser im Frontend

Der Parser muss fragmentierte Netzwerkblöcke korrekt zusammensetzen. Ein `reader.read()` entspricht nicht zwingend einem vollständigen SSE-Ereignis.

Zielalgorithmus:

```ts
let buffer = "";

while (true) {
  const result = await reader.read();

  if (result.done) {
    break;
  }

  buffer += decoder.decode(
    result.value,
    {
      stream: true,
    },
  );

  const blocks = buffer.split(/\r?\n\r?\n/);
  buffer = blocks.pop() ?? "";

  for (const block of blocks) {
    const event = parseSseBlock(block);

    if (event) {
      onEvent(event);
    }
  }
}
```

Das ist einer der wichtigsten Prüfpunkte. Ein Parser, der jeden Netzwerkblock unmittelbar als JSON behandelt, wird früher oder später fehlschlagen.

---

### 14. Frontend-Event-Validierung

Auch Serverereignisse müssen im Frontend geprüft werden.

```ts
export type ChatStreamEventType =
  | "start"
  | "token"
  | "message"
  | "reasoning"
  | "tool_call"
  | "tool_result"
  | "usage"
  | "complete"
  | "error"
  | "heartbeat";

export interface ChatStreamEvent {
  schema_version: string;
  event: ChatStreamEventType;
  sequence: number;
  request_id: string;
  conversation_id?: string;
  message_id?: string;
  data: Record<string, unknown>;
}
```

Unbekannte Ereignisse dürfen nicht stillschweigend als bekannte Ereignisse interpretiert werden.

```ts
export function isKnownChatEventType(
  value: string,
): value is ChatStreamEventType {
  return [
    "start",
    "token",
    "message",
    "reasoning",
    "tool_call",
    "tool_result",
    "usage",
    "complete",
    "error",
    "heartbeat",
  ].includes(value);
}
```

Unbekannte Typen sollten protokolliert und sichtbar als nicht unterstützt behandelt werden.

---

### 15. Aktualisierung des Chat-States

Der Frontend-State muss zwischen Nachrichten-ID, Request-ID und Conversation-ID unterscheiden.

Empfohlene Statuswerte:

```ts
export type ChatRequestStatus =
  | "idle"
  | "connecting"
  | "streaming"
  | "completed"
  | "failed"
  | "cancelled";
```

Eine Assistentennachricht sollte bereits beim `start`-Event angelegt werden. `token`-Events ergänzen ausschließlich diese Nachricht.

Nicht bei jedem Token eine neue Nachricht erzeugen.

---

### 16. Abschluss des Streams

Ein Stream ist erst erfolgreich abgeschlossen, wenn ein `complete`-Ereignis empfangen wurde.

Nur ein geschlossenes Netzwerk-Streaming reicht nicht als Erfolgskriterium.

Das Frontend sollte unterscheiden:

* `complete` empfangen: erfolgreich
* `error` empfangen: fachlicher oder technischer Fehler
* Verbindung ohne Abschluss geschlossen: unvollständiger Stream
* Benutzerabbruch: `cancelled`

---

### 17. Persistierung

Zu prüfen:

* Benutzernachricht wird nur einmal gespeichert
* Assistentennachricht wird eindeutig zugeordnet
* Teilantworten werden kontrolliert gespeichert
* abgebrochene Antworten erhalten Status
* Tool-Aufrufe werden nachvollziehbar gespeichert
* Conversation-ID wird beim ersten Chat erzeugt und zurückgegeben
* Transaktion bleibt nicht während des gesamten Modellstreams offen

Empfohlener Ablauf:

```text
1. Conversation auflösen oder erzeugen
2. Benutzernachricht speichern
3. Transaktion abschließen
4. Modellstream ausführen
5. Antwort puffern oder kontrolliert aktualisieren
6. Assistentennachricht finalisieren
7. Usage und Status speichern
```

Eine Datenbanktransaktion sollte nicht minutenlang über den vollständigen Modellstream geöffnet bleiben.

---

## Konkrete Arbeitsabfolge für die Fehlerbehebung

Wir bearbeiten die Dateien in dieser Reihenfolge:

1. `frontend/src/.../GenericChatView.tsx`
2. zentraler Frontend-API-Client, beispielsweise `frontend/src/api/client.ts`
3. Chat-Verträge und TypeScript-Typen
4. `backend/app/api/.../chat.py`
5. Backend-Chat-Request-Schema
6. `ChatService`
7. `StreamContext`
8. Config- und Prompt-Auflösung
9. `ModelRegistry`
10. `ToolRegistry`
11. Modellbackend, zuerst Ollama
12. SSE-Encoder
13. globales und streaminternes Error-Handling
14. Persistierung
15. Frontend-SSE-Parser
16. Frontend-State und Darstellung
17. Backend-Tests
18. Frontend-Tests
19. API- und Schema-Dokumentation

## Erster Prüfblock

Als ersten Block benötigen wir gemeinsam:

```text
GenericChatView.tsx
zentraler API-Client
ChatRequest-/SSE-TypeScript-Typen
Backend-Router chat.py
Backend-Chat-Schemas
ChatService
```

Ich werde bei jeder Datei dann jeweils direkt liefern:

```text
1. festgestellter Fehler
2. Auswirkung auf die Pipeline
3. notwendige Vertrags- oder Schemaänderung
4. vollständige korrigierte Datei
5. benötigte Folgedateien
6. passende Tests
```

Beginnen sollten wir mit `GenericChatView.tsx`, weil dort die Pipeline sichtbar startet und sich bereits feststellen lässt, ob Request, Stream-Abbruch, SSE-Verarbeitung und State-Verwaltung korrekt zusammenspielen.
