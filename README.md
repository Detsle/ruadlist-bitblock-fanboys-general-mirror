# RU AdList + EasyList mirror

Публичное зеркало фильтров для совместимых блокировщиков рекламы, в том числе TV Bro.

## Единый список RU AdList + EasyList

Основной URL для подписки:

```text
https://raw.githubusercontent.com/Detsle/ruadlist-bitblock-fanboys-general-mirror/main/ruadlist+easylist.txt
```

[Открыть фильтр](https://raw.githubusercontent.com/Detsle/ruadlist-bitblock-fanboys-general-mirror/main/ruadlist+easylist.txt)

Альтернативный CDN URL (jsDelivr):

```text
https://cdn.jsdelivr.net/gh/Detsle/ruadlist-bitblock-fanboys-general-mirror@main/ruadlist+easylist.txt
```

## Как работает обновление

- GitHub Actions запускает обновление каждые 6 часов и также поддерживает ручной запуск.
- Сначала скачивается официальный объединённый список EasyList: `ruadlist+easylist.txt`.
- Если он недоступен или не проходит проверку, скрипт пытается получить EasyList и RU AdList отдельно и собирает объединённый список, удаляя только точные дубликаты строк.
- Проверяются заголовок Adblock Plus, метаданные, размер, количество строк и дата обновления. Если новая версия не проходит проверку, прежний файл сохраняется.
- Существующее зеркало BitBlock по пути `main/bitblock.txt` продолжает обновляться тем же workflow.

Расписание GitHub Actions может выполняться с задержкой. Доступность raw.githubusercontent.com и jsDelivr зависит от сети и провайдера; проверьте URL непосредственно на устройстве, где используется TV Bro.

## Исходники

- [Официальный объединённый RU AdList + EasyList](https://easylist-downloads.adblockplus.org/ruadlist+easylist.txt)
- [EasyList](https://easylist.to/easylist/easylist.txt)
- [RU AdList / advblock](https://easylist-downloads.adblockplus.org/advblock.txt)
- [BitBlock](https://easylist-downloads.adblockplus.org/bitblock.txt)

Это независимое зеркало; оно не является официальным проектом EasyList или RU AdList.
