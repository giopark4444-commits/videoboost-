# videoboost

> ⚠️ **Starter scaffold.** El repo estaba vacío; esto es una base que ya compila
> y tiene pruebas, sobre la que se construye la app real.

## Qué hace (por ahora)

Utilidades puras para trabajar con video:

- `formatTimecode(segundos)` → `"HH:MM:SS"`.
- `targetVideoBitrateKbps(duración, tamañoMB, audioKbps?)` → bitrate de video
  estimado para que un clip quepa en un tamaño objetivo.

**Propósito previsto** (según el nombre): herramienta para mejorar / procesar /
comprimir video. Las funciones de arriba son el primer ladrillo.

## Para quién es

Punto de partida para una librería/app de procesamiento de video en TypeScript.

## Instalación

```bash
git clone https://github.com/giopark4444-commits/videoboost-.git
cd videoboost-
npm install
```

## Ejemplo de uso

```ts
import { formatTimecode, targetVideoBitrateKbps } from "./src/index";

formatTimecode(3661);            // "01:01:01"
targetVideoBitrateKbps(60, 25);  // kbps para 60s en 25 MB
```

## Pruebas

```bash
npm test          # vitest run
npm run test:watch
```

## Stack

TypeScript · Vitest.
