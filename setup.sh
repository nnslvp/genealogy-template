#!/bin/bash
# Создаёт новый генеалогический проект из шаблона.
# Использование: ~/work/genealogy-template/setup.sh <slug> "<Имя>" "<Имени (родительный падеж)>"
# Пример:        ~/work/genealogy-template/setup.sh anna "Анна" "Анны"
set -e
SLUG="$1"; NAME="$2"; NAME_GEN="$3"
if [ -z "$SLUG" ] || [ -z "$NAME" ] || [ -z "$NAME_GEN" ]; then
  echo "Использование: $0 <slug латиницей> \"<Имя>\" \"<Имени>\"" >&2; exit 1
fi
case "$SLUG" in *[!a-z0-9-]*) echo "slug — только латиница, цифры и дефис" >&2; exit 1;; esac
SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$HOME/work/genealogy-$SLUG"
if [ -e "$DST" ]; then echo "Папка $DST уже существует, ничего не трогаю." >&2; exit 1; fi

mkdir -p "$DST"
# Копируем всё, кроме истории git самого шаблона и этого скрипта.
rsync -a --exclude '.git' --exclude 'setup.sh' --exclude '.DS_Store' "$SRC/" "$DST/"

# Подставляем имя. Плейсхолдеры: {{NAME}}, {{NAME_GEN}}, {{SLUG}}, {{DATE}}.
TODAY="$(date '+%d.%m.%Y')"
export NAME NAME_GEN SLUG TODAY
find "$DST" -type f \( -name '*.md' -o -name '*.json' -o -name '*.py' -o -name '*.html' \) -print0 \
  | xargs -0 perl -pi -e 's/\{\{NAME\}\}/$ENV{NAME}/g; s/\{\{NAME_GEN\}\}/$ENV{NAME_GEN}/g; s/\{\{SLUG\}\}/$ENV{SLUG}/g; s/\{\{DATE\}\}/$ENV{TODAY}/g'

# README шаблона заменяем на README проекта.
cat > "$DST/README.md" <<EOF
# Генеалогический поиск → roadmap ПМЖ/гражданство: $NAME

Начато: $TODAY. Правила проекта — в \`CLAUDE.md\`, как всё сохраняется — в \`VERSIONING.md\`.

## Структура
- \`docs/inbox/\` — сюда кладите сканы и фото документов (jpg, png, pdf, heic). Claude их читает напрямую и раскладывает по людям.
- \`questionnaire.md\` — вопросы к вам и родне; заполнять прямо в файле после «Ответ:».
- \`persons.md\`, \`persons/\` — карточки предков; \`TRACKER.md\` — статус по восьми прадедам.
- \`findings/\` — результаты поиска по базам; \`letters/\` — черновики запросов (не отправляются без вашего «да»).
- \`roadmap.md\` — юридический roadmap по странам; \`TODO.md\` — что дальше.
- \`handbook/\` — справочник по источникам и методике.

## Правила ведения
- Каждая находка: источник (URL/архив/фонд), дата запроса, что именно найдено, степень уверенности.
- Ничего платного не покупаем без явного согласия.
EOF

cd "$DST"
chmod +x save.sh
git init -q
git add -A
git commit -q -m "Каркас проекта из genealogy-template, $TODAY"
echo "Создано: $DST"
echo
echo "Дальше руками:"
echo "  1) приватный репозиторий на GitHub и первая отправка:"
echo "     gh repo create genealogy-$SLUG --private --source \"$DST\" --remote origin --push"
echo "  2) проверить, что хук автосохранения в ~/.claude/settings.json ловит папку:"
echo "     grep -c 'work/genealogy\\*' ~/.claude/settings.json   # должно быть 1"
echo "     Если 0 — см. VERSIONING.md, раздел «Хук автосохранения»."
echo "  3) открыть claude в $DST и заполнить блок «О себе» в questionnaire.md."
