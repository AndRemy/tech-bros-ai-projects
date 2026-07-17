# Convenciones para Claude Code en este repo

## Un commit por Pull Request

Cada PR debe quedar como **un solo commit** en el historial de `main`.

- Si vas a agregar cambios a una rama que ya tiene una PR abierta (por ejemplo,
  corrigiendo algo que se pidió en la misma tarea, o un fix encontrado
  probando el mismo trabajo), no crees un commit nuevo: usa
  `git commit --amend` para combinarlo con el commit existente de esa rama, y
  sube el resultado con `git push --force-with-lease`.
- Esta autorización para forzar el push aplica **únicamente** a este flujo
  (mantener una PR existente en un solo commit). No autoriza force-push en
  ningún otro contexto (por ejemplo, reescribir una rama ya mergeada, o el
  historial de `main`).
- Si la PR ya fue mergeada antes de subir cambios adicionales, ese flujo ya no
  aplica: abre una PR nueva con un commit nuevo (no hay nada que amendar).
- Al amendar, actualiza el mensaje del commit para que siga reflejando el
  conjunto completo de cambios de la PR, no solo el último fix.
