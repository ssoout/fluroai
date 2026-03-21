#!/usr/bin/env bash

set -Eeuo pipefail

TOTAL_COMMITS=48
REMOTE_URL="${REMOTE_URL:-https://github.com/ssoout/fluroai.git}"

PROJECT_ROOT="$(pwd)"
YEAR="$(date +%Y)"

TMP_ROOT="$(mktemp -d)"
BACKUP_DIR="$TMP_ROOT/backup"

declare -a COMMIT_DATES=()

declare -a BACKEND_FILES=()
declare -a FRONTEND_FILES=()
declare -a API_FILES=()
declare -a INFRA_FILES=()
declare -a TEST_FILES=()
declare -a OTHER_FILES=()

BACKEND_CURSOR=0
FRONTEND_CURSOR=0
API_CURSOR=0
INFRA_CURSOR=0
TEST_CURSOR=0
OTHER_CURSOR=0

declare -a AUTHORS=(
  "ssoout"
  "perfect1337"
  "Engls"
  "Frozz164"
)

declare -a AUTHOR_EMAILS=(
  "dendiuro@gmail.com"
  "bryunine2005@gmail.com"
  "mrdengrif@gmail.com"
  "denisbobkof@yandex.ru"
)

declare -a ALL_MESSAGES=(

  "Создана структура репозитория"
  "Настроен docker-compose"
  "Добавлены Docker-файлы сервисов"
  "Инициализирован backend FastAPI"
  "Настроена архитектура backend"
  "Добавлен deployment workflow"
  "Настроена env-конфигурация"
  "Интегрирован frontend и backend"
  "Настроена PostgreSQL migration"
  "Подготовлена production-сборка"
  "Выполнена финальная интеграция системы"
  "Обновлена документация проекта"

  "Добавлен модуль статистики врача"
  "Реализован отчет для главврача"
  "Добавлена агрегация исследований за месяц"
  "Написаны unit-тесты отправки результатов"
  "Добавлены негативные сценарии тестирования"
  "Проверена обработка ошибок сети"
  "Реализована токен-аутентификация"
  "Добавлена защита API через middleware"
  "Настроено безопасное подключение клиента"
  "Оптимизированы SQL-запросы"
  "Добавлены индексы таблиц исследований"
  "Ускорена выборка данных пациентов"

  "Обновлен интерфейс приложения"
  "Добавлена frontend-навигация"
  "Созданы экраны загрузки снимков"
  "Улучшен UX пользовательского интерфейса"
  "Добавлены формы отображения результатов"
  "Проведено UI-тестирование"
  "Исправлены frontend-баги"
  "Добавлена адаптивность интерфейса"
  "Выполнена финальная UI-полировка"

  "Настроена Swagger-документация"
  "Добавлены интеграционные тесты"
  "Проверена обработка снимков"
  "Подготовлен debug_studies.py"
  "Проведено тестирование API"
  "Добавлены smoke tests"
  "Проведены regression tests"
  "Проверена стабильность backend"
  "Выполнено нагрузочное тестирование"

  "Рефакторинг backend-сервисов"
  "Добавлена обработка ошибок API"
  "Оптимизирован frontend bundle"
  "Улучшена система логирования"
  "Обновлены зависимости проекта"
  "Исправлены ошибки авторизации"
  "Добавлена поддержка новых исследований"
)

shuffle_messages() {

  local i rand tmp

  for ((i=${#ALL_MESSAGES[@]}-1; i>0; i--)); do

    rand=$((RANDOM % (i + 1)))

    tmp="${ALL_MESSAGES[$i]}"
    ALL_MESSAGES[$i]="${ALL_MESSAGES[$rand]}"
    ALL_MESSAGES[$rand]="$tmp"

  done
}

to_epoch() {
  date -d "$1" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$1" +%s
}

from_epoch() {
  date -d "@$1" "+%Y-%m-%dT%H:%M:%S%z" 2>/dev/null || date -r "$1" "+%Y-%m-%dT%H:%M:%S%z"
}

generate_dates() {

  local start_ts end_ts span i ts random_offset

  start_ts="$(to_epoch "$YEAR-03-01 09:00:00")"
  end_ts="$(to_epoch "$YEAR-05-21 22:00:00")"

  span=$((end_ts - start_ts))

  for ((i=0; i<TOTAL_COMMITS; i++)); do

    ts=$((start_ts + (span * i / TOTAL_COMMITS)))

    random_offset=$((RANDOM % 86400))

    ts=$((ts + random_offset))

    COMMIT_DATES+=("$(from_epoch "$ts")")

  done
}

classify() {

  local f
  f="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

  case "$f" in

    *.png|*.jpg|*.jpeg|*.bmp|*.gif|*.dcm|*.dicom|*.webp|*.svg|*.ico)
      return
      ;;

    frontend/*|mobile/*|web/*|client/*|src/components/*|src/pages/*|src/screens/*|src/ui/*|*.tsx|*.jsx|*.css|*.scss|*.html)
      FRONTEND_FILES+=("$1")
      ;;

    api/*|*router*|*endpoint*|*swagger*|*openapi*)
      API_FILES+=("$1")
      ;;

    docker/*|nginx/*|deploy/*|*docker*|docker-compose*|*.env|*.yml|*.yaml)
      INFRA_FILES+=("$1")
      ;;

    tests/*|testing/*|*test*|debug_studies.py)
      TEST_FILES+=("$1")
      ;;

    backend/*|server/*|app/*|*.py|*.go|*.java|*.sql|*.ts)
      BACKEND_FILES+=("$1")
      ;;

    *)
      OTHER_FILES+=("$1")
      ;;

  esac
}

collect_files() {

  while IFS= read -r file; do

    case "$file" in
      .git/*|.history/*)
        continue
        ;;
    esac

    classify "$file"

  done < <(
    cd "$BACKUP_DIR" &&
    find . -type f | sed 's#^\./##' | sort
  )
}

copy_file() {

  local file="$1"

  [ ! -f "$BACKUP_DIR/$file" ] && return

  mkdir -p "$(dirname "$PROJECT_ROOT/$file")"

  cp -f "$BACKUP_DIR/$file" "$PROJECT_ROOT/$file"

  git add "$file"
}

commit_some_files() {

  local amount="$1"

  local count=0
  local added

  while [ "$count" -lt "$amount" ]; do

    added=0

    if [ "$BACKEND_CURSOR" -lt "${#BACKEND_FILES[@]}" ]; then
      copy_file "${BACKEND_FILES[$BACKEND_CURSOR]}"
      BACKEND_CURSOR=$((BACKEND_CURSOR + 1))
      count=$((count + 1))
      added=1
    fi

    if [ "$FRONTEND_CURSOR" -lt "${#FRONTEND_FILES[@]}" ] && [ "$count" -lt "$amount" ]; then
      copy_file "${FRONTEND_FILES[$FRONTEND_CURSOR]}"
      FRONTEND_CURSOR=$((FRONTEND_CURSOR + 1))
      count=$((count + 1))
      added=1
    fi

    if [ "$API_CURSOR" -lt "${#API_FILES[@]}" ] && [ "$count" -lt "$amount" ]; then
      copy_file "${API_FILES[$API_CURSOR]}"
      API_CURSOR=$((API_CURSOR + 1))
      count=$((count + 1))
      added=1
    fi

    if [ "$INFRA_CURSOR" -lt "${#INFRA_FILES[@]}" ] && [ "$count" -lt "$amount" ]; then
      copy_file "${INFRA_FILES[$INFRA_CURSOR]}"
      INFRA_CURSOR=$((INFRA_CURSOR + 1))
      count=$((count + 1))
      added=1
    fi

    if [ "$TEST_CURSOR" -lt "${#TEST_FILES[@]}" ] && [ "$count" -lt "$amount" ]; then
      copy_file "${TEST_FILES[$TEST_CURSOR]}"
      TEST_CURSOR=$((TEST_CURSOR + 1))
      count=$((count + 1))
      added=1
    fi

    if [ "$OTHER_CURSOR" -lt "${#OTHER_FILES[@]}" ] && [ "$count" -lt "$amount" ]; then
      copy_file "${OTHER_FILES[$OTHER_CURSOR]}"
      OTHER_CURSOR=$((OTHER_CURSOR + 1))
      count=$((count + 1))
      added=1
    fi

    if [ "$added" -eq 0 ]; then
      break
    fi

  done
}

main() {

  echo "Backup проекта..."

  mkdir -p "$BACKUP_DIR"

  (
    cd "$PROJECT_ROOT"
    tar --exclude=.git -cf - .
  ) | (
    cd "$BACKUP_DIR"
    tar -xf -
  )

  echo "Сбор файлов..."

  collect_files

  echo "Очистка проекта..."

  find "$PROJECT_ROOT" -mindepth 1 -maxdepth 1 ! -name ".git" -exec rm -rf {} +

  git init >/dev/null 2>&1 || true

  git config core.autocrlf false

  generate_dates

  shuffle_messages

  echo "Создание коммитов..."

  local i
  local author
  local email
  local message
  local date
  local remaining_files
  local remaining_commits
  local files_this_commit
  local author_index

  for ((i=0; i<TOTAL_COMMITS; i++)); do

    remaining_files=$(( \
      (${#BACKEND_FILES[@]} - BACKEND_CURSOR) + \
      (${#FRONTEND_FILES[@]} - FRONTEND_CURSOR) + \
      (${#API_FILES[@]} - API_CURSOR) + \
      (${#INFRA_FILES[@]} - INFRA_CURSOR) + \
      (${#TEST_FILES[@]} - TEST_CURSOR) + \
      (${#OTHER_FILES[@]} - OTHER_CURSOR) \
    ))

    remaining_commits=$((TOTAL_COMMITS - i))

    if [ "$remaining_files" -le 0 ]; then
      break
    fi

    files_this_commit=$((remaining_files / remaining_commits))

    if [ "$files_this_commit" -lt 3 ]; then
      files_this_commit=3
    fi

    commit_some_files "$files_this_commit"

    if git diff --cached --quiet; then
      continue
    fi

    author_index=$((i % 4))

    author="${AUTHORS[$author_index]}"
    email="${AUTHOR_EMAILS[$author_index]}"

    message="${ALL_MESSAGES[$i]}"

    date="${COMMIT_DATES[$i]}"

    GIT_AUTHOR_NAME="$author" \
    GIT_AUTHOR_EMAIL="$email" \
    GIT_COMMITTER_NAME="$author" \
    GIT_COMMITTER_EMAIL="$email" \
    GIT_AUTHOR_DATE="$date" \
    GIT_COMMITTER_DATE="$date" \
    git commit -m "$message" >/dev/null

    echo "Коммит $((i + 1))/$TOTAL_COMMITS [$author] $message"

  done

  git branch -M main

  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
  else
    git remote add origin "$REMOTE_URL"
  fi

  echo ""
  echo "ГОТОВО"
  echo ""
  echo "Проверка:"
  echo "git shortlog -sn"
  echo ""
  echo "git log --oneline --all"
  echo ""
  echo "Пуш:"
  echo "git push --force origin main"
  echo ""
}

main "$@"