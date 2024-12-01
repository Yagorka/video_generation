import requests
from PIL import Image
import requests
from io import BytesIO
from bs4 import BeautifulSoup

def autorization(login, password): 
    url = "https://mc.dev.rand.agency/api/v1/get-access-token"  # Не забудьте заменить YOUR_API_KEY на ваш личный ключ API [1](https://sky.pro/media/kak-rabotat-s-api-v-python/)
    headers = {'Content-Type': 'application/json;charset=utf-8', 'Accept': 'application/json'}
    query = {
    "email": login,
    "password": password,
    "device": "bot-v0.0.1"
    }
    try:
        response = requests.post(url, params=query, headers=headers)
        if response.status_code==200:
            return response.status_code, response.json()['access_token']
        else:
            if response.json()['errors'].keys()[0]=='password':
                return response.status_code, 'Неверный пароль'
            elif response.json()['errors'].keys()[0]=='email':
                return response.status_code, 'Несуществующий логин'
            else:
                return response.status_code, f'Неизвестная ошибка с кодом {response.status_code}'
    except:
        return -1, f'Авторизация не пройдена из-за неизвестной ошибки'

def get_my_pages(authorizate_token): 
    url = "https://mc.dev.rand.agency/api/cabinet/individual-pages"
    headers = {'Authorization': f'Bearer {authorizate_token}', 'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8'}

    try:
        response = requests.get(url, headers=headers)
        resp_json = response.json()
        if response.status_code==200:
            if len(resp_json)>0:
                return response.status_code, response.json()
            else:
                return -2, 'Ваш список доступных страниц пуст'

        else:
            return response.status_code, f'Неизвестная ошибка с кодом {response.status_code}'
    except Exception as ex:
        return -1, f'Страницы не найдены из-за ошибки: {ex}'

def load_photo(link):
    try:
        img = Image.open(BytesIO(requests.get(link).content))
        return 200, img
    except Exception as ex:
        return -1, f"Изображение не найдено {ex}"

def get_biography(url, token):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8'}
    try:
        response = requests.get(url, headers=headers)

        if response.status_code==200:
            response_text = response.text
            if len(response_text)>0:
                soup = BeautifulSoup(response_text, "html.parser")
                mydivs = soup.find_all("div", {"class": "m-biography__section"}) 
                res = {}
                for i, parent in enumerate(mydivs):
                    titles = parent.find_all("h3", {"class": "title title--s m-biography__section-title"})
                    texts = parent.find_all("div", {"class": "m-biography__section-text"})
                    images = parent.find_all("div", {"class": "m-biography__imgbox"})
                    for title, text in zip(titles, texts):
                        title = title.get_text()
                        text = text.get_text()
                        if i in res:
                            res[i]['title'] = title
                            res[i]['text'] = text
                        else:
                            res[i] = {}
                            res[i]['title'] = title
                            res[i]['text'] = text
                        for image in images:
                            image_text = image.find("span", {"class": "m-biography__img-name"})
                            image_url = images[0].find("img")
                            if 'images' in res[i]:
                                res[i]['images'].append((image_url['src'], image_text.get_text()))
                            else:
                                res[i]['images'] = [(image_url['src'], image_text.get_text())]                
                return response.status_code, res
            else:
                return -2, 'Данные на странице пустые'

        else:
            return response.status_code, f'Неизвестная ошибка с кодом {response.status_code}'
    except Exception as ex:
        return -1, f'Страницы не найдены из-за {ex}'