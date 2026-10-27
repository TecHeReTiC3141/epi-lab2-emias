
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Создание Git-веток для PERT-задач YouTrack.

Формат: feature/EMI-123-short-description

Переменные окружения:
  YOUTRACK_URL
  YOUTRACK_TOKEN
  YOUTRACK_PROJECT (по умолчанию EMI)

Запуск:
  python create_task_branches.py --dry-run
  python create_task_branches.py
  python create_task_branches.py --push
"""

import os
import re
import sys
import argparse
import subprocess
import requests


BASE_URL = os.environ.get("YOUTRACK_URL", "https://epi-emias-lab2.youtrack.cloud").rstrip("/")
TOKEN = os.environ.get("YOUTRACK_TOKEN", "perm-YWRtaW4=.NDgtMA==.ZoVcBoft5q1yORrDj17mFLa766cHdm")
PROJECT_KEY = os.environ.get("YOUTRACK_PROJECT", "EMI")

# В названиях импортированных задач есть префиксы 1.1, 1.2 ... 9.5.
TASK_PATTERN = re.compile(r"^\d+\.\d+\s+")

TRANSLITERATION = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def run_git(*args, check=True, capture_output=True):
    """Выполняет команду Git."""
    result = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=capture_output,
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} завершился с ошибкой:\n"
            f"{result.stderr.strip()}"
        )

    return result


def transliterate(text):
    """Преобразует кириллицу в латиницу."""
    result = []

    for char in text.lower():
        if char in TRANSLITERATION:
            result.append(TRANSLITERATION[char])
        else:
            result.append(char)

    return "".join(result)


def make_slug(summary):
    """Создаёт короткое описание для имени ветки."""
    # Удаляем номер задачи в начале, например '1.1 '.
    title = TASK_PATTERN.sub("", summary)

    slug = transliterate(title)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    # Ограничиваем длину имени ветки.
    return slug[:45].rstrip("-") or "task"


def get_youtrack_tasks():
    """Получает задачи проекта через YouTrack REST API."""
    if not BASE_URL or not TOKEN:
        raise RuntimeError(
            "Задай переменные окружения YOUTRACK_URL и YOUTRACK_TOKEN."
        )

    if not BASE_URL.startswith("https://"):
        raise RuntimeError("YOUTRACK_URL должен начинаться с https://")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    })

    response = session.get(
        f"{BASE_URL}/api/issues",
        params={
            "query": f"project: {PROJECT}",
            "fields": "id,idReadable,summary",
            "$top": "100",
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"YouTrack API вернул HTTP {response.status_code}:\n"
            f"{response.text[:1500]}"
        )

    issues = response.json()

    # Оставляем только задачи, чьи названия начинаются с номера PERT.
    tasks = [
        issue for issue in issues
        if TASK_PATTERN.match(issue.get("summary", ""))
    ]

    # Не допускаем неоднозначности в именах веток.
    seen = set()
    unique_tasks = []

    for task in tasks:
        issue_id = task.get("idReadable")
        if not issue_id:
            continue

        if issue_id not in seen:
            seen.add(issue_id)
            unique_tasks.append(task)

    return sorted(
        unique_tasks,
        key=lambda task: tuple(
            int(part)
            for part in re.match(
                r"^(\d+)\.(\d+)",
                task["summary"],
            ).groups()
        ),
    )


def get_base_branch(explicit_base=None):
    """Определяет основную ветку репозитория."""
    if explicit_base:
        return explicit_base

    result = run_git(
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
        check=False,
    )

    if result.returncode == 0:
        return result.stdout.strip()

    for candidate in (
        "origin/main",
        "origin/master",
        "main",
        "master",
    ):
        result = run_git(
            "rev-parse",
            "--verify",
            "--quiet",
            candidate,
            check=False,
        )
        if result.returncode == 0:
            return candidate

    raise RuntimeError(
        "Не удалось определить основную ветку. "
        "Укажи её явно через --base, например --base main."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Создание feature-веток для задач YouTrack."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать ветки, ничего не создавать.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="После создания отправить ветки в origin.",
    )
    parser.add_argument(
        "--base",
        help="Базовая ветка, например origin/main или main.",
    )
    args = parser.parse_args()

    # Проверяем, что команда выполняется внутри Git-репозитория.
    run_git("rev-parse", "--show-toplevel")

    tasks = get_youtrack_tasks()

    if not tasks:
        raise RuntimeError(
            "Не найдено задач с номерами вида 1.1, 1.2 ... 9.5. "
            "Проверь проект и названия задач в YouTrack."
        )

    if len(tasks) != 45:
        print(
            f"Внимание: найдено {len(tasks)} задач вместо ожидаемых 45. "
            "Проверь выборку до создания веток."
        )

    base = get_base_branch(args.base)

    print(f"Проект YouTrack: {PROJECT}")
    print(f"Базовая ветка: {base}")
    print(f"Найдено задач: {len(tasks)}")
    print()

    created = 0
    existing = 0

    for task in tasks:
        issue_id = task["idReadable"]
        summary = task["summary"]
        slug = make_slug(summary)
        branch = f"feature/{issue_id}-{slug}"

        print(f"{branch}")
        print(f"  Задача: {summary}")

        if args.dry_run:
            continue

        # Если ветка уже есть, не создаём её повторно.
        result = run_git(
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
            check=False,
        )

        if result.returncode == 0:
            print("  Уже существует локально — пропускаем создание.")
            existing += 1
        else:
            run_git("branch", branch, base)
            print("  Создана.")
            created += 1

        if args.push:
            # Публикуем ветку в remote origin.
            run_git("push", "-u", "origin", branch)
            print("  Отправлена в origin.")

        print()

    if args.dry_run:
        print("Проверка завершена. Ветки не создавались.")
    else:
        print("Готово.")
        print(f"Создано локальных веток: {created}")
        print(f"Уже существовало: {existing}")
        if args.push:
            print("Отправка в origin выполнена для всех найденных веток.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, requests.RequestException, ValueError) as exc:
        print(f"\nОШИБКА: {exc}", file=sys.stderr)
        sys.exit(1)
