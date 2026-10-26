
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание PERT-задач в YouTrack Cloud:
  - 9 эпиков типа Epic;
  - 45 задач типа Task;
  - оценки Ei в поле Period;
  - назначения спринтов в поле Sprint;
  - реальные связи Subtask of с эпиками.

Настройки через переменные окружения:
  YOUTRACK_URL
  YOUTRACK_TOKEN
  YOUTRACK_PROJECT       по умолчанию EMI
  YOUTRACK_TYPE_FIELD    по умолчанию Type
  YOUTRACK_ESTIMATE_FIELD по умолчанию Оценка
  YOUTRACK_SPRINT_FIELD  по умолчанию Sprint

Проверка без запросов к API:
  python create_emias_pert.py --dry-run

ВНИМАНИЕ: повторный запуск без dry-run создаст новые задачи-дубликаты.
"""

import os
import sys
import argparse
import requests


BASE_URL = os.environ.get("YOUTRACK_URL", "https://epi-emias-lab2.youtrack.cloud").rstrip("/")
TOKEN = os.environ.get("YOUTRACK_TOKEN", "perm-YWRtaW4=.NDgtMA==.ZoVcBoft5q1yORrDj17mFLa766cHdm")
PROJECT_KEY = os.environ.get("YOUTRACK_PROJECT", "EMI")

TYPE_FIELD = os.environ.get("YOUTRACK_TYPE_FIELD", "Type")
ESTIMATE_FIELD = os.environ.get("YOUTRACK_ESTIMATE_FIELD", "Estimated")
SPRINT_FIELD = os.environ.get("YOUTRACK_SPRINT_FIELD", "Sprint")


# Для каждой группы задач указан спринт.
# Названия спринтов должны точно совпадать со значениями поля Sprint в YouTrack.
EPICS = [
    {
        "summary": "1. Подготовка",
        "sprint": "1. Проектирование и подготовка",
        "tasks": [
            ("1.1", "Сбор и анализ функциональных и нефункциональных требований проекта", 25.33),
            ("1.2", "Составление SRS", 20.67),
            ("1.3", "Выбор архитектуры проекта", 14.67),
            ("1.4", "Выбор стека проекта", 8.33),
            ("1.5", "Распределение обязанностей", 4.00),
            ("1.6", "Дизайн в Figma, создание дизайн-системы, подготовка ассетов", 40.00),
        ],
    },
    {
        "summary": "2. Общие компоненты",
        "sprint": "2. Общие компоненты и главная страница",
        "tasks": [
            ("2.1", "Общий хедер с навигацией", 7.83),
            ("2.2", "Общий футер с медиа ссылками", 5.83),
            ("2.3", "Разработка общих компонентов (модальное окно, таблицы, карточки)", 21.33),
        ],
    },
    {
        "summary": "3. Главная страница",
        "sprint": "2. Общие компоненты и главная страница",
        "tasks": [
            ("3.1", "Форма записи по полису", 4.17),
            ("3.2", "Информация о прикреплении к медорганизации", 3.17),
            ("3.3", "Описание возможностей сервиса", 2.00),
            ("3.4", "Плитка со ссылкой на авторизацию через mos.ru", 2.00),
            ("3.5", "Раздел о мобильном приложении", 3.50),
        ],
    },
    {
        "summary": "4. Страница медучреждений",
        "sprint": "3. Медучреждения и медицинские справки",
        "tasks": [
            ("4.1", "Список карточек медучреждений", 20.00),
            ("4.2", "Поиск по названию, адресу или метро", 11.33),
            ("4.3", "Фильтр по типу учреждения", 3.167),
            ("4.4", "Карта Москвы с маркерами учреждений", 31.333),
            ("4.5", "Запись с помощью маркеров на карте", 10.00),
            ("4.6", "Переключатель режима отображения списка учреждений", 2.167),
        ],
    },
    {
        "summary": "5. Страница справок",
        "sprint": "3. Медучреждения и медицинские справки",
        "tasks": [
            ("5.1", "Карточка о записи на медкомиссию при записи к врачу", 2.00),
            ("5.2", "Карточка с алгоритмом записи на комиссию", 5.00),
            ("5.3", "Переключатель цели медкомиссии ГИБДД/Оружие", 2.00),
            ("5.4", "Список освидетельствований для ГИБДД", 10.00),
            ("5.5", "Список освидетельствований для Оружия", 8.00),
            ("5.6", "Информационное сообщение об одновременном оформлении справок", 2.00),
        ],
    },
    {
        "summary": "6. Авторизация",
        "sprint": "4. Авторизация и запись к врачу",
        "tasks": [
            ("6.1", "Авторизация через mos.id", 16.667),
            ("6.2", "Получение персональных данных с mos.id", 9.833),
            ("6.3", "Смена аккаунта mos.id", 7.00),
            ("6.4", "Выход из аккаунта", 4.167),
        ],
    },
    {
        "summary": "7. Страница расписания медучреждения",
        "sprint": "4. Авторизация и запись к врачу",
        "tasks": [
            ("7.1", "Карточка с информацией об учреждении", 4.167),
            ("7.2", "Список специалистов учреждения", 11.333),
            ("7.3", "Модальное окно расписания специалиста", 8.50),
            ("7.4", "Сообщение об отсутствии расписания", 3.00),
        ],
    },
    {
        "summary": "8. Запись к врачу",
        "sprint": "4. Авторизация и запись к врачу",
        "tasks": [
            ("8.1", "Навигация по разделам", 5.333),
            ("8.2", "Отображение списка полисов ОМС", 4.333),
            ("8.3", "Форма добавления полиса ОМС", 14.667),
            ("8.4", "Отображение списка медучреждений, к которым прикреплён полис ОМС", 13.00),
            ("8.5", "Отображение списка записей пользователя", 10.00),
            ("8.6", "Форма добавления записи", 31.333),
        ],
    },
    {
        "summary": "9. Общее",
        "sprint": "5. Тестирование, запуск и поддержка",
        "tasks": [
            ("9.1", "Модульные тесты", 75.00),
            ("9.2", "Интеграционные тесты", 120.00),
            ("9.3", "Аренда хостинга", 7.833),
            ("9.4", "Тестирование на стенде", 21.667),
            ("9.5", "Адаптивная вёрстка", 24.00),
        ],
    },
]


class YouTrack:
    def __init__(self, base_url, token, dry_run=False):
        self.base_url = base_url
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def request(self, method, path, **kwargs):
        response = self.session.request(
            method,
            f"{self.base_url}/api/{path.lstrip('/')}",
            timeout=30,
            **kwargs,
        )

        if not response.ok:
            raise RuntimeError(
                f"{method} {path}: HTTP {response.status_code}\n"
                f"{response.text[:2000]}"
            )

        if response.status_code == 204 or not response.text.strip():
            return None

        return response.json()

    def get_project(self, project_key):
        projects = self.request(
            "GET",
            "admin/projects",
            params={
                "fields": "id,shortName,name",
                "$top": "1000",
            },
        )

        matches = [
            project
            for project in projects
            if project.get("shortName", "").upper() == project_key.upper()
        ]

        if len(matches) != 1:
            raise RuntimeError(
                f"Не удалось однозначно найти проект с ключом {project_key!r}. "
                "Проверь YOUTRACK_PROJECT."
            )

        return matches[0]

    def get_subtask_link(self):
        link_types = self.request(
            "GET",
            "issueLinkTypes",
            params={
                "fields": (
                    "id,name,sourceToTarget,targetToSource,"
                    "directed,aggregation"
                ),
            },
        )

        for link in link_types:
            if (
                link.get("directed")
                and link.get("aggregation")
                and link.get("sourceToTarget", "").lower() == "parent for"
                and link.get("targetToSource", "").lower() == "subtask of"
            ):
                # Связываем эпик с дочерней задачей в направлении Parent for.
                return link["id"] + "s"

        available = "\n".join(
            f"  {item.get('name')}: "
            f"{item.get('sourceToTarget')} / {item.get('targetToSource')}"
            for item in link_types
        )

        raise RuntimeError(
            "Не найден тип связи Parent for / Subtask of.\n"
            "Доступные типы связей:\n" + available
        )

    def create_issue(
        self,
        project_id,
        summary,
        description,
        issue_type,
        estimate=None,
        sprint=None,
    ):
        custom_fields = [
            {
                "name": TYPE_FIELD,
                "$type": "SingleEnumIssueCustomField",
                "value": {"name": issue_type},
            },
        ]

        if estimate is not None:
            custom_fields.append({
                "name": ESTIMATE_FIELD,
                "$type": "PeriodIssueCustomField",
                "value": {"minutes": round(estimate * 60)},
            })

        if sprint is not None:
            custom_fields.append({
                "name": SPRINT_FIELD,
                "$type": "SingleEnumIssueCustomField",
                "value": {"name": sprint},
            })

        payload = {
            "project": {"id": project_id},
            "summary": summary,
            "description": description,
            "customFields": custom_fields,
        }

        if self.dry_run:
            estimate_text = (
                f", Ei={estimate:g} ч" if estimate is not None else ""
            )
            sprint_text = f", Sprint={sprint}" if sprint else ""
            print(f"[DRY RUN] {issue_type}: {summary}{estimate_text}{sprint_text}")
            return {
                "id": f"dry-{summary}",
                "idReadable": "DRY-RUN",
                "summary": summary,
            }

        return self.request(
            "POST",
            "issues",
            params={"fields": "id,idReadable,summary"},
            json=payload,
        )

    def link_child(self, epic, child, link_id):
        if self.dry_run:
            print(f"    [DRY RUN] Связь Subtask of: {child['summary']}")
            return

        self.request(
            "POST",
            f"issues/{epic['id']}/links/{link_id}/issues",
            params={"fields": "id,idReadable,summary"},
            json={"id": child["id"]},
        )


def main():
    parser = argparse.ArgumentParser(
        description="Создание эпиков, PERT-задач и связей в YouTrack."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать план без обращения к YouTrack.",
    )
    args = parser.parse_args()

    if not args.dry_run:
        if not BASE_URL or not TOKEN:
            sys.exit(
                "Задай YOUTRACK_URL и YOUTRACK_TOKEN в переменных окружения."
            )

        if not BASE_URL.startswith("https://"):
            sys.exit("YOUTRACK_URL должен начинаться с https://")

    total_tasks = sum(len(epic["tasks"]) for epic in EPICS)
    total_hours = sum(
        estimate
        for epic in EPICS
        for _, _, estimate in epic["tasks"]
    )

    print(f"Проект: {PROJECT_KEY}")
    print(f"Эпиков: {len(EPICS)}")
    print(f"Обычных задач: {total_tasks}")
    print(f"Связей с эпиками: {total_tasks}")
    print(f"Сумма оценок Ei: {total_hours:.2f} ч")
    print()

    yt = YouTrack(BASE_URL, TOKEN, dry_run=args.dry_run)

    if args.dry_run:
        project = {"id": "dry-project", "shortName": PROJECT_KEY}
        link_id = "dry-link"
    else:
        me = yt.request(
            "GET",
            "users/me",
            params={"fields": "id,login"},
        )
        print(f"Подключение выполнено от имени: {me.get('login', me.get('id'))}")

        project = yt.get_project(PROJECT_KEY)
        link_id = yt.get_subtask_link()

    print(f"Найден проект: {project.get('shortName', PROJECT_KEY)}")
    print()

    created_epics = 0
    created_tasks = 0
    created_links = 0

    for epic_data in EPICS:
        epic_summary = epic_data["summary"]

        epic = yt.create_issue(
            project["id"],
            epic_summary,
            "Группа задач проекта emias.info по PERT-плану.",
            "Epic",
        )
        created_epics += 1

        print(
            f"Эпик {epic.get('idReadable', '')}: {epic_summary}"
        )

        for number, title, estimate in epic_data["tasks"]:
            task_summary = f"{number} {title}"
            sprint = epic_data["sprint"]

            description = (
                "Задача из PERT-плана проекта emias.info.\n"
                f"Номер: {number}\n"
                f"Эпик: {epic_summary}\n"
                f"Спринт: {sprint}\n"
                f"Ожидаемая длительность Ei: {estimate:g} ч."
            )

            task = yt.create_issue(
                project["id"],
                task_summary,
                description,
                "Task",
                estimate=estimate,
                sprint=sprint,
            )
            created_tasks += 1

            yt.link_child(epic, task, link_id)
            created_links += 1

            print(
                f"  {task.get('idReadable', '')}: {task_summary} "
                f"| Ei={estimate:g} ч | Sprint={sprint}"
            )

    print("\nГотово.")
    print(f"Создано эпиков: {created_epics}")
    print(f"Создано задач: {created_tasks}")
    print(f"Создано связей: {created_links}")
    print(f"Сумма Ei: {total_hours:.2f} ч")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        print(f"\nОШИБКА: {exc}", file=sys.stderr)
        sys.exit(1)
