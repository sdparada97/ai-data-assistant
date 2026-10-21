---
description: Verifica un change de OpenSpec antes de archivarlo
argument-hint: <change-id>
---
Verifica el change $ARGUMENTS:
1. Ejecuta `openspec validate $ARGUMENTS --strict` (con el PATH de Node ≥ 20).
2. Delega en el subagente implementation-verifier la revisión de $ARGUMENTS.
3. Resume los hallazgos y propón correcciones para los bloqueantes, sin aplicarlas hasta que yo apruebe.
4. Si todo cumple, indica que está listo para /opsx:archive. No lo archives.
