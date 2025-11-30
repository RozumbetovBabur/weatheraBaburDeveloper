from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import RegisterSerializer, TokenSerializer, UserSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WeatherCache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

User = get_user_model()

@login_required(login_url=settings.LOGIN_URL)
def dashboard_view(request):
    """
    Paydalanıwshı sessiyaǵa iye bolsa dashboardi Render etedi.
    Dashboard shablonı: templates/dashboard.html
    """
    return render(request, 'dashboard.html')

@login_required(login_url=settings.LOGIN_URL)
def home_page(request):
    return render(request, "dashboard.html")

# Profil API: bul AJAX shaqırıwları bolsa da login kerek boladı
@login_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET"])
# @csrf_exempt
def profile_details(request):
    user = request.user
    return JsonResponse({
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "region": user.region,
        "city": user.city,
    })
@login_required(login_url=settings.LOGIN_URL)
@require_http_methods(["POST"])
# @csrf_exempt
def profile_update(request):
    user = request.user
    data = json.loads(request.body)

    user.email = data.get("email", user.email)
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.region = data.get("region", user.region)
    user.city = data.get("city", user.city)

    # Parolni yangilash
    if data.get("password"):
        user.set_password(data["password"])

    user.save()

    return JsonResponse({"message": "Profil tabıslı turde jańalandı!"})

def token_login_page(request):
    """
    GET: token kiriw betin kórsetedi (templates/auth/token_login.html)
    POST: body: {'token': '<access_token>'} di tekseredi.
    Eger token haqıyqıy bolsa-paydalanıwdı login etedi hám /dashboard ǵa jiberedi.
    """

    if request.method == 'GET':
        return render(request, 'auth/token_login.html')

    # POST
    token = request.POST.get('token', '').strip()
    if not token:
        messages.error(request, "Iltimas júzimen kirgiziń.")
        return render(request, 'auth/token_login.html')

    try:
        # AccessToken(token) tokenni dekodlaydı Hám qoldı da tekseredi.
        at = AccessToken(token)
        user_id = at.get('user_id')
        if not user_id:
            messages.error(request, "Token ishinde user_id tabılmadı.")
            return render(request, 'auth/token_login.html')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            messages.error(request, "Júzimendagi paydalanıw tabılmadı.")
            return render(request, 'auth/token_login.html')

        # Session payda etiw (Django login)
        login(request, user)
        # Tabıslı -> dashboard
        return redirect('dashboard')

    except (TokenError, InvalidToken) as e:
        messages.error(request, "Token nadurıs yamasa múddeti ótken.")
        return render(request, 'auth/token_login.html')
    except Exception:
        messages.error(request, "Tokendi tekseriwde qátelik júz berdi.")
        return render(request, 'auth/token_login.html')

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]  # POST ushın JSON juwap beredi
    parser_classes = [JSONParser]

    def get(self, request):
        # templates/auth/register.html Jaylasqan bolıwı kerek
        return render(request, 'auth/register.html')

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # token jaratıw
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "token": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    # Browsable API ni óshirip tek JSON juwap beremiz (POST ushın)
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    def get(self, request):
        """
        GET soraw bolsa, login betin Render etedi.
        templates/auth/login.html jaylasqan bolıwı kerek.
        """
        return render(request, 'auth/login.html')

    def post(self, request):
        """
        POST soraw bolsa-JSON maǵlıwmat (username, parol) kútedi hám token qaytaradı.
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"detail": "username hám password kiritiliwi shárt."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "token": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_200_OK)

        return Response({"detail": "username yamasa parol nadurıs"},
                        status=status.HTTP_401_UNAUTHORIZED)


class CityListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import json, os
        from django.conf import settings
        # JSON faylni o‘qish
        path = os.path.join(settings.BASE_DIR, 'static/json/regions.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Response(data)


class WeatherView(APIView):
    # Kópshilik ushın ruxsat-frontend paydalanıwshıları token jiberiwinde isleydi
    permission_classes = [permissions.AllowAny]
    # Eger siz qáleseńiz, authentication_classes di qoyıwıńız múmkin,
    # Bıraq anonim GETler ushın ol talap islenmeydi.
    CACHE_TTL = timedelta(minutes=30)

    # Simple rate limit: Bir IP ushın WINDOW sekund ishinde MAX_REQ den aspasa boladi
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_MAX = 60     # requests per WINDOW

    def _get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _rate_limited(self, request):
        ip = self._get_client_ip(request) or 'anon'
        key = f"weather_rl_{ip}"
        cnt = cache.get(key, 0)
        if cnt >= self.RATE_LIMIT_MAX:
            return True
        # increment with expiry = window
        cache.incr(key) if cache.get(key) is not None else cache.set(key, 1, self.RATE_LIMIT_WINDOW)
        return False

    def get(self, request):
        # Rate-limit check
        try:
            if self._rate_limited(request):
                return Response({"detail": "Júdá kóp sorawlar, Iltimas azmaz kútiń."},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception:
            # Eger cache backend incr/set menen uyqas kelmese, dawam etiwine ruxsat beremiz
            pass

        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        city = request.query_params.get('city')

        if lat and lon:
            city_key = f"lat:{lat},lon:{lon}"
            params_remote = {'lat': lat, 'lon': lon}
        elif city:
            city_key = city.strip()
            params_remote = {'q': city_key}
        else:
            return Response({"detail": "lat/lon yamasa qala param talap qılınadı."},
                            status=status.HTTP_400_BAD_REQUEST)

        units = request.query_params.get('units', 'metric')

        # cache tekshiruv
        cutoff = timezone.now() - self.CACHE_TTL
        cached = WeatherCache.objects.filter(city_key=city_key, created_at__gte=cutoff).order_by('-created_at').first()
        if cached:
            # DRF Response datetime ni serializatsiyalashi kerak (yoki str ga o'zgartiring)
            return Response({"source": "cache", "cached_at": cached.created_at, "data": cached.data})

        api_key = getattr(settings, 'OPENWEATHER_API_KEY', None)
        if not api_key:
            return Response({"detail": "OpenWeather API gilt sazlanbaǵan."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {**params_remote, "appid": api_key, "units": units, "lang": "uz"}

        try:
            resp = requests.get(url, params=params, timeout=10)
        except requests.RequestException as e:
            return Response({"detail": "Sırtqı API qátesi.", "error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        if resp.status_code != 200:
            try:
                error_json = resp.json()
            except Exception:
                error_json = {"detail": "OpenWeather Juwabı qáte", "status_code": resp.status_code}
            return Response({"source": "remote", "status_code": resp.status_code, "error": error_json},
                            status=resp.status_code)

        data = resp.json()
        # save cache
        try:
            WeatherCache.objects.create(city_key=city_key, data=data)
        except Exception:
            # Eger saqlawda qáte bolsa da juwap qaytarsin
            pass

        return Response({"source": "remote", "data": data})



@login_required(login_url=settings.LOGIN_URL)
@csrf_protect
def user_logout(request):
    """
    Paydalanıwshını qawipsiz shıǵarıw:
    -DRF token (eger ámeldegi bolsa) óshiriledi
    -SımpleJWT (eger blacklist bolsa) ushın OutstandingToken óshiriledi
    -Server cache ishindegi paydalanıw ǵa tiyisli giltlerdi óshiriledi
    -Session flush etiledi, cookie'ler óshiriledi, redirect etiledi
    """
    user = request.user
    request.session.flush()
    logout(request)
    response = redirect('token_login')  # Yamasa 'login' ǵa ózgertiriń
    response.delete_cookie('sessionid')
    response.delete_cookie('access')
    response.delete_cookie('refresh')

    # 1) Eger DRF TokenAuthentication paydalanılsa - serverdegi token obektin óshiriw
    try:
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user=user).delete()
    except Exception:
        # drf.authtoken Joq bolsa da dawam etedi
        pass

    # 2) Eger SimpleJWT + blacklist Paydalanılsa-OutstandingTokenlaerdi  óshiriw / blacklisting
    # (Esletpe: eger siz refresh tokendi jiberseńiz, onı blacklist qılıw maqul)
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        # Barlıq outstanding tokenlerdi óshiriw (eger blacklist app ornatılǵan bolsa)
        outs = OutstandingToken.objects.filter(user=user)
        for ot in outs:
            try:
                BlacklistedToken.objects.get_or_create(token=ot)
            except Exception:
                pass
            # optional: ot.delete()
    except Exception:
        pass

    # 3) Cache ishindegi paydalanıwshıǵa oid giltlerdi óshiriw (mısal)
    # Bul jerge siz joybarngizdagi user-ge oid cache giltlerin jazıń
    try:
        cache.delete(f"user_profile_{user.id}")
        cache.delete(f"user_permissions_{user.id}")
        cache.delete(f"user_{user.username}_data")
    except Exception:
        pass

    # 4) Sessiyanı pútkilley tazalaw
    request.session.flush()      # Session data  hám cookie id ni jańalaydı
    logout(request)              # django.contrib.auth.logout Shaqırıladı (sessionni tamamlaydı)

    # 5) Juwap hám cookie óshiriw (sessionid hám múmkin bolǵan access/refresh cookie'leri)
    response = redirect('home')  # Ózgertiriń: 'home'-> sizdiń tiykarǵı betńiz yamasa login beti
    response.delete_cookie('sessionid')
    response.delete_cookie('access')   # Eger siz access júzimen aspazie retinde saqlaǵan bolsańız
    response.delete_cookie('refresh')  # Eger refresh cookie bolsa

    return response


