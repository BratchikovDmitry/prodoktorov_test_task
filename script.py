import os
import re
from datetime import datetime

import requests.exceptions
from requests import get


def get_data_from_api():
    """
    This function handles response from API to get useful data.
    If any http error received raise an exception.

    :return: list of dictionaries with data for report or False.

    """
    try:
        data_list = []

        users_list = get("https://json.medrating.org/users").json()
        for user in users_list:
            user_data = {
                "username": user["username"],
                "name": user["name"],
                "company": user["company"]["name"],
                "email": user["email"],
            }

            tasks = get("https://json.medrating.org/todos",
                        params={"userId": user["id"]}).json()
            user_data["tasks_count"] = len(tasks)
            if tasks:
                user_data["done"] = [task["title"] for task in tasks if task["completed"]]
                user_data["not_done"] = [task["title"] for task in tasks if not task["completed"]]

            data_list.append(user_data)
        return data_list
    except requests.exceptions.RequestException:
        raise
    except KeyError as e:
        print(f"Error in response data. Key not found {e}")
        return False


def get_file_string(user_data: dict):
    """
    This function generate reports' string.

    :param user_data: dictionary of necessary params for report
    :return: finished string for file writing or False if KeyError received

    """
    try:
        file_string = f"Отчёт для {user_data['company']}.\n" \
                      f"{user_data['name']} <{user_data['email']}>" \
                      f" {datetime.now().strftime('%d.%m.%Y %H:%M')}\n" \
                      f"Всего задач: {user_data['tasks_count']}\n" \

        if 'done' in user_data and len(user_data['done']):
            file_string += f"\nЗавершённые задачи ({len(user_data['done'])}):\n"
            for task in user_data['done']:
                file_string += f"{task}\n" if len(task) < 48 else f"{task[:48]}...\n"
        file_string += f"\nОставшиеся задачи ({len(user_data['not_done'])}):\n"

        if 'not_done' and len(user_data['not_done']):
            for task in user_data['not_done']:
                file_string += f"{task}\n" if len(task) < 48 else f"{task[:48]}...\n"

        return file_string
    except KeyError as e:
        print(f"Error in user data. Key not found: {e}")
        return False


if __name__ == "__main__":
    if not os.path.exists("tasks"):
        os.mkdir("tasks")

    users_data = get_data_from_api()

    for user_info in users_data:
        if os.path.exists(f"tasks/{user_info['username']}.txt"):
            with open(f"tasks/{user_info['username']}.txt", "r") as file:
                date_line = file.readlines()[1]
                date = re.findall(r'\d{2}.\d{2}.\d{4} \d{2}:\d{2}', date_line)
                date = datetime.strptime(date[0], '%d.%m.%Y %H:%M')
                date = date.strftime("%Y-%m-%dT%H:%M")
                os.rename(file.name,
                          f"tasks/old_{user_info['username']}_{date}.txt")

        string_for_file = get_file_string(user_info)
        if string_for_file:
            with open(f"tasks/{user_info['username']}.txt", "w") as file:
                file.write(string_for_file)
