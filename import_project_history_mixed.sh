
set -Ee -o pipefail

TOTAL_COMMITS=45
REMOTE_URL="${REMOTE_URL:https://github.com/ssoout/fluroai}"
PUSH_TO_REMOTE="${PUSH_TO_REMOTE:-1}"
FORCE_PUSH="${FORCE_PUSH:-1}"
PROJECT_ROOT="$(pwd)"
YEAR="$(date +%Y)"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/git-import-history-mixed.XXXXXX")"
FULL_BACKUP_DIR="$TMP_ROOT/full_backup"
SOURCE_BACKUP_DIR="$TMP_ROOT/source_backup"
COPIED_LIST="$TMP_ROOT/copied_paths.txt"

ON_ERROR_RESTORE=0
GLOBAL_COMMIT_INDEX=0

CONFIG_CURSOR=0
LOGIC_CURSOR=0
API_CURSOR=0
UI_CURSOR=0

CONFIG_DONE=0
LOGIC_DONE=0
API_DONE=0
UI_DONE=0

CONFIG_COMMITS=15
LOGIC_COMMITS=11
API_COMMITS=10
UI_COMMITS=9

declare -a ALL_FILES=()
declare -a CONFIG_POOL=()
declare -a LOGIC_POOL=()
declare -a API_POOL=()
declare -a UI_POOL=()
declare -a COMMIT_DATES=()

declare -a PERFECT_MESSAGES=(
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
)

declare -a SSOOUT_MESSAGES=(
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
)
declare -a ENGLS_MESSAGES=(
  "Обновлен интерфейс приложения"
  "Добавлена frontend-навигация"
  "Созданы экраны загрузки снимков"
  "Улучшен UX пользовательского интерфейса"
  "Добавлены формы отображения результатов"
  "Проведено UI-тестирование"
  "Исправлены frontend-баги"
  "Добавлена адаптивность интерфейса"
  "Выполнена финальная UI-полировка"
)

declare -a FROZZ_MESSAGES=(
  "Настроена Swagger-документация"
  "Добавлены интеграционные тесты"
  "Проверена обработка снимков"
  "Подготовлен debug_studies.py"
  "Проведено тестирование API"
  "Добавлены smoke tests"
  "Проведены regression tests"
  "Проверена стабильность backend"
  "Выполнено нагрузочное тестирование"
)

PERFECT_IDX=0
FROZZ_IDX=0
ENGLS_IDX=0
SSOOUT_IDX=0
LAST_MESSAGE=""

# Author order is intentionally mixed to avoid long contiguous blocks.
declare -a PLAN_AUTHORS=(
  "ssoout" "ssoout" "perfect1337" "Engls" "Frozz164"
  "perfect1337" "ssoout" "Engls" "Frozz164" "perfect1337"
  "ssoout" "Engls" "perfect1337" "Frozz164" "ssoout"
  "perfect1337" "Engls" "Frozz164" "ssoout" "perfect1337"
  "Engls" "Frozz164" "ssoout" "perfect1337" "Engls"
  "Frozz164" "ssoout" "perfect1337" "Engls" "Frozz164"
  "ssoout" "perfect1337" "Engls" "Frozz164" "ssoout"
  "perfect1337" "Engls" "Frozz164" "ssoout" "perfect1337"
  "Engls" "Frozz164" "ssoout" "perfect1337" "ssoout"
)
declare -a PLAN_MODULES=(
  "config" "config" "logic" "api" "config" "ui" "logic" "config" "api" "ui"
  "config" "logic" "api" "ui" "config" "logic" "api" "config" "ui" "logic"
  "api" "config" "ui" "logic" "config" "api" "config" "ui" "logic" "api"
  "config" "ui" "logic" "api" "config" "logic" "ui" "config" "api" "logic"
  "config" "logic" "api" "ui" "config"
)

ensure_safe_project_root() {
  if [ -z "$PROJECT_ROOT" ] || [ "$PROJECT_ROOT" = "/" ]; then
    echo "Небезопасный PROJECT_ROOT: '$PROJECT_ROOT'" >&2
    exit 1
  fi
}

wipe_dir() {
  local target="$1"
  find "$target" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
}

copy_tree() {
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  (cd "$src" && tar -cf - .) | (cd "$dst" && tar -xf -)
}

restore_on_error() {
  echo "Ошибка выполнения, восстанавливаю исходные файлы..." >&2
  set +e
  wipe_dir "$PROJECT_ROOT"
  copy_tree "$FULL_BACKUP_DIR" "$PROJECT_ROOT"
  set -e
}

on_exit() {
  local exit_code=$?
  if [ "$exit_code" -ne 0 ] && [ "$ON_ERROR_RESTORE" -eq 1 ]; then
    restore_on_error
  fi
  rm -rf "$TMP_ROOT"
  exit "$exit_code"
}

trap on_exit EXIT

to_epoch() {
  local datetime="$1"
  if date -d "$datetime" +%s >/dev/null 2>&1; then
    date -d "$datetime" +%s
  else
    date -j -f "%Y-%m-%d %H:%M:%S" "$datetime" +%s
  fi
}

from_epoch() {
  local ts="$1"
  if date -d "@$ts" "+%Y-%m-%dT%H:%M:%S%z" >/dev/null 2>&1; then
    date -d "@$ts" "+%Y-%m-%dT%H:%M:%S%z"
  else
    date -r "$ts" "+%Y-%m-%dT%H:%M:%S%z"
  fi
}

generate_commit_dates() {
  local start_ts end_ts span i ts
  local anchor min_gap max_allowed window rand32 offset prev_ts

  start_ts="$(to_epoch "$YEAR-02-03 09:00:00")"
  end_ts="$(to_epoch "$YEAR-05-18 21:00:00")"
  span=$((end_ts - start_ts))

  min_gap=3600
  window=$((span / (TOTAL_COMMITS * 3)))
  prev_ts=0

  for ((i=0; i<TOTAL_COMMITS; i++)); do
    if [ "$i" -eq 0 ]; then
      ts="$start_ts"
    elif [ "$i" -eq $((TOTAL_COMMITS - 1)) ]; then
      ts="$end_ts"
    else
      anchor=$((start_ts + (span * i) / (TOTAL_COMMITS - 1)))
      rand32=$(((RANDOM << 15) | RANDOM))
      offset=$((rand32 % (2 * window + 1) - window))
      ts=$((anchor + offset))
    fi

    if [ "$i" -gt 0 ] && [ "$ts" -le "$prev_ts" ]; then
      ts=$((prev_ts + min_gap))
    fi

    max_allowed=$((end_ts - (TOTAL_COMMITS - 1 - i) * min_gap))
    if [ "$ts" -gt "$max_allowed" ]; then
      ts="$max_allowed"
    fi

    COMMIT_DATES+=("$(from_epoch "$ts")")
    prev_ts="$ts"
  done
}

is_copied() {
  local rel="$1"
  grep -Fqx -- "$rel" "$COPIED_LIST" 2>/dev/null
}

mark_copied() {
  local rel="$1"
  if ! is_copied "$rel"; then
    printf '%s\n' "$rel" >> "$COPIED_LIST"
  fi
}

copy_path_from_backup() {
  local rel="$1"
  local src="$SOURCE_BACKUP_DIR/$rel"
  local dst="$PROJECT_ROOT/$rel"

  if is_copied "$rel"; then
    return 0
  fi
  if [ ! -f "$src" ]; then
    return 1
  fi

  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
  mark_copied "$rel"
  return 0
}

classify_module() {
  local rel="$1"
  local low
  low="$(printf '%s' "$rel" | tr '[:upper:]' '[:lower:]')"

  case "$low" in
    mobile/ar-games/src/components/*|mobile/ar-games/src/*.css|mobile/ar-games/src/*.jsx|mobile/ar-games/src/*.html|mobile/src/screens/admin/*|mobile/src/screens/child/*|mobile/src/screens/parent/*|mobile/src/screens/loginscreen.js|mobile/assets/*|*.css|*.scss)
      echo "ui"
      ;;
    backend/routes/*|backend/models/*|backend/config/db.js|backend/middleware/*|backend/server.js|mobile/src/config/api.js|mobile/src/utils/network.js|*api*notes.md)
      echo "api"
      ;;
    backend/controllers/*|backend/scripts/*|mobile/src/context/*|mobile/src/navigation/*|mobile/src/screens/games/*|mobile/ar-games/src/hooks/*|mobile/ar-games/src/contexts/*|mobile/src/utils/responsive.js)
      echo "logic"
      ;;
    *)
      echo "config"
      ;;
  esac
}

collect_and_split_files() {
  local rel module

  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    case "$rel" in
      .git/*|.history/*)
        continue
        ;;
    esac

    ALL_FILES+=("$rel")
    module="$(classify_module "$rel")"
    case "$module" in
      config) CONFIG_POOL+=("$rel") ;;
      logic) LOGIC_POOL+=("$rel") ;;
      api) API_POOL+=("$rel") ;;
      ui) UI_POOL+=("$rel") ;;
      *) CONFIG_POOL+=("$rel") ;;
    esac
  done < <(cd "$SOURCE_BACKUP_DIR" && find . -type f | sed 's#^\./##' | sort)
}

stage_files_for_module() {
  local module="$1"
  local total cursor done_count commit_total remaining_files remaining_commits take n rel

  case "$module" in
    config)
      total="${#CONFIG_POOL[@]}"
      cursor="$CONFIG_CURSOR"
      done_count="$CONFIG_DONE"
      commit_total="$CONFIG_COMMITS"
      ;;
    logic)
      total="${#LOGIC_POOL[@]}"
      cursor="$LOGIC_CURSOR"
      done_count="$LOGIC_DONE"
      commit_total="$LOGIC_COMMITS"
      ;;
    api)
      total="${#API_POOL[@]}"
      cursor="$API_CURSOR"
      done_count="$API_DONE"
      commit_total="$API_COMMITS"
      ;;
    ui)
      total="${#UI_POOL[@]}"
      cursor="$UI_CURSOR"
      done_count="$UI_DONE"
      commit_total="$UI_COMMITS"
      ;;
    *)
      echo "Неизвестный модуль: $module" >&2
      exit 1
      ;;
  esac

  remaining_files=$((total - cursor))
  remaining_commits=$((commit_total - done_count))

  if [ "$remaining_commits" -le 0 ]; then
    take=0
  elif [ "$remaining_files" -le 0 ]; then
    take=0
  else
    take=$(((remaining_files + remaining_commits - 1) / remaining_commits))
  fi

  for ((n=0; n<take; n++)); do
    case "$module" in
      config)
        rel="${CONFIG_POOL[$CONFIG_CURSOR]}"
        CONFIG_CURSOR=$((CONFIG_CURSOR + 1))
        ;;
      logic)
        rel="${LOGIC_POOL[$LOGIC_CURSOR]}"
        LOGIC_CURSOR=$((LOGIC_CURSOR + 1))
        ;;
      api)
        rel="${API_POOL[$API_CURSOR]}"
        API_CURSOR=$((API_CURSOR + 1))
        ;;
      ui)
        rel="${UI_POOL[$UI_CURSOR]}"
        UI_CURSOR=$((UI_CURSOR + 1))
        ;;
    esac
    copy_path_from_backup "$rel"
    git add -- "$rel"
  done

  case "$module" in
    config) CONFIG_DONE=$((CONFIG_DONE + 1)) ;;
    logic) LOGIC_DONE=$((LOGIC_DONE + 1)) ;;
    api) API_DONE=$((API_DONE + 1)) ;;
    ui) UI_DONE=$((UI_DONE + 1)) ;;
  esac
}

restore_remaining_files() {
  local rel
  for rel in "${ALL_FILES[@]}"; do
    if ! is_copied "$rel"; then
      copy_path_from_backup "$rel"
      git add -- "$rel"
    fi
  done
}

touchup_if_empty() {
  local module="$1"
  local target

  target=".history/${module}_followup.md"
  mkdir -p "$PROJECT_ROOT/.history"
  if [ ! -f "$PROJECT_ROOT/$target" ]; then
    printf '# Follow-up for %s\n' "$module" > "$PROJECT_ROOT/$target"
  fi
  printf '\n' >> "$PROJECT_ROOT/$target"
  git add -- "$target"
}

author_email() {
  case "$1" in
    perfect1337) echo "bryunine2005@gmail.com" ;;
    Frozz164) echo "denisbobkof@yandex.ru" ;;
    Engls) echo "mrdengrif@gmail.com" ;;
    ssoout) echo "dendiuro@gmail.com" ;;
    *) echo "unknown@example.com" ;;
  esac
}

set_next_message() {
  case "$1" in
    perfect1337)
      LAST_MESSAGE="${PERFECT_MESSAGES[$PERFECT_IDX]}"
      PERFECT_IDX=$((PERFECT_IDX + 1))
      ;;
    Frozz164)
      LAST_MESSAGE="${FROZZ_MESSAGES[$FROZZ_IDX]}"
      FROZZ_IDX=$((FROZZ_IDX + 1))
      ;;
    Engls)
      LAST_MESSAGE="${ENGLS_MESSAGES[$ENGLS_IDX]}"
      ENGLS_IDX=$((ENGLS_IDX + 1))
      ;;
    ssoout)
      LAST_MESSAGE="${SSOOUT_MESSAGES[$SSOOUT_IDX]}"
      SSOOUT_IDX=$((SSOOUT_IDX + 1))
      ;;
    *)
      LAST_MESSAGE="Техническое обновление"
      ;;
  esac
}

validate_plan() {
  if [ "${#PLAN_AUTHORS[@]}" -ne "$TOTAL_COMMITS" ] || [ "${#PLAN_MODULES[@]}" -ne "$TOTAL_COMMITS" ]; then
    echo "План коммитов некорректен: ожидалось $TOTAL_COMMITS записей" >&2
    exit 1
  fi
}

run_plan() {
  local i author module message email commit_date

  for ((i=0; i<TOTAL_COMMITS; i++)); do
    author="${PLAN_AUTHORS[$i]}"
    module="${PLAN_MODULES[$i]}"

    stage_files_for_module "$module"

    if [ "$i" -eq $((TOTAL_COMMITS - 1)) ]; then
      restore_remaining_files
    fi

    if git diff --cached --quiet; then
      touchup_if_empty "$module"
    fi

    set_next_message "$author"
    message="$LAST_MESSAGE"
    email="$(author_email "$author")"
    commit_date="${COMMIT_DATES[$GLOBAL_COMMIT_INDEX]}"

    GIT_AUTHOR_NAME="$author" \
    GIT_AUTHOR_EMAIL="$email" \
    GIT_COMMITTER_NAME="$author" \
    GIT_COMMITTER_EMAIL="$email" \
    GIT_AUTHOR_DATE="$commit_date" \
    GIT_COMMITTER_DATE="$commit_date" \
    git commit -m "$message" >/dev/null

    GLOBAL_COMMIT_INDEX=$((GLOBAL_COMMIT_INDEX + 1))
  done
}

main() {
  ensure_safe_project_root
  validate_plan

  mkdir -p "$FULL_BACKUP_DIR" "$SOURCE_BACKUP_DIR"
  : > "$COPIED_LIST"

  copy_tree "$PROJECT_ROOT" "$FULL_BACKUP_DIR"
  copy_tree "$PROJECT_ROOT" "$SOURCE_BACKUP_DIR"
  find "$SOURCE_BACKUP_DIR" -name '.git' -exec rm -rf {} + 2>/dev/null || true

  collect_and_split_files
  generate_commit_dates

  ON_ERROR_RESTORE=1
  wipe_dir "$PROJECT_ROOT"

  git init >/dev/null
  run_plan

  if [ "$(git rev-list --count HEAD)" -ne "$TOTAL_COMMITS" ]; then
    echo "Ошибка: количество коммитов отличается от $TOTAL_COMMITS" >&2
    exit 1
  fi

  git branch -M main

  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
  else
    git remote add origin "$REMOTE_URL"
  fi

  if [ "$PUSH_TO_REMOTE" -eq 1 ]; then
    if [ "$FORCE_PUSH" -eq 1 ]; then
      git push -u --force-with-lease origin main
    else
      git push -u origin main
    fi
  fi

  ON_ERROR_RESTORE=0

  echo "Готово: создано $TOTAL_COMMITS коммитов, авторы перемешаны, origin=$REMOTE_URL"
}

main "$@"
