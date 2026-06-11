# ACCEPTED — проверка сборщика engine/build_cover.py

Принято архитектором 2026-06-10.

Все 5 шагов верификации прошли (отчёт кодера):
- py_compile 4 движков — без ошибок.
- Дефолтный запуск — управляемая ошибка `FAILED: File not found` (snarky-cover отсутствует
  на этой машине, это вход с другого ПК; не баг).
- AUTO (`build_cover_chain`) на фикстуре front_art_test.png → разворот 4649×2850 px,
  PDF MediaBox 15.4967×9.5 in (1115.76×684 pt), фронт-арт вписан в переднюю половину.
- SIMPLE happy (валидный размер) → PASS, delta 0 px, cover.pdf создан.
- SIMPLE reject (неверный размер) → ValueError с понятным сообщением, папка не создана.

Архитектор проверял по host-коду (cover_generator/cover_to_pdf/build_cover) + отчёту;
локальный прогон в песочнице невозможен из-за усечения mount-копии cover_generator.py
(глюк синхронизации песочницы, не баг кода).

ОТКРЫТЫЕ ХВОСТЫ (не блокеры):
1. `cover_proof.png` при draw_guides=True: host-код сохраняет его как `cover_proof.png`
   (out_path с суффиксом _proof). Кодер не нашёл файл — перепроверить точное имя/путь;
   если реально отсутствует — мелкий фикс в cover_generator. Низкий приоритет.
2. Стале-пути в доках перенесённых DOE-проектов (см. отчёт о переносе) — починить позже.
3. git stash от sync ("local edits before sync") — устарел (DEV-NOTES возвращён в
   AGENTS.md вручную), рекомендуется `git stash drop stash@{0}`.
