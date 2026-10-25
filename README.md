# RU AdList + EasyList mirror

Публичное зеркало списков фильтров в формате Adblock Plus, в том числе для совместимых блокировщиков в TV Bro.

## Единый список RU AdList + EasyList

Основная ссылка для подписки:

```text
https://raw.githubusercontent.com/Detsle/ruadlist-bitblock-fanboys-general-mirror/main/ruadlist+easylist.txt
```

[Открыть основной фильтр](https://raw.githubusercontent.com/Detsle/ruadlist-bitblock-fanboys-general-mirror/main/ruadlist%2Beasylist.txt)

Альтернативная ссылка через jsDelivr:

```text
https://cdn.jsdelivr.net/gh/Detsle/ruadlist-bitblock-fanboys-general-mirror@main/ruadlist+easylist.txt
```

## BitBlock

BitBlock публикуется отдельно:

```text
https://raw.githubusercontent.com/Detsle/ruadlist-bitblock-fanboys-general-mirror/main/bitblock.txt
```

## Обновление

- Основной объединённый список скачивается **только из официального источника RU AdList + EasyList**. Advblock больше не используется как резервный источник и не участвует в резервной сборке.
- Если официальный объединённый список недоступен или не проходит проверку, сохраняется предыдущая рабочая копия. Скрипт не собирает замену из отдельных списков.
- GitHub Actions проверяет и обновляет зеркала ежедневно в 23:17 UTC, а также при изменении updater/workflow и по ручному запуску.
- В заголовке официального объединённого списка указана периодичность обновления 1 день, но у издателя не обнаружено фиксированного публичного времени публикации. Поэтому зеркало проверяет источник раз в сутки ближе к концу дня UTC; фактическая задержка зависит от времени выхода новой версии и задержки GitHub Actions.
- Перед заменой проверяются формат Adblock Plus, размер, число строк и метаданные. Если проверка не проходит, старая копия остаётся на месте.
- BitBlock обновляется в рамках того же ежедневного запуска. При ошибке источника используется его зеркало на GitHub.

Расписание GitHub Actions может выполняться с задержкой. Доступность raw.githubusercontent.com и jsDelivr зависит от сети и провайдера; проверь ссылку непосредственно на устройстве с TV Bro.

## Источники

- [Официальный объединённый RU AdList + EasyList](https://easylist-downloads.adblockplus.org/ruadlist%2Beasylist.txt)
- [Официальный BitBlock](https://easylist-downloads.adblockplus.org/bitblock.txt)

Это независимое зеркало; оно не является официальным проектом EasyList или RU AdList.
