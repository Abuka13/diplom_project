
from django.core.paginator import Paginator, Page
from django.core.cache import caches
from django.http import HttpRequest

DatabaseCache = caches["database"]
cache = caches["default"]
ram_cache = caches["ram_cache"]


class CustomCache:
    """Кеширование данных."""

    # without cache
    # 1 - NEWS - 0.1s == 1 * 0.1s
    # 1000 * 0.1s == 100s
    # 1 000 000 * 0.1s == 100 000s

    # with cache (1s)
    # 1 - NEWS - 0.1s == 1 * 0.1s
    # 1000 / 1s * 0.001s(RAM) == 1s
    # 1 000 000 / 1s * 0.001s(RAM) == 100s

    # with cache (10s)
    # 1 - NEWS - 0.1s == 1 * 0.1s
    # 1000 / 10s * 0.001s(RAM vs BD) == 0.1s
    # 1 000 000 / 10s * 0.001s(RAM) == 100s

    # name = cache.get("books ratings_top")  # data | None
    # if name is None:
    #     name = f"Arman {random.randint(1, 1000)} (новая)"
    #     cache.set("books ratings_top", name, timeout=20)
    # else:
    #     name += " (из кэша)"

    # LRU cache - выкидывает сначала наименее используемые данные
    # data = {
    #     "key":"books ratings_top",
    #     "data": f"Arman {random.randint(1, 1000)} ({datetime})",
    #     "expired": datetime.datetime.now() + datetime.timedelta(hours=1)
    # }
    # time killer

    @staticmethod
    def caching(key: str, lambda_func: callable, timeout: int = 1) -> any:
        """Попытка взять или записать кэш."""

        data = cache.get(key)
        if data is None:
            data = lambda_func()
            cache.set(key, data, timeout=timeout)
        return data

    @staticmethod
    def clear_cache(key: str) -> any:
        """Очистка кэша."""

        cache.set(key, None, timeout=1)

    @staticmethod
    def set_cache(key: str, data: any, timeout: int = 1):
        """."""

        cache.set(key, data, timeout=timeout)


