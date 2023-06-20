import json
import sys
import time

import fake_useragent
import requests
from art import *
from bs4 import BeautifulSoup

user_agent = fake_useragent.UserAgent()
spider_art = text2art('Simple       Parser       -->       hh.ru', chr_ignore=True)
print(spider_art)


def get_city_id(city_name, json_data):
    for city in json_data:
        if city['name'].lower() == city_name.lower():
            return int(city['id'])
        elif city['areas']:
            nested_city_id = get_city_id(city_name, city['areas'])
            if nested_city_id:
                return int(nested_city_id)
    return None


def get_links(text, city_name):
    with open('areas.json', 'r', encoding='utf-8') as f:
        data_json = json.load(f)
        city_id = get_city_id(city_name, data_json)
        if not city_id:
            return print(f"Идентификатор для города '{city_name.capitalize()}' не найден.")

    response = requests.get(
        f'https://hh.kz/search/vacancy?text={text}&salary=&area={city_id}&ored_clusters=true',
        headers={'user-agent': user_agent.random}
    )
    if response.status_code != 200:
        return
    soup = BeautifulSoup(response.content, 'lxml')
    try:
        page_count = int(
            soup.find('div', attrs={'class': 'pager'}).find_all('span', recursive=False)[-1].find('a').find(
                'span').text)
    except:
        return
    for page in range(page_count):
        try:
            response = requests.get(
                f'https://hh.kz/search/vacancy?text={text}&salary=&area={city_id}&ored_clusters=true&page={page}',
                headers={'user-agent': user_agent.random}
            )
            soup = BeautifulSoup(response.content, 'lxml')
            for a in soup.find_all('a', attrs={'class': 'serp-item__title'}):
                yield f"{a.attrs['href']}"
        except Exception as e:
            print(f'{e}')


def get_jobs(link):
    response = requests.get(link, headers={'user-agent': user_agent.random})
    if response.status_code != 200:
        return
    soup = BeautifulSoup(response.content, 'lxml')
    try:
        title = soup.find('div', attrs={'class': 'vacancy-title'}).text.replace('\xa0', '')
        salary = soup.find('div', attrs={'data-qa': 'vacancy-salary'}).text.replace('\xa0', '')
        experience = soup.find('p', attrs={'class': 'vacancy-description-list-item'}).text.replace('\xa0', '')
        tags = [tag.text for tag in soup.find('div', attrs={'class': 'bloko-tag-list'})]
    except:
        title, salary, experience, link, tags = None, None, None, None, None
    vacancy = {
        'title': title,
        'salary': salary,
        'experience': experience,
        'link': link,
        'tags': tags,
    }
    return vacancy


if __name__ == '__main__':
    vacancy_data = []
    try:
        start_time = time.time()
        vacancy_name = input('Введите название вакансии --> ')
        city_name = input('Введите название города в котором хотите выполнить поиск --> ')

        for links in get_links(vacancy_name, city_name):
            job = get_jobs(links)
            if job and all(value is not None for value in job.values()):
                vacancy_data.append(job)
                print(f"Добавлена вакансия --> {job['title']}")
            else:
                print('Запись была исключена!')
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(vacancy_data, f, indent=5, ensure_ascii=False)
        end_time = time.time()
        elapsed_time = start_time - end_time
        if elapsed_time < 60:
            print(f"Программа успешно завершена за {abs(elapsed_time):.2f} секунд!")
        else:
            print(f"Программа успешно завершена за {elapsed_time // 60:.0f} минут {elapsed_time % 60:.2f} секунд!")
    except KeyboardInterrupt:
        print('Программа успешно завершена!')
        sys.exit(0)
