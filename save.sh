#!/bin/bash
# Фиксирует все изменения в репозитории генеалогии и отправляет их на GitHub.
# Использование: ./save.sh "короткое описание"
# Вызывается вручную и автоматически (хук PostToolUse в ~/.claude/settings.json).
cd "$(dirname "$0")" || exit 1

# Если git занят другим процессом — подождать до 10 секунд.
for i in $(seq 1 20); do
  [ -f .git/index.lock ] || break
  sleep 0.5
done

if [ -n "$(git status --porcelain)" ]; then
  MSG="${1:-Автосохранение $(date '+%Y-%m-%d %H:%M')}"
  git add -A || exit 1
  if git commit -q -m "$MSG"; then
    echo "Сохранено: $(git log --oneline -1)"
  else
    echo "ОШИБКА: не удалось сохранить изменения в git." >&2
    exit 1
  fi
else
  echo "Изменений нет."
fi

# Отправить на GitHub. Если сети нет — предупредить, но не считать это провалом:
# коммит уже сделан локально, отправится при следующем запуске.
if git remote get-url origin >/dev/null 2>&1; then
  if [ -n "$(git log --branches --not --remotes --oneline)" ]; then
    if git push -q origin HEAD 2>/dev/null; then
      echo "Отправлено на GitHub."
    else
      echo "ВНИМАНИЕ: коммит сделан, но отправить на GitHub не вышло (нет сети?). Отправится в следующий раз." >&2
    fi
  fi
fi
