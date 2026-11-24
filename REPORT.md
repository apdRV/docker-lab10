### 1. Клонирование репозитория

Склонировал репозиторий и изучил структуру проекта:

Первоначальный `docker-compose.yml` выглядел корректно, поэтому сразу попробовал поднять контейнеры.

### 2. Падение app2

При выполнении `docker compose up` контейнер `app2` не поднимался. В логах была ошибка:

```python
python3: can't open file '//app1.py': [Errno 2] No such file or directory
```

**Причина:** в `Dockerfile` для app2 в `CMD` был указан файл `app1.py` вместо `app2.py`.

После этого app2 начал запускаться. Осталась только ошибка nginx.

### 3. Ошибка nginx

Nginx падал со следующей ошибкой:

```nginx
nginx: [emerg] host not found in upstream "app" in /etc/nginx/conf.d/default.conf:9
```

**Причина:** в конфигурации nginx в блоке `proxy_pass` был указан несуществующий хост `app`:

```nginx
location / {
    proxy_pass http://app;
}
```

Заменил proxy_pass http://app; на proxy_pass http://loadbalancer;

### 4. Отсутствие SSL-сертификатов

После исправления upstream nginx снова упал, теперь с ошибкой:

```nginx
nginx: [emerg] cannot load certificate "/etc/nginx/www.example.com.crt":
BIO_new_file() failed (SSL: ... No such file or directory ...)
```

**Причина:** в nginx.conf указаны пути к сертификату и ключу (www.example.com.crt, www.example.com.key), но в Dockerfile nginx эти файлы не копировались в образ.

После этого nginx успешно запустился.

### 5. Неверный маппинг портов

Nginx запустился, но по адресу localhost:445 был недоступен.

**Причина:** в docker-compose.yml был указан маппинг "445:445", а nginx внутри контейнера слушает порт 443 (согласно директиве listen 443 ssl; в конфиге).

Изменил маппинг на "443:443" в docker-compose.yml.

После этого curl -k https://localhost:443/ начал возвращать ответ, но с ошибкой 502 Bad Gateway.

### 6. Неверные порты бэкендов в upstream

Nginx не мог достучаться до бэкендов:

```html
<html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>nginx/1.31.10</center>
</body>
</html>
```

**Причина:** в nginx.conf в upstream-блоке у обоих серверов был указан порт 81:

```nginx
upstream loadbalancer {
    least_conn;
    server app1:81;
    server app2:81;
}
```

Заменил порты на реальные:

```nginx
upstream loadbalancer {
    least_conn;
    server app1:8080;
    server app2:80;
}
```

### 7. Ошибки python файлов

После исправления портов curl -k https://localhost/ стал возвращать 404 Not Found, а /hello — 500.

**Причина:** в коде приложений была попытка отрендерить шаблон index.html, но flask по умолчанию ищет его в папке templates/ рядом с appX.py. А у нас index.html лежит в папке storage/, которая монтируется в контейнеры как /storage.

Убрал маппинг на /hello, так как по условию задания страница должна открываться по корневому пути /.
В app1.py и app2.py указал явный путь к папке с шаблонами:

```python
app = Flask(__name__, template_folder="/storage")
```

После этого curl -k https://localhost/ начал возвращать корректную HTML-страницу:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Fashion Digital</title>
</head>
<body>
<h1>Hello World from app1!</h1>
</body>
</html>
```

### 8. app2 возвращает ответ без своего имени

**Причина:** в app2.py в функции hello_world() при рендере шаблона не был указан параметр source_app='app2', поэтому в шаблоне ничего не подставлялось.

В app2.py явно указал source_app='app2'
