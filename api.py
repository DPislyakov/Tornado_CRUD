from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop
import json
import base64

items = {}


class TodoItems(RequestHandler):
    # Получение полного списка запросов
    async def get(self):
        self.write({'items': items})


class GetKey(RequestHandler):
    # Получения запроса по ключу /api/get?key=key
    async def get(self):
        try:
            key = self.get_argument('key', None)
            if key in items.keys():
                self.write({'body': items[key][0],
                            'duplicates': len(items[key])-1})
            else:
                self.write({})
        except Exception as e:
            self.send_error(status_code=400)


# Создание тела запроса и генерация ключа POST /api/add/ -d {}
class AddItem(RequestHandler):

    async def post(self, _):
        try:
            params = json.loads(self.request.body.decode())
            keystr = ''
            body_value = ''

            if params:
                # Формируем строки для генерации ключа
                for key, param in params.items():
                    keystr += key
                    # Проверка, есть ли в теле запроса списки
                    if isinstance(param, list):
                        for string in param:
                            body_value += string
                    else:
                        body_value += param

                # Генерируем ключ
                finish_str = keystr + body_value
                id_bytes = finish_str.encode('ascii')
                finish_bytes = base64.b64encode(id_bytes)
                finish_id = finish_bytes.decode('ascii')

                # Используем список, длина которого и есть счетчик дубликатов
                items.setdefault(finish_id, []).append(params)
                self.write({'Key': finish_id})

        except Exception as e:
            self.send_error(status_code=400)


class RemoveItem(RequestHandler):
    # Удаление запроса по ключу /api/remove/
    async def delete(self, key_id):
        try:
            if key_id in items.keys():
                del items[key_id]
            else:
                self.send_error(status_code=404, message="The Resource You Are Trying To Delete Does Not Exist")

        except Exception as e:
            self.send_error(status_code=400)


class UpdateItem(RequestHandler):
    # Изменение тела запроса и создание нового ключа, счетчик дубликатов обнуляется /api/update/
    async def put(self, key_id):
        try:
            if key_id in items.keys():

                params = json.loads(self.request.body.decode())
                new_item = items[key_id][0]
                del items[key_id]

                for key_param in params.keys():
                    if key_param in new_item.keys():
                        new_item[key_param] = params[key_param]

                keystr = ''
                body_value = ''

                for key in new_item.keys():
                    keystr += key
                    body_value += new_item[key]

                finish_str = keystr + body_value
                id_bytes = finish_str.encode('ascii')
                finish_bytes = base64.b64encode(id_bytes)
                finish_id = finish_bytes.decode('ascii')

                items.setdefault(finish_id, []).append(new_item)
                self.write({'Key': finish_id})

            else:
                self.send_error(status_code=404, message="The Resource You Are Trying To Update Does Not Exist")

        except Exception as e:
            self.send_error(status_code=400)


class StatisticDupl(RequestHandler):
    # Получение процента дубликатов от общего количества запросов /api/statistic
    # В случае отсутствия дубликатов возвращаем уведомление об их отсутствии
    async def get(self):
        try:
            count_duplicates = 0
            count_request = 0
            for key in items.keys():
                count_duplicates += (len(items[key]) - 1)
                count_request += len(items[key])

            if count_duplicates == 0:
                self.write("There are no duplicates")
            else:
                duplicates_rate = (count_duplicates/count_request)
                duplicates_rate1 = float("{:.2f}".format(duplicates_rate)) * 100
                self.write(f"Duplicate rate: {duplicates_rate1}%")

        except Exception as e:
            self.send_error(status_code=400)


def make_app():
    urls = [
        ("/", TodoItems),
        ("/api/get", GetKey),
        (r"/api/add/([^/]+)?", AddItem),
        (r"/api/remove/([^/]+)?", RemoveItem),
        (r"/api/update/([^/]+)?", UpdateItem),
        (r"/api/statistic", StatisticDupl)
    ]
    return Application(urls, debug=True)


if __name__ == '__main__':
    app = make_app()
    app.listen(5000)
    IOLoop.instance().start()
