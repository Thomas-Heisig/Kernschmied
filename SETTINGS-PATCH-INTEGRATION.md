# Integration des Settings-Patches

## 1. Dateien kopieren

Den Inhalt des ZIP-Archivs in das Stammverzeichnis `F:\Kernschmied` kopieren. Neue Dateien werden ergänzt.

## 2. Backend-Router registrieren

In der zentralen API-v1-Routerdatei ergänzen:

```python
from app.api.v1.settings_catalog import router as settings_catalog_router

api_router.include_router(settings_catalog_router)
```

Falls die Anwendung Router direkt in `backend/main.py` registriert:

```python
from app.api.v1.settings_catalog import router as settings_catalog_router

app.include_router(settings_catalog_router, prefix="/api/v1")
```

Der resultierende Endpunkt muss sein:

```text
GET /api/v1/settings/catalog
```

## 3. Frontend erreichbar machen

Die neue Komponente lautet:

```tsx
import { SettingsCatalogView } from "./components/settings/SettingsCatalogView";
```

Sie kann zunächst in der bestehenden Settings-Seite eingebunden werden:

```tsx
return <SettingsCatalogView />;
```

Oder in der vorhandenen Action-/View-Registry als bekannte feste Komponente registriert werden:

```ts
"settings-catalog": SettingsCatalogView
```

## 4. Konfigurationswerte vorbereiten

Alle Felder mit `source: "config"` verwenden den vorhandenen Vertrag:

```text
GET /api/v1/config
PUT /api/v1/config/{group}/{key}
```

Die konkreten Defaultwerte müssen in der bestehenden Bootstrap-/Seed-Konfiguration ergänzt werden. Eine vollständige Vorschlagsliste liegt in `settings-defaults.json`.

## 5. Noch nicht vorhandene Ressourcen

Links mit Status `prepared` oder `planned` dürfen im Frontend sichtbar sein, müssen aber als nicht verfügbar gekennzeichnet bleiben. Keine Route darf im Frontend vorgetäuscht werden.
