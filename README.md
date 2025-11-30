# weatheraBaburDeveloper
Paydalanıwshıǵa real waqıt rejiminde hawa rayı maǵlıwmatların usınıs etiwshi Telegram bot.  Joybar Django backend, OpenWeather API hám jergilikli JSON qala yamasa rayon mappingi tiykarında isleydi.

                                            ----------Assalomu alaykum!----------
WeatherBot

WeatherBot-paydalanıwshılarǵa hawa-rayı maǵlıwmatların jetkezip beretuǵın xızmet: Django REST API + OpenWeather integraciyası hám Telegram bot arqalı paydalanıw.
 Joybar jergilikli JSON kartası (Vilayat → qala hám rayonlar kórsetilgen), paydalanıwshı profili (region/city saqlaw), hám cache (sońǵı 30 min) mexanizmin óz ishine aladı.

-------------Tiykarǵı múmkinshilikler-------------

Paydalanıwshılar dizimnen ótedi (JWT menen).

Profilge vilayat hám qala yamasa rayonlar saqlaw imkaniyatları berilgen.

/weather/{city} arqalı hawa-rayı sorawı cache: 30 min dan.

OpenWeather API menen maǵlıwmat alıw.

Telegram bot: /start, /setcity, /weather buyrıqları.

JSON mapping arqalı túrli jazılıwlardı normalizatsiya qılıw (nokis/Nukus/Nókis hám t.b.).

-------------Arxitektura qısqasha -------------

Django (REST API — Django REST Framework)

PostgreSQL (production / AlwaysData)

OpenWeather — sırtqı hawa rayı API

Telegram Bot — webhook (usınıs) yamasa long-polling

Jergilikli JSON — region/city mapping (static/json/...) yamasa template context

-------------Texnologiyalar-------------

asgiref==3.11.0
Django==4.2.26
djangorestframework==3.16.1
djangorestframework_simplejwt==5.5.1
python-dotenv
PyJWT==2.10.1
sqlparse==0.5.3
typing_extensions==4.15.0
tzdata==2025.2
psycopg2-binary
requests

------------- Zárúrli fayllar -------------

requirements.txt — Joybarǵa kerekli paketler

.env — Jasırın sazlamalar

static/json/regions_lot.json — viloyat hám qala yamasa rayonlar mapping (fallback)

telegram_bot.py — Eger Polling paydalanıw arqalı

yourapp/views.py — webhook endpoint / API view

------------- .env -------------
DEBUG=False
SECRET_KEY=put_a_secret_here

# Web (Allowed hosts)
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,rozumbetov.alwaysdata.net

# Django API base
DJANGO_API_BASE=https://rozumbetov.alwaysdata.net

# OpenWeather
OPENWEATHER_API_KEY=YOUR_OPENWEATHER_KEY

# Telegram
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

# Bot <-> Django (eger kerek bolsa)
BOT_SERVICE_TOKEN=optional_bot_service_token

# Postgres (AlwaysData)
DB_NAME=name
DB_USER=user
DB_PASSWORD=password
DB_HOST=postgresql-user.alwaysdata.net
DB_PORT=5432



------------- Lokal ornatıw jolı (development) ------------- 

Repo klonlaw jolı:

git clone https://github.com/RozumbetovBabur/weatheraBaburDeveloper.git
cd weatheraBaburDeveloper papkage kiriw kerek


Virtualenv yaǵni venv jaratıwlıw kerek hám aktivlestiriw kerek:

python3 -m venv venv
source venv/bin/activate


------------- Paketlerdi ornatıw: ------------- 

pip install -r requirements.txt


.env Fayldı joybar túbirinde jaratıw (joqarıdaǵı mısalda kórsetilgen).

------------- Migrate hám collectstatic ------------- :

python manage.py migrate
python manage.py collectstatic


Superuser jaratıw:

python manage.py createsuperuser


serverdi iske tusiriw:

python manage.py runserver
# Browser: http://127.0.0.1:8000/


--------------------------------------------------------------

REST API — endpointları (mısal)

API bazası: DJANGO_API_BASE (máselen https://rozumbetov.alwaysdata.net)

Method	Endpoint	Desctiption
POST	/auth/register	Paydalanıwshı dizimnen ótedi. (JSON)
POST	/auth/login	JWT token menen kiredi.
POST	/users/city	Paydalanıwshı ózi jasap turǵan Vilayat hám qala yamasa rayondi saylaydi (token menen).
GET	/weather/{city} yamasa /weather?city=...	Belgilengen qala yamasa rayon boyınsha hawa-rayı maǵlıwmatın qaytaradı (cache  qollanıladı).

Dizimnen ótkende
curl -X POST https://rozumbetov.alwaysdata.net/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser",
    "email":"test@example.com",
    "password":"password123",
    "password2":"password123",
    "region":"Qaraqalpaqıstan Respublikası",
    "city":"Nókis qalası"
  }'

------------- Login (JWT olıw jolı) ------------- 
curl -X POST https://rozumbetov.alwaysdata.net/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'


Juwapda kiriw-token hám refresh-token tokenleri payda boladı.

------------- Profilge city saqlaw ------------- 
curl -X POST https://rozumbetov.alwaysdata.net/users/city \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"city":"Nókis qalası","region":"Qaraqalpaqıston Respublikası"}'

------------- Hawa-rayı sorawı (lat/lon arqalı city menen) ------------- 
curl "https://rozumbetov.alwaysdata.net/weather?city=Nukus%20shahar"
# yamasa
curl "https://rozumbetov.alwaysdata.net/weather?lat=41.2995&lon=69.2401"

------------- Qollap-Quwatlaw / test etiw -------------

Postman járdeminde joqarıdaǵı sorawlardı jiberiń (headers: Content-Type: application/json).

telegram_bot.py sazlań hám iske tusiriń python telegram_bot.py Telegramǵa /start, - faydalanıwshı baslaydı /setcity Nókis - qalası saqlaydı, /weather Kegeyli - hawa rayı haqqında malıwmat keledi.

Egerde OpenWeather maǵlıwmat kelmese — .env degi OPENWEATHER_API_KEY di tekseriń.

------------- Qanday hújjetler hám kod úlgileri README-ǵe kiritilgen ------------- 

Joybardıń maqseti hám qásiyetleri.

Lokal yamasa server menen deploy qádemleri kórsetilgen.

.env hám security eskertilgen.

API endpointlar menen Postman / curl mısallar kórsetilgen.

Telegram bot ushın long-polling usınısları.

