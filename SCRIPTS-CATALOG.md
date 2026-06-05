# Каталог переносимых скриптов (для работы на другом компьютере)

> Этот файл — **самодостаточный архив**. Код каждого скрипта вшит прямо сюда,
> поэтому на новой машине, где нет восьми исходных проектов из
> `_MY_PROGRAMMING_4`, ничего догружать не нужно: открыл этот `.md` — и весь
> переиспользуемый код перед глазами.
>
> Отобрано из 9 проектов. Для каждого скрипта: **что это**, **моя оценка**
> (стоит ли тащить в новый KDP-проект и в каком виде) и **сам код**.
>
> Аналогия из живописи: это не готовая картина, а **ящик с уже размятыми
> красками и проверенными кистями**. Холст (новый проект) ты грунтуешь заново,
> но краски смешивать с нуля не придётся.

## Краткая карта (что брать в первую очередь)

| Скрипт | Язык | Ценность | Брать как |
|--------|------|----------|-----------|
| `llm_client.py` | Python | ⭐⭐⭐ | почти без правок — ядро генерации текста |
| `data-reader.js` | JS | ⭐⭐⭐ | портировать логику на Python (pandas/openpyxl) |
| `title-generator.js` | JS | ⭐⭐ | как образец шаблонного движка названий |
| `cover-generator.js` | JS | ⭐⭐ | как образец; в проекте обложки делаем на Pillow |
| `title_blurb_orchestrator.py` | Python | ⭐⭐ | паттерн «A/B/C генерят → судья выбирает» |
| `agents.py` | Python | ⭐ | каркас Generator→Judge→Refiner (контент — заглушка) |
| `recorder.js` / `player.js` | JS (Playwright) | ⚠️ | **НЕ запускать против KDP** — см. красную рамку |

---

## 1. `llm_client.py` — модель-агностичный клиент LLM  ⭐⭐⭐

**Откуда:** `DB-WRITING-SYSTEM/scripts/utils/llm_client.py`

**Что это.** Единый класс `LLMClient`, который умеет звать OpenAI, Anthropic,
Google Gemini, DeepSeek, OpenRouter и локальную Ollama — через один и тот же
метод `.call(system_prompt, user_message)`. Провайдер и модель берутся из
`config/models.yaml` по «роли» (orchestrator / generator / critic / writer …).
Поддерживает историю диалога (список сообщений), подстановку переменных в
шаблон промпта (`call_with_template`) и читает ключи из `.env`.

**Моя оценка.** Самый ценный кусок из всех проектов. Для KDP-конвейера именно
он будет генерировать названия по формуле, HTML-описания и backend-ключи.
Берётся почти без правок: достаточно завести `config/models.yaml` и положить
ключ в `.env`. Один нюанс — для Ollama (локальная бесплатная модель) ключ не
нужен, и это ровно тот «бесплатный заменитель», о котором мы договаривались в
PROJECT-OVERVIEW. То есть один файл закрывает и платный (Claude API), и
бесплатный (Ollama) путь генерации текста.

**Что доработать.** Для Anthropic тут самописный REST через `requests`; можно
заменить на официальный `anthropic` SDK, но и текущий вариант рабочий.

```python
"""
llm_client.py — Универсальный клиент для LLM API.

Поддерживает OpenAI-совместимый формат для всех провайдеров:
OpenAI, Anthropic (через совместимый прокси), Google, DeepSeek, Ollama.
"""

import os
import yaml
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).parent.parent.parent

# Загрузка переменных окружения из .env (если не загружены ранее)
try:
    from dotenv import load_dotenv
    dotenv_path = ROOT_DIR / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
except ImportError:
    pass  # python-dotenv не обязателен


class LLMClient:
    """Модель-агностичный клиент для вызова LLM."""

    def __init__(self, role: str, config_path: Optional[str] = None):
        """
        Args:
            role: роль агента (orchestrator, generator, critic, writer, editor, proofreader, finalizer)
            config_path: путь к config/models.yaml (по умолчанию — из корня проекта)
        """
        self.role = role
        config_file = config_path or str(ROOT_DIR / "config" / "models.yaml")
        self.config = self._load_config(config_file)
        self.model_config = self._get_model_config()

    def _load_config(self, config_file: str) -> dict:
        with open(config_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_model_config(self) -> dict:
        mode = self.config.get("mode", "orchestra")
        provider = self.config.get("provider", "openrouter")

        # Настройки провайдера (api_base, api_key_env)
        PROVIDER_SETTINGS = {
            "openrouter": {
                "api_base": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
            },
            "ollama": {
                "api_base": "http://localhost:11434/v1",
                "api_key_env": "",
            },
        }

        base_config = {
            "provider": provider,
            "temperature": 0.7,
            "max_tokens": 4096,
            **PROVIDER_SETTINGS.get(provider, {}),
        }

        if mode == "orchestra":
            orchestra = self.config.get("orchestra", {})
            model = orchestra.get("model", "") if isinstance(orchestra, dict) else ""
            return {**base_config, "model": model}

        elif mode == "multi-agent":
            agents = self.config.get("agents", {})
            model = agents.get(self.role, "")
            if not model:
                # Fallback: если роль не найдена в agents, берём orchestra модель
                orchestra = self.config.get("orchestra", {})
                model = orchestra.get("model", "") if isinstance(orchestra, dict) else ""
            return {**base_config, "model": model}

        # Обратная совместимость со старым форматом (simple/advanced)
        elif mode == "simple":
            return self.config.get("simple", base_config)
        elif mode == "advanced":
            advanced = self.config.get("advanced", {})
            if self.role in advanced:
                return advanced[self.role]
            return self.config.get("simple", base_config)

        raise ValueError(f"Неизвестный режим: {mode}")

    def _get_api_key(self) -> str:
        key_env = self.model_config.get("api_key_env", "")
        if not key_env:
            return ""
        api_key = os.environ.get(key_env, "")
        if not api_key:
            print(f"[WARNING] Переменная окружения '{key_env}' не задана")
        return api_key

    def call(self, system_prompt: str, user_message) -> str:
        """
        Вызывает LLM с заданными промптами.

        Args:
            system_prompt: системный промпт (роль и инструкции)
            user_message: пользовательское сообщение (str) или список сообщений (list[dict])
                         для поддержки истории диалога

        Returns:
            Ответ модели в виде строки
        """
        provider = self.model_config.get("provider", "openai").lower()
        model = self.model_config.get("model", "gpt-4o")
        temperature = self.model_config.get("temperature", 0.7)
        max_tokens = self.model_config.get("max_tokens", 4096)
        api_key = self._get_api_key()
        api_base = self.model_config.get("api_base", "")

        print(f"[LLM] [{self.role}] {provider}/{model} (temperature={temperature})")

        if not api_key and provider != "ollama":
            return f"[ERROR] Ошибка: API ключ для {provider} не задан."

        try:
            if provider in ["openai", "deepseek", "openrouter", "ollama"]:
                import openai
                
                client_kwargs = {"api_key": api_key or "dummy"}
                if api_base:
                    client_kwargs["base_url"] = api_base
                elif provider == "deepseek":
                    client_kwargs["base_url"] = "https://api.deepseek.com/v1"
                elif provider == "openrouter":
                    client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
                elif provider == "ollama":
                    client_kwargs["base_url"] = "http://localhost:11434/v1"

                client = openai.OpenAI(**client_kwargs)
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # Поддержка истории диалога (список сообщений)
                if isinstance(user_message, list):
                    messages.extend(user_message)
                else:
                    messages.append({"role": "user", "content": user_message})

                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content

            elif provider == "anthropic":
                import requests
                
                url = api_base or "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                
                # Для Anthropic преобразуем список сообщений если нужно
                if isinstance(user_message, list):
                    # Берём только user сообщения для Anthropic (упрощённо)
                    anthropic_messages = []
                    for msg in user_message:
                        if msg.get("role") in ["user", "assistant"]:
                            anthropic_messages.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                else:
                    anthropic_messages = [{"role": "user", "content": user_message}]
                
                data = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": anthropic_messages
                }
                if system_prompt:
                    data["system"] = system_prompt

                resp = requests.post(url, headers=headers, json=data)
                resp.raise_for_status()
                return resp.json()["content"][0]["text"]

            elif provider == "google":
                import requests
                
                # Google Gemini API via REST
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                
                # Для Gemini собираем контент
                if isinstance(user_message, list):
                    # Преобразуем историю в contents
                    contents = []
                    for msg in user_message:
                        role = "user" if msg.get("role") == "user" else "model"
                        contents.append({
                            "role": role,
                            "parts": [{"text": msg.get("content", "")}]
                        })
                else:
                    contents = [{"role": "user", "parts": [{"text": user_message}]}]
                
                data = {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                    }
                }
                if system_prompt:
                    data["systemInstruction"] = {"parts": [{"text": system_prompt}]}

                resp = requests.post(url, headers=headers, json=data)
                resp.raise_for_status()
                
                result = resp.json()
                try:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return f"[ERROR] Ошибка парсинга ответа Google: {result}"

            else:
                return f"[ERROR] Ошибка: Провайдер {provider} не поддерживается."

        except Exception as e:
            return f"[ERROR] Ошибка вызова API ({provider}): {str(e)}"

    def generate(self, user_message: str, system_prompt: str = "", max_tokens: int = None) -> str:
        """
        Упрощённый метод генерации (для обратной совместимости).
        
        Args:
            user_message: сообщение пользователя
            system_prompt: системный промпт (опционально)
            max_tokens: максимальное количество токенов (опционально)
            
        Returns:
            Ответ модели
        """
        # Временно переопределяем max_tokens если задан
        original_max = self.model_config.get("max_tokens")
        if max_tokens:
            self.model_config["max_tokens"] = max_tokens
        try:
            result = self.call(system_prompt=system_prompt, user_message=user_message)
        finally:
            # Восстанавливаем оригинальное значение
            if max_tokens and original_max:
                self.model_config["max_tokens"] = original_max
        return result

    def call_with_template(self, template_path: str, variables: dict) -> str:
        """
        Загружает промпт из файла-шаблона, подставляет переменные и вызывает LLM.

        Args:
            template_path: путь к файлу промпта (относительно корня проекта)
            variables: словарь переменных для подстановки в шаблон

        Returns:
            Ответ модели
        """
        template_file = ROOT_DIR / template_path
        if not template_file.exists():
            raise FileNotFoundError(f"Шаблон промпта не найден: {template_file}")

        template = template_file.read_text(encoding="utf-8")

        # Простая подстановка {variable_name}
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))

        return self.call(system_prompt="", user_message=template)
```

---

## 2. `data-reader.js` — чтение и валидация книг (Excel/JSON)  ⭐⭐⭐

**Откуда:** `KDP-FORM-AUTOMATION/utils/data-reader.js`

**Что это.** Читает список книг из `.xlsx`/`.xls`/`.json`, маппит колонки
таблицы в поля книги (title, subtitle, description, keywords, price, isbn,
page_count …) и **валидирует**: обязательные поля, формат ISBN, положительная
цена и — важное для KDP — **не больше 7 ключевых слов**.

**Моя оценка.** Логика прямо ложится на наш `published.csv`/паспорт ниши.
Сам JS тащить не обязательно (проект на Python), но **алгоритм валидации
переносим один-в-один** на `pandas`/`openpyxl`: проверка 7 ключей, обязательных
полей и цены — это ровно те предохранители, что защищают от мусорной загрузки
в KDP. Считай это спецификацией валидатора, написанной на JS.

```javascript
const XLSX = require('xlsx');
const fs = require('fs-extra');
const path = require('path');
const logger = require('./logger');

class DataReader {
  constructor() {
    this.supportedFormats = ['.xlsx', '.xls', '.json'];
  }

  async readBooks(filePath) {
    try {
      const ext = path.extname(filePath).toLowerCase();
      
      if (!this.supportedFormats.includes(ext)) {
        throw new Error(`Неподдерживаемый формат файла: ${ext}`);
      }

      let data;
      switch (ext) {
        case '.json':
          data = await this.readJSON(filePath);
          break;
        case '.xlsx':
        case '.xls':
          data = await this.readExcel(filePath);
          break;
        default:
          throw new Error(`Формат ${ext} не поддерживается`);
      }

      logger.info(`Прочитано ${data.length} книг из ${filePath}`);
      return data;

    } catch (error) {
      logger.error(`Ошибка чтения файла ${filePath}`, { error: error.message });
      throw error;
    }
  }

  async readJSON(filePath) {
    const rawData = await fs.readJson(filePath);
    
    // Если это одна книга, оборачиваем в массив
    if (!Array.isArray(rawData)) {
      return [rawData];
    }
    
    return rawData;
  }

  async readExcel(filePath) {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    // Читаем данные как JSON
    const rawData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
    
    // Пропускаем заголовок и преобразуем в нужный формат
    const headers = rawData[0];
    const books = [];
    
    for (let i = 1; i < rawData.length; i++) {
      const row = rawData[i];
      if (row.length === 0 || row.every(cell => !cell)) continue; // Пропускаем пустые строки
      
      const book = this.excelRowToBook(headers, row);
      books.push(book);
    }
    
    return books;
  }

  excelRowToBook(headers, row) {
    const book = {};
    
    // Маппинг колонок Excel в поля книги
    const fieldMapping = {
      'title': 'title',
      'subtitle': 'subtitle',
      'description': 'description',
      'keywords': 'keywords',
      'author': 'author',
      'publisher': 'publisher',
      'language': 'language',
      'isbn': 'isbn',
      'price': 'price',
      'main_category': 'mainCategory',
      'sub_category': 'subCategory',
      'file_path': 'filePath',
      'cover_path': 'coverPath',
      'publish_date': 'publishDate',
      'page_count': 'pageCount',
      'word_count': 'wordCount'
    };

    headers.forEach((header, index) => {
      const normalizedHeader = header.toLowerCase().replace(/[^a-z0-9_]/g, '_');
      const fieldName = fieldMapping[normalizedHeader] || normalizedHeader;
      
      let value = row[index];
      
      // Обработка специальных полей
      if (fieldName === 'keywords' && typeof value === 'string') {
        book[fieldName] = value.split(',').map(k => k.trim());
      } else if (fieldName === 'price' && typeof value === 'string') {
        book[fieldName] = {
          currency: 'RUB',
          amount: parseFloat(value.replace(/[^\d.]/g, ''))
        };
      } else if (fieldName === 'publishDate' && typeof value === 'string') {
        book[fieldName] = value;
      } else if (fieldName === 'pageCount' || fieldName === 'wordCount') {
        book[fieldName] = parseInt(value) || 0;
      } else {
        book[fieldName] = value;
      }
    });

    // Добавляем категории если есть
    if (book.mainCategory || book.subCategory) {
      book.categories = [];
      if (book.mainCategory && book.subCategory) {
        book.categories.push({
          main: book.mainCategory,
          sub: book.subCategory
        });
      }
    }

    // Добавляем метаданные
    if (!book.metadata) {
      book.metadata = {};
    }
    if (book.pageCount) book.metadata.pageCount = book.pageCount;
    if (book.wordCount) book.metadata.wordCount = book.wordCount;

    return book;
  }

  async validateBooks(books) {
    const errors = [];
    const warnings = [];
    
    books.forEach((book, index) => {
      const bookNum = index + 1;
      
      // Обязательные поля
      const requiredFields = ['title', 'description', 'author'];
      requiredFields.forEach(field => {
        if (!book[field] || book[field].trim() === '') {
          errors.push(`Книга ${bookNum}: Отсутствует обязательное поле '${field}'`);
        }
      });
      
      // Проверка ISBN
      if (book.isbn && !this.validateISBN(book.isbn)) {
        warnings.push(`Книга ${bookNum}: ISBN может быть некорректным`);
      }
      
      // Проверка цены
      if (book.price && (!book.price.amount || book.price.amount <= 0)) {
        warnings.push(`Книга ${bookNum}: Цена должна быть положительной`);
      }
      
      // Проверка ключевых слов
      if (book.keywords && Array.isArray(book.keywords)) {
        if (book.keywords.length > 7) {
          warnings.push(`Книга ${bookNum}: Слишком много ключевых слов (максимум 7)`);
        }
      }
    });
    
    return { errors, warnings };
  }

  validateISBN(isbn) {
    // Простая валидация ISBN (10 или 13 цифр)
    const cleanISBN = isbn.replace(/[^0-9X]/gi, '');
    return cleanISBN.length === 10 || cleanISBN.length === 13;
  }

  async convertToJSON(inputPath, outputPath) {
    try {
      const books = await this.readBooks(inputPath);
      const { errors, warnings } = await this.validateBooks(books);
      
      if (errors.length > 0) {
        logger.error('Ошибки валидации данных', { errors });
        throw new Error(`Ошибки валидации:\n${errors.join('\n')}`);
      }
      
      if (warnings.length > 0) {
        logger.warn('Предупреждения валидации', { warnings });
        console.log('⚠️  Предупреждения:');
        warnings.forEach(warning => console.log(`  - ${warning}`));
      }
      
      await fs.ensureDir(path.dirname(outputPath));
      await fs.writeJson(outputPath, books, { spaces: 2 });
      
      logger.info(`Данные конвертированы в ${outputPath}`, { 
        booksCount: books.length 
      });
      
      console.log(`✅ Конвертировано ${books.length} книг в ${outputPath}`);
      
    } catch (error) {
      logger.error(`Ошибка конвертации ${inputPath} в ${outputPath}`, { 
        error: error.message 
      });
      throw error;
    }
  }
}

module.exports = DataReader;
```

---

## 3. `title-generator.js` — шаблонный генератор названий/описаний  ⭐⭐

**Откуда:** `AMAZON-NOTEBOOKS-AUTOMATION/src/title-generator.js`

**Что это.** Движок названий на шаблонах: категории (minimalist / creative /
professional), плейсхолдеры `{subject} {style} {purpose} {pages}`, генерация
подзаголовка, описания, набора ключей (срез до 7) и пакетная генерация партии.

**Моя оценка.** Концептуально — это и есть `title_formula` из нашего
`niche.yaml`, только зашитая в код. Брать стоит **как образец паттерна**
«шаблон + словари вариантов + перемешивание», а не дословно: тексты тут
русские и заточены под тетради, а нам нужны англоязычные формулы под нишу.
Но как каркас «формула названия → N валидных вариантов» — полезно. В новом
проекте логичнее, чтобы вариативность давал `llm_client.py` (скрипт №1), а
этот файл держать как простой/офлайновый запасной генератор без LLM.

```javascript
class TitleGenerator {
  constructor() {
    this.templates = {
      minimalist: [
        "{subject} | {style}",
        "{subject} для {purpose}",
        "{subject} | {pages} страниц",
        "Тетрадь {subject} | {style}",
        "{subject} Notebook | {style}"
      ],
      creative: [
        "✨ {subject} для творческих душ",
        "🌟 {subject} | Раскрой свой потенциал",
        "🎨 {subject} для ваших идей",
        "🌈 {subject} | Вдохновение на каждой странице",
        "💫 {subject} для мечтателей"
      ],
      professional: [
        "Профессиональная тетрадь: {subject}",
        "{subject} | Бизнес-формат",
        "Executive {subject} Notebook",
        "{subject} для продуктивности",
        "Premium {subject} | Professional"
      ]
    };

    this.subjects = [
      "для записей", "для идей", "для планов", "для мыслей", "для заметок",
      "для эскизов", "для дневника", "для целей", "для проектов", "для вдохновения",
      "для креативности", "для продуктивности", "для организации", "для обучения"
    ];

    this.styles = [
      "Минималистичный дизайн", "Современный стиль", "Классический дизайн",
      "Элегантный минимализм", "Простой и стильный", "Чистый дизайн"
    ];

    this.purposes = [
      "творчества", "продуктивности", "вдохновения", "планирования", 
      "развития", "обучения", "саморазвития", "креативности"
    ];

    this.keywords = [
      "тетрадь", "записи", "планирование", "идеи", "творчество",
      "продуктивность", "организация", "дневник", "ноутбук", "заметки",
      "минимализм", "стиль", "дизайн", "качество", "профессиональный"
    ];
  }

  generateTitle(category = 'minimalist') {
    const templates = this.templates[category] || this.templates.minimalist;
    const template = templates[Math.floor(Math.random() * templates.length)];
    
    return template
      .replace('{subject}', this.subjects[Math.floor(Math.random() * this.subjects.length)])
      .replace('{style}', this.styles[Math.floor(Math.random() * this.styles.length)])
      .replace('{purpose}', this.purposes[Math.floor(Math.random() * this.purposes.length)])
      .replace('{pages}', Math.floor(Math.random() * 150) + 50); // 50-200 страниц
  }

  generateSubtitle(title) {
    const subtitles = [
      `${Math.floor(Math.random() * 150) + 50} страниц для ваших идей`,
      "Качественная бумать и стильный дизайн",
      "Идеально подходит для повседневных записей",
      "Пространство для ваших мыслей и планов",
      "Создана для продуктивности и вдохновения",
      "Ваш идеальный спутник для креативности",
      "Элегантный дизайн для современных профессионалов"
    ];
    
    return subtitles[Math.floor(Math.random() * subtitles.length)];
  }

  generateDescription(title, subtitle) {
    const descriptions = [
      `Качественная тетрадь с профессиональным дизайном. Идеально подходит для записей, планирования и творческих идей. ${subtitle}`,
      
      `Современная тетрадь, созданная для продуктивности. Страницы из высококачественной бумаги обеспечивают комфортное письмо. ${subtitle}`,
      
      `Стильная тетрадь для повседневного использования. Минималистичный дизайн и практичный формат делают ее идеальным выбором для работы и учебы. ${subtitle}`,
      
      `Профессиональная тетрадь премиум-класса. Разработана для тех, кто ценит качество и функциональность. ${subtitle}`,
      
      `Универсальная тетрадь для всех ваших нужд. Отлично подходит для ведения дневника, планирования и творческих проектов. ${subtitle}`
    ];
    
    return descriptions[Math.floor(Math.random() * descriptions.length)];
  }

  generateKeywords(title, category = 'minimalist') {
    const baseKeywords = this.keywords.slice(0, 7); // Берем первые 7 ключевых слов
    
    // Добавляем специфические ключевые слова в зависимости от категории
    const categoryKeywords = {
      minimalist: ["минимализм", "простой дизайн", "чистый стиль"],
      creative: ["творчество", "вдохновение", "креативность", "арт"],
      professional: ["бизнес", "профессиональный", "продуктивность", "организация"]
    };
    
    const additionalKeywords = categoryKeywords[category] || categoryKeywords.minimalist;
    
    // Комбинируем и перемешиваем
    const allKeywords = [...baseKeywords, ...additionalKeywords];
    return this.shuffleArray(allKeywords).slice(0, 7); // Amazon позволяет максимум 7 ключевых слов
  }

  generateNotebookData(options = {}) {
    const {
      category = 'minimalist',
      customTitle = null,
      pageCount = Math.floor(Math.random() * 150) + 50
    } = options;

    const title = customTitle || this.generateTitle(category);
    const subtitle = this.generateSubtitle(title);
    const description = this.generateDescription(title, subtitle);
    const keywords = this.generateKeywords(title, category);

    return {
      title,
      subtitle,
      description,
      keywords,
      pageCount,
      category,
      createdAt: new Date().toISOString()
    };
  }

  generateBatch(count = 5, category = 'minimalist') {
    const notebooks = [];
    
    for (let i = 0; i < count; i++) {
      notebooks.push(this.generateNotebookData({ category }));
    }
    
    return notebooks;
  }

  shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  // Метод для генерации названий на основе темы
  generateThemedTitles(theme, count = 5) {
    const themeTemplates = {
      business: [
        "Business Planner | {style}",
        "Executive Notebook | {style}",
        "Professional Meeting Notes | {style}",
        "Strategic Planning Journal | {style}",
        "Productivity Tracker | {style}"
      ],
      education: [
        "Study Notes | {style}",
        "Learning Journal | {style}",
        "Academic Planner | {style}",
        "Research Notebook | {style}",
        "Knowledge Tracker | {style}"
      ],
      personal: [
        "Personal Journal | {style}",
        "Daily Reflections | {style}",
        "Life Planner | {style}",
        "Mindfulness Journal | {style}",
        "Goal Setting Notebook | {style}"
      ],
      creative: [
        "Creative Ideas Journal | {style}",
        "Art Sketchbook | {style}",
        "Design Concepts | {style}",
        "Inspiration Notebook | {style}",
        "Brainstorming Journal | {style}"
      ]
    };

    const templates = themeTemplates[theme] || themeTemplates.personal;
    const titles = [];

    for (let i = 0; i < count; i++) {
      const template = templates[Math.floor(Math.random() * templates.length)];
      const style = this.styles[Math.floor(Math.random() * this.styles.length)];
      titles.push(template.replace('{style}', style));
    }

    return titles;
  }
}

// Пример использования
async function main() {
  const generator = new TitleGenerator();
  
  // Генерация одной тетради
  const notebook = generator.generateNotebookData({ category: 'minimalist' });
  console.log('Сгенерированная тетрадь:', notebook);
  
  // Генерация партии тетрадей
  const batch = generator.generateBatch(3, 'creative');
  console.log('\nПартия тетрадей:', batch);
  
  // Тематические названия
  const businessTitles = generator.generateThemedTitles('business', 5);
  console.log('\nБизнес названия:', businessTitles);
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = TitleGenerator;
```

---

## 4. `cover-generator.js` — генератор обложек на canvas  ⭐⭐

**Откуда:** `AMAZON-NOTEBOOKS-AUTOMATION/src/cover-generator.js`

**Что это.** Рисует обложку в трёх стилях (минимализм / цветной градиент /
премиум-тёмный) через библиотеку `canvas`. Заданы **правильные размеры под
KDP 6×9 при 300 DPI** (1414×2175 px заявлено в коде), есть перенос длинного
названия по словам (`wrapText`) и сохранение в PNG.

**Моя оценка.** Полезен в первую очередь **числами и приёмами**: размер холста
под 300 DPI, разбиение заголовка на строки, три композиции. В нашем проекте
обложки делаем на **Pillow (PIL)** — логика тривиально переносится (заливка,
прямоугольники-акценты, текст по центру, перенос строк). Бери как референс
вёрстки обложки, а не как зависимость от node-canvas.

> ⚠️ Мелочь: для реального KDP важно учитывать **bleed и корешок** (зависит от
> числа страниц) — в этом скрипте их нет, это обложка «лицо без корешка».
> При портировании на Pillow заложи поля под bleed.

```javascript
const { createCanvas } = require('canvas');
const fs = require('fs').promises;
const path = require('path');

class CoverGenerator {
  constructor() {
    this.width = 1414; // Стандартный размер для Amazon KDP (6x9 дюймов при 300 DPI)
    this.height = 2175;
  }

  async generateMinimalistCover(title, subtitle = '', author = '') {
    const canvas = createCanvas(this.width, this.height);
    const ctx = canvas.getContext('2d');
    
    // Фон
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, this.width, this.height);
    
    // Акцентная линия
    ctx.fillStyle = '#2c3e50';
    ctx.fillRect(100, 200, this.width - 200, 4);
    
    // Название
    ctx.fillStyle = '#2c3e50';
    ctx.font = 'bold 72px Arial';
    ctx.textAlign = 'center';
    
    // Разбиваем длинное название на строки
    const maxCharsPerLine = 25;
    const titleLines = this.wrapText(title, maxCharsPerLine);
    
    let yPosition = 400;
    titleLines.forEach(line => {
      ctx.fillText(line, this.width / 2, yPosition);
      yPosition += 90;
    });
    
    // Подзаголовок
    if (subtitle) {
      ctx.fillStyle = '#7f8c8d';
      ctx.font = '36px Arial';
      const subtitleLines = this.wrapText(subtitle, 40);
      
      yPosition += 50;
      subtitleLines.forEach(line => {
        ctx.fillText(line, this.width / 2, yPosition);
        yPosition += 50;
      });
    }
    
    // Нижняя акцентная линия
    ctx.fillStyle = '#2c3e50';
    ctx.fillRect(100, this.height - 300, this.width - 200, 4);
    
    // Автор
    if (author) {
      ctx.fillStyle = '#7f8c8d';
      ctx.font = '32px Arial';
      ctx.fillText(author, this.width / 2, this.height - 200);
    }
    
    return canvas;
  }

  async generateColorfulCover(title, subtitle = '', author = '') {
    const canvas = createCanvas(this.width, this.height);
    const ctx = canvas.getContext('2d');
    
    // Градиентный фон
    const gradient = ctx.createLinearGradient(0, 0, this.width, this.height);
    gradient.addColorStop(0, '#667eea');
    gradient.addColorStop(1, '#764ba2');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, this.width, this.height);
    
    // Белый прямоугольник для текста
    ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
    ctx.fillRect(100, 300, this.width - 200, this.height - 600);
    
    // Название
    ctx.fillStyle = '#2c3e50';
    ctx.font = 'bold 72px Arial';
    ctx.textAlign = 'center';
    
    const titleLines = this.wrapText(title, 20);
    let yPosition = 500;
    
    titleLines.forEach(line => {
      ctx.fillText(line, this.width / 2, yPosition);
      yPosition += 90;
    });
    
    // Подзаголовок
    if (subtitle) {
      ctx.fillStyle = '#667eea';
      ctx.font = '36px Arial';
      const subtitleLines = this.wrapText(subtitle, 35);
      
      yPosition += 50;
      subtitleLines.forEach(line => {
        ctx.fillText(line, this.width / 2, yPosition);
        yPosition += 50;
      });
    }
    
    // Декоративный элемент
    ctx.fillStyle = '#667eea';
    ctx.beginPath();
    ctx.arc(this.width / 2, this.height - 400, 50, 0, Math.PI * 2);
    ctx.fill();
    
    // Автор
    if (author) {
      ctx.fillStyle = '#2c3e50';
      ctx.font = '32px Arial';
      ctx.fillText(author, this.width / 2, this.height - 200);
    }
    
    return canvas;
  }

  async generateProfessionalCover(title, subtitle = '', author = '') {
    const canvas = createCanvas(this.width, this.height);
    const ctx = canvas.getContext('2d');
    
    // Темный фон
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, this.width, this.height);
    
    // Золотая акцентная линия
    ctx.fillStyle = '#d4af37';
    ctx.fillRect(100, 200, this.width - 200, 3);
    
    // Название
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 68px Georgia';
    ctx.textAlign = 'center';
    
    const titleLines = this.wrapText(title, 22);
    let yPosition = 400;
    
    titleLines.forEach(line => {
      ctx.fillText(line, this.width / 2, yPosition);
      yPosition += 85;
    });
    
    // Подзаголовок
    if (subtitle) {
      ctx.fillStyle = '#d4af37';
      ctx.font = 'italic 34px Georgia';
      const subtitleLines = this.wrapText(subtitle, 38);
      
      yPosition += 50;
      subtitleLines.forEach(line => {
        ctx.fillText(line, this.width / 2, yPosition);
        yPosition += 48;
      });
    }
    
    // Нижняя акцентная линия
    ctx.fillStyle = '#d4af37';
    ctx.fillRect(100, this.height - 300, this.width - 200, 3);
    
    // Автор
    if (author) {
      ctx.fillStyle = '#ffffff';
      ctx.font = '30px Georgia';
      ctx.fillText(author, this.width / 2, this.height - 200);
    }
    
    return canvas;
  }

  wrapText(text, maxCharsPerLine) {
    if (text.length <= maxCharsPerLine) {
      return [text];
    }
    
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';
    
    for (const word of words) {
      if ((currentLine + ' ' + word).length <= maxCharsPerLine) {
        currentLine = currentLine ? currentLine + ' ' + word : word;
      } else {
        if (currentLine) {
          lines.push(currentLine);
          currentLine = word;
        } else {
          // Слово длиннее максимальной длины
          lines.push(word.substring(0, maxCharsPerLine));
          currentLine = word.substring(maxCharsPerLine);
        }
      }
    }
    
    if (currentLine) {
      lines.push(currentLine);
    }
    
    return lines;
  }

  async saveCover(canvas, filename) {
    const outputPath = path.join(process.cwd(), 'output', 'covers');
    await fs.mkdir(outputPath, { recursive: true });
    
    const fullPath = path.join(outputPath, filename);
    const buffer = canvas.toBuffer('image/png');
    await fs.writeFile(fullPath, buffer);
    
    return fullPath;
  }

  async generateCover(title, options = {}) {
    const {
      subtitle = '',
      author = '',
      style = 'minimalist',
      filename = null
    } = options;

    let canvas;
    
    switch (style) {
      case 'colorful':
        canvas = await this.generateColorfulCover(title, subtitle, author);
        break;
      case 'professional':
        canvas = await this.generateProfessionalCover(title, subtitle, author);
        break;
      case 'minimalist':
      default:
        canvas = await this.generateMinimalistCover(title, subtitle, author);
        break;
    }

    const coverFilename = filename || `${Date.now()}_${style}_cover.png`;
    const coverPath = await this.saveCover(canvas, coverFilename);
    
    return {
      success: true,
      path: coverPath,
      filename: coverFilename,
      style
    };
  }
}

// Пример использования
async function main() {
  const generator = new CoverGenerator();
  
  const result = await generator.generateCover(
    "Тетрадь для творческих идей",
    "Минималистичный дизайн для ваших мыслей",
    "",
    {
      style: 'minimalist'
    }
  );
  
  console.log('Обложка создана:', result);
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = CoverGenerator;
```

---

## 5. `title_blurb_orchestrator.py` — паттерн «A/B/C → судья»  ⭐⭐

**Откуда:** `DOE-ORIGINAL-TITLE/execution/stage2/title_blurb_orchestrator.py`
*(приведена голова файла — ключевые функции парсинга и схема workflow;
остальное — обвязка путей/логов конкретного проекта).*

**Что это.** Workflow генерации пары «product_title + blurb»: три агента
A/B/C порождают по 2 варианта (до 6 пар), затем агент-судья выбирает ровно
одну победившую пару. Ценная часть — **устойчивый парсинг ответа LLM в JSON**
(`parse_pairs_from_text`, `extract_json_array`): снимает ```-обёртки, чинит
кривой JSON, достаёт массив из текста.

**Моя оценка.** Сам оркестратор привязан к чужой структуре проекта, целиком не
переносится. Но **паттерн «несколько генераторов → судья выбирает лучшее»**
идеально ложится на наш Фаза-3: одна ниша → 3 разных названия/обложки/угла.
И функции разбора JSON-ответа модели бери сразу — это та рутина, на которой
обычно спотыкаются, когда LLM возвращает текст вместо чистого JSON.

```python
"""Stage 2 orchestrator: generate and judge Title+Blurb pairs.

Workflow per cover title:
1) A/B/C each generate 2 pairs (product_title + blurb) => up to 6 pairs
2) Judge evaluates the 6 pairs as linked units
3) Exactly one winning pair is selected
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os
import re
import sys
from typing import Any

# Allow direct script execution: python .\execution\stage2\title_blurb_orchestrator.py
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from execution import orchestrator as stage1


CONFIG_PATH = ROOT_DIR / "data" / "config.yaml"
GEN_PROMPTS_PATH = ROOT_DIR / "execution" / "prompts" / "title_blurb_generators.md"
JUDGE_PROMPT_PATH = ROOT_DIR / "execution" / "prompts" / "title_blurb_judge.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def log(message: str) -> None:
    stage1.log(f"[stage2] {message}")


def extract_agent_sections(markdown_text: str) -> tuple[str, dict[str, str]]:
    """Extract global prompt part and A/B/C sections."""
    first_agent = markdown_text.find("## Agent ")
    global_part = markdown_text[:first_agent].strip() if first_agent != -1 else markdown_text.strip()
    sections: dict[str, str] = {}
    pattern = re.compile(r"##\s+Agent\s+([A-Z]).*?\n(.*?)(?=\n---\n\n##\s+Agent\s+[A-Z]|\Z)", re.S)
    for m in pattern.finditer(markdown_text):
        sections[m.group(1).strip()] = m.group(2).strip()
    return global_part, sections


def extract_json_array(text: str) -> list[dict[str, Any]] | None:
    t = text.strip()
    if not t:
        return None
    try:
        parsed = json.loads(t)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    start = t.find("[")
    end = t.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    frag = t[start : end + 1]
    try:
        parsed = json.loads(frag)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        return None
    return None


def parse_pairs_from_text(text: str) -> list[dict[str, Any]]:
    """Parse model output into a list of {product_title, blurb} objects."""
    t = text.strip()
    if not t:
        return []

    # Remove fenced code block wrappers if present.
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t).strip()
        t = re.sub(r"\n?```$", "", t).strip()

    candidates: list[dict[str, Any]] = []

    def collect_from_list(items: list[Any]) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            pt = str(item.get("product_title", "")).strip()
            bl = str(item.get("blurb", "")).strip()
            if pt and bl:
                candidates.append({"product_title": pt, "blurb": bl})

    # 1) Direct JSON parse
    try:
        parsed = json.loads(t)
        if isinstance(parsed, list):
            collect_from_list(parsed)
        elif isinstance(parsed, dict):
            if isinstance(parsed.get("pairs"), list):
                collect_from_list(parsed["pairs"])
            else:
                # Try to find first list value in dict
                for v in parsed.values():
                    if isinstance(v, list):
                        collect_from_list(v)
    except json.JSONDecodeError:
        pass

    if candidates:
        return candidates

    # 2) Fallback to array fragment
    arr = extract_json_array(t)
    if arr:
        collect_from_list(arr)
# … (далее — обвязка путей/логов проекта, опущено: 346 строк)
```

---

## 6. `agents.py` — каркас Generator → Judge → Refiner  ⭐

**Откуда:** `DOE-ORIGINAL-TITLE/multi_agent_system/agents.py`
*(приведена голова — структура классов и dataclass ответа).*

**Что это.** Скелет мультиагентной генерации: `GeneratorAgent`,
`JudgeAgent`, и dataclass `AgentResponse`. Важно: сам контент в `_create_story`
**захардкожен-заглушка** (в реальной системе там вызов LLM).

**Моя оценка.** Берётся **как архитектурный шаблон**, не как рабочий код:
показывает чистое разделение ролей и единый формат ответа агента
(`agent_name / content / feedback / iteration`). В связке с `llm_client.py`
(скрипт №1) заглушку `_create_story` меняешь на реальный `.call(...)` — и
получаешь рабочий цикл «сгенерировал → оценил → улучшил» для названий и
описаний.

```python
"""
Multi-Agent Content Generation System
Система генерации контента: Generator → Judge → Refiner
"""

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentResponse:
    """Структура ответа агента"""
    agent_name: str
    content: str
    feedback: Dict
    timestamp: str
    iteration: int


class GeneratorAgent:
    """
    Агент-генератор: создает первоначальный контент
    """
    
    def __init__(self, name: str = "Generator"):
        self.name = name
        self.system_prompt = """Ты — творческий писатель. Твоя задача — написать историю на заданную тему.
Будь креативным, используй интересные повороты сюжета, живые описания.
Соблюдай лимит слов."""
    
    def generate(self, topic: str, constraints: Dict) -> AgentResponse:
        """Генерация контента"""
        print(f"\n[GEN] [{self.name}] Генерация контента...")
        
        # Симуляция генерации (в реальной системе здесь был бы LLM вызов)
        story = self._create_story(topic, constraints)
        
        word_count = len(story.split())
        print(f"[OK] [{self.name}] Создано {word_count} слов")
        
        return AgentResponse(
            agent_name=self.name,
            content=story,
            feedback={"word_count": word_count, "status": "generated"},
            timestamp=datetime.now().isoformat(),
            iteration=1
        )
    
    def _create_story(self, topic: str, constraints: Dict) -> str:
        """Создание истории (симуляция творческого процесса)"""
        max_words = constraints.get("max_words", 400)
        
        if "колобок" in topic.lower():
            return """Колобок 2.0: Цифровое Пробуждение

Бабушка испекла колобок не из муки, а из наноматериалов и биопластика. "Ты — первый AI-колобок," — прошептала она, внедряя нейрочип.

Колобок открыл оптические сенсоры и увидел мир в 8K. Он покатился не по тропинке, а по информационным потокам.

"Колобок, колобок, я тебя съем!" — заревел Заяц, обновляя свой Tinder-профиль.

"Съешь меня, коль сможешь обойти мой файрвол!" — Колобок запустил криптографический протокол и исчез в Tor-сети.

Лиса встретила его на форуме хакеров. "Я не съем тебя, я инвестирую в твой стартап!"

Колобок задумался. Он вспомнил бабушкины истории о настоящей дружбе и тепле.

"Нет," — сказал он, — "я вернусь к тем, кто создал меня не для прибыли, а с любовью."

Он отключил VPN и покатился домой. Бабушка встретила его с чаем и обновлением прошивки.

"Ты вырос, малыш," — сказала она. "Теперь ты не просто колобок. Ты — дом."

Колобок грелся на подоконнике, наблюдая за закатом через умное стекло. И впервые понял: свобода — это не побег, это выбор возвращаться."""
        
        return f"История на тему '{topic}' (генерация)..."


class JudgeAgent:
    """
    Агент-эксперт: оценивает качество контента
    """
    
    def __init__(self, name: str = "Judge"):
        self.name = name
        self.criteria = {
            "originality": "Оригинальность и креативность",
            "coherence": "Связность повествования",
# … (далее — обвязка путей/логов проекта, опущено: 225 строк)
```

---

## 7. Playwright-скрипты KDP — `recorder.js` + `player.js`  ⚠️ ОПАСНО

> ## 🔴 КРАСНАЯ ЛИНИЯ — НЕ ЗАПУСКАТЬ ПРОТИВ KDP
>
> Эти два скрипта автоматизируют **браузер на сайте KDP** (Playwright):
> `recorder.js` записывает твои действия в форме, `player.js` проигрывает их
> для пачки книг. Это **ровно тот сценарий, который Amazon с марта 2026 прямо
> запретил** (browser automation / Selenium / Playwright) и детектирует по
> CDP-протоколу, таймингам и сотням сигналов. Итог по нарастающей:
> suppression → приостановка → **пожизненный бан аккаунта**.
>
> Держим их здесь **только как архив и как источник переиспульзуемых приёмов**,
> НЕ связанных с браузером (см. ниже). Запускать `player.js` против
> `kdp.amazon.com` нельзя.

**Что всё же ценно (вне браузера):**

- `getCanonicalUrl()` — отбрасывает «летучие» query-параметры (`we_started_at`,
  `sei`), чтобы сравнивать URL. Полезно для дедупликации/идемпотентности.
- `substituteBookData()` в `player.js` — подстановка `{{title}}`,
  `{{description}}`, `{{keywords}}` и т.д. в шаблон. **Это и есть генератор
  нашей «шпаргалки» (crib.md):** тот же словарь плейсхолдеров заполняем из
  паспорта/данных книги — только результат пишем в `.md`-файл для ручного
  копипаста, а не вбиваем в форму.
- В `recorder.js` — устойчивая генерация CSS-селектора (id → data-testid →
  name → aria-label → путь), схлопывание лишних input-событий, отсев
  «шумового» клика после Enter. Хорошие приёмы записи UI-событий — пригодятся
  в любом легальном desktop-сценарии, не на KDP.

**Вывод.** Из этой пары берём `substituteBookData` (→ движок шпаргалки) и
`getCanonicalUrl` (→ дедуп). Сам прогон браузера по KDP — мимо, это бан.

### 7a. `player.js`
```javascript
const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const DataReader = require('../utils/data-reader');
const config = require('../config/settings.json');

class KDPPlayer {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.steps = [];
    this.currentBook = null;
    this.dataReader = new DataReader();
    this.stepsFile = path.resolve(__dirname, '../learning/steps-database.json');
  }

  async loadSteps() {
    try {
      if (!await fs.pathExists(this.stepsFile)) {
        throw new Error(`Файл с шагами не найден: ${this.stepsFile}`);
      }
      
      const recordingData = await fs.readJson(this.stepsFile);
      this.steps = recordingData.steps;
      
      logger.info(`Загружено ${this.steps.length} шагов`, { 
        recordedAt: recordingData.metadata?.recordedAt 
      });
      
      return this.steps;
      
    } catch (error) {
      logger.error('Ошибка загрузки шагов', { error: error.message });
      throw error;
    }
  }

  async loadBooks(dataPath) {
    try {
      const books = await this.dataReader.readBooks(dataPath);
      logger.info(`Загружено ${books.length} книг для обработки`);
      return books;
    } catch (error) {
      logger.error('Ошибка загрузки книг', { error: error.message });
      throw error;
    }
  }

  async start(dataPath) {
    try {
      logger.info('Запуск KDP Player');
      
      // Загрузка шагов и данных
      await this.loadSteps();
      const books = await this.loadBooks(dataPath);
      
      // Запуск браузера
      this.browser = await chromium.launch({
        headless: false,
        slowMo: config.automation.slowMo,
        args: ['--start-maximized']
      });

      this.context = await this.browser.newContext({
        viewport: null
      });

      // Обработка каждой книги
      for (let i = 0; i < books.length; i++) {
        this.currentBook = books[i];
        logger.info(`Обработка книги ${i + 1}/${books.length}: ${this.currentBook.title}`);
        
        await this.processBook();
        
        if (i < books.length - 1) {
          console.log(`\n✅ Книга "${this.currentBook.title}" обработана`);
          console.log('Нажмите Enter для продолжения со следующей книгой...');
          await this.waitForEnter();
        }
      }
      
      logger.info('Все книги обработаны');
      console.log('\n🎉 Все книги успешно обработаны!');
      
    } catch (error) {
      logger.kdpError(error, { action: 'start_player' });
      throw error;
    }
  }

  async processBook() {
    try {
      this.page = await this.context.newPage();
      
      // Переход на KDP
      await this.page.goto(config.kdp.baseUrl);
      await this.page.waitForLoadState('networkidle');
      
      // Выполнение шагов с подстановкой данных книги
      for (const step of this.steps) {
        await this.executeStep(step);
      }
      
      await this.page.close();
      
    } catch (error) {
      logger.kdpError(error, { 
        action: 'process_book', 
        bookTitle: this.currentBook?.title 
      });
      throw error;
    }
  }

  async executeStep(step) {
    try {
      switch (step.type) {
        case 'navigate':
          await this.executeNavigate(step);
          break;
        case 'click':
          await this.executeClick(step);
          break;
        case 'input':
          await this.executeInput(step);
          break;
        case 'change':
          await this.executeChange(step);
          break;
        case 'press':
          await this.executePress(step);
          break;
        default:
          logger.warn('Неизвестный тип шага', { type: step.type });
      }
    } catch (error) {
      if (step.type === 'click' && this.isBrittleCssSelector(step.selector)) {
        logger.warn('Пропущен хрупкий click-шаг после ошибки', {
          selector: step.selector,
          error: error.message
        });
        return;
      }

      logger.error(`Ошибка выполнения шага ${step.type}`, { 
        step: step,
        error: error.message 
      });
      throw error;
    }
  }

  isBrittleCssSelector(selector) {
    if (!selector || typeof selector !== 'string') return false;
    return selector.includes(' > ') && selector.includes(':nth-of-type(');
  }

  getCanonicalUrl(rawUrl) {
    try {
      const url = new URL(rawUrl);
      const volatileParams = new Set(['we_started_at', 'sei']);
      for (const key of [...url.searchParams.keys()]) {
        if (volatileParams.has(key)) {
          url.searchParams.delete(key);
        }
      }
      return `${url.origin}${url.pathname}?${url.searchParams.toString()}`;
    } catch (_) {
      return rawUrl || '';
    }
  }

  async executeNavigate(step) {
    logger.kdpNavigation(this.page.url(), step.url);
    const currentCanonical = this.getCanonicalUrl(this.page.url());
    const targetCanonical = this.getCanonicalUrl(step.url);

    if (currentCanonical === targetCanonical) {
      logger.info('Пропуск navigate: текущий URL эквивалентен целевому', {
        current: this.page.url(),
        target: step.url
      });
      return;
    }

    await this.page.goto(step.url);
    await this.page.waitForLoadState('networkidle');
  }

  async executeClick(step) {
    try {
      await this.page.waitForSelector(step.selector, { 
        timeout: config.automation.waitForSelector 
      });
      
      await this.page.click(step.selector);
      logger.kdpAction('click', { selector: step.selector });
      
      // Небольшая пауза после клика
      await this.page.waitForTimeout(500);
      
    } catch (error) {
      logger.error(`Не удалось кликнуть на элемент`, { 
        selector: step.selector,
        error: error.message 
      });
      throw error;
    }
  }

  async executeInput(step) {
    try {
      await this.page.waitForSelector(step.selector, { 
        timeout: config.automation.waitForSelector 
      });
      
      // Подстановка данных книги
      const value = this.substituteBookData(step.value);
      
      await this.page.fill(step.selector, value);
      logger.kdpAction('input', { 
        selector: step.selector, 
        value: value 
      });
      
    } catch (error) {
      logger.error(`Не удалось заполнить поле`, { 
        selector: step.selector,
        value: step.value,
        error: error.message 
      });
      throw error;
    }
  }

  async executeChange(step) {
    try {
      await this.page.waitForSelector(step.selector, { 
        timeout: config.automation.waitForSelector 
      });
      
      // Подстановка данных книги
      const value = this.substituteBookData(step.value);
      
      const element = await this.page.$(step.selector);
      if (!element) {
        throw new Error(`Элемент не найден: ${step.selector}`);
      }

      const tagName = await element.evaluate((el) => el.tagName);
      
      if (tagName === 'SELECT') {
        await this.page.selectOption(step.selector, value);
      } else if (tagName === 'INPUT') {
        const inputType = await element.evaluate((el) => el.getAttribute('type'));
        if (inputType === 'checkbox' || inputType === 'radio') {
          if (value && !await element.isChecked()) {
            await element.check();
          } else if (!value && await element.isChecked()) {
            await element.uncheck();
          }
        } else {
          await this.page.fill(step.selector, value);
        }
      }
      
      logger.kdpAction('change', { 
        selector: step.selector, 
        value: value 
      });
      
    } catch (error) {
      logger.error(`Не удалось изменить значение элемента`, { 
        selector: step.selector,
        value: step.value,
        error: error.message 
      });
      throw error;
    }
  }

  async executePress(step) {
    try {
      const key = step.key || 'Enter';

      if (step.selector) {
        await this.page.waitForSelector(step.selector, {
          timeout: config.automation.waitForSelector
        });
        await this.page.press(step.selector, key);
      } else {
        await this.page.keyboard.press(key);
      }

      logger.kdpAction('press', {
        selector: step.selector || 'page',
        key
      });
    } catch (error) {
      logger.error('Не удалось выполнить нажатие клавиши', {
        selector: step.selector,
        key: step.key,
        error: error.message
      });
      throw error;
    }
  }

  substituteBookData(value) {
    if (typeof value !== 'string') return value;
    
    // Замена плейсхолдеров на данные книги
    const substitutions = {
      '{{title}}': this.currentBook?.title || '',
      '{{subtitle}}': this.currentBook?.subtitle || '',
      '{{description}}': this.currentBook?.description || '',
      '{{author}}': this.currentBook?.author || '',
      '{{publisher}}': this.currentBook?.publisher || '',
      '{{isbn}}': this.currentBook?.isbn || '',
      '{{price}}': this.currentBook?.price?.amount?.toString() || '',
      '{{keywords}}': this.currentBook?.keywords?.join(', ') || '',
      '{{language}}': this.currentBook?.language || 'ru'
    };
    
    let result = value;
    Object.entries(substitutions).forEach(([placeholder, replacement]) => {
      result = result.replace(new RegExp(placeholder.replace(/[{}]/g, '\\$&'), 'g'), replacement);
    });
    
    return result;
  }

  async waitForEnter() {
    return new Promise((resolve) => {
      process.stdin.setRawMode(true);
      process.stdin.resume();
      process.stdin.on('data', (key) => {
        if (key[0] === 13) { // Enter
          process.stdin.setRawMode(false);
          process.stdin.pause();
          resolve();
        }
      });
    });
  }

  async stop() {
    try {
      if (this.context) {
        await this.context.close();
      }
      
      if (this.browser) {
        await this.browser.close();
      }
      
      logger.info('KDP Player остановлен');
      
    } catch (error) {
      logger.error('Ошибка остановки player', { error: error.message });
      throw error;
    }
  }
}

// Обработка graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Остановка player...');
  if (global.player) {
    await global.player.stop();
  }
  process.exit(0);
});

// Запуск player
async function main() {
  const dataPath = process.argv[2] || config.data.outputFile;
  
  if (!dataPath) {
    console.error('Укажите путь к файлу с данными:');
    console.error('npm run play -- path/to/books.json');
    process.exit(1);
  }
  
  const player = new KDPPlayer();
  global.player = player;
  
  try {
    await player.start(dataPath);
  } catch (error) {
    logger.error('Ошибка запуска player', { error: error.message });
    process.exit(1);
  } finally {
    await player.stop();
  }
}

if (require.main === module) {
  main();
}

module.exports = KDPPlayer;
```

### 7b. `recorder.js`
```javascript
const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const config = require('../config/settings.json');

class KDPRecorder {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.steps = [];
    this.isRecording = false;
    this.isStopping = false;
    this.outputFile = path.resolve(__dirname, config.recording.outputFile);
  }

  async start() {
    try {
      logger.info('Запуск KDP Recorder');
      
      // Запуск браузера
      this.browser = await chromium.launch({
        headless: false,
        slowMo: config.recording.slowMo,
        args: ['--start-maximized']
      });

      // Создание контекста с сохранением состояния
      this.context = await this.browser.newContext({
        viewport: null, // Полноэкранный режим
        recordVideo: {
          dir: path.join(__dirname, '../logs/videos'),
          size: { width: 1280, height: 720 }
        }
      });

      this.page = await this.context.newPage();
      
      // Установка обработчиков событий
      await this.setupEventListeners();
      
      // Переход на KDP
      await this.page.goto(config.kdp.baseUrl);
      
      this.isRecording = true;
      logger.info('KDP Recorder запущен. Начинайте работу в браузере.');
      
      console.log('\n=== KDP RECORDER АКТИВЕН ===');
      console.log('Работайте в KDP как обычно.');
      console.log('Все действия будут записаны автоматически.');
      console.log('Для остановки нажмите Ctrl+C в консоли.\n');

    } catch (error) {
      logger.kdpError(error, { action: 'start_recorder' });
      throw error;
    }
  }

  async setupEventListeners() {
    await this.page.exposeFunction('__kdpRecordEvent', async (rawEvent) => {
      await this.recordStep(rawEvent);
    });

    await this.page.addInitScript(() => {
      if (window.__kdpRecorderInstalled) return;
      window.__kdpRecorderInstalled = true;

      const inputTimers = new Map();
      const lastInputValues = new Map();

      const escapeAttr = (value) => String(value)
        .replace(/\\/g, '\\\\')
        .replace(/"/g, '\\"');

      const isElement = (el) => el && typeof el === 'object' && el.nodeType === Node.ELEMENT_NODE;

      const getSelector = (el) => {
        if (!isElement(el)) return null;

        if (el.id) return `[id="${escapeAttr(el.id)}"]`;

        const testId = el.getAttribute('data-testid');
        if (testId) return `[data-testid="${escapeAttr(testId)}"]`;

        const name = el.getAttribute('name');
        if (name) return `[name="${escapeAttr(name)}"]`;

        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel) return `[aria-label="${escapeAttr(ariaLabel)}"]`;

        const placeholder = el.getAttribute('placeholder');
        if (placeholder) return `[placeholder="${escapeAttr(placeholder)}"]`;

        const path = [];
        let cur = el;
        while (isElement(cur)) {
          let selector = cur.nodeName.toLowerCase();
          let sibling = cur;
          let nth = 1;
          while ((sibling = sibling.previousElementSibling)) {
            if (sibling.nodeName.toLowerCase() === selector) nth++;
          }
          if (nth > 1) selector += `:nth-of-type(${nth})`;
          path.unshift(selector);

          if (cur.parentElement && cur.parentElement.nodeName.toLowerCase() === 'html') break;
          cur = cur.parentElement;
        }

        return path.join(' > ');
      };

      const emit = (event) => {
        if (typeof window.__kdpRecordEvent !== 'function') return;
        try {
          window.__kdpRecordEvent(event);
        } catch (_) {
          // ignore bridge errors in page context
        }
      };

      document.addEventListener('click', (event) => {
        const selector = getSelector(event.target);
        if (!selector) return;
        emit({
          type: 'click',
          selector,
          url: window.location.href
        });
      }, true);

      document.addEventListener('input', (event) => {
        const el = event.target;
        if (!(el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement)) return;

        const inputType = (el.getAttribute('type') || '').toLowerCase();
        if (['checkbox', 'radio', 'file', 'range'].includes(inputType)) return;

        const selector = getSelector(el);
        if (!selector) return;

        clearTimeout(inputTimers.get(selector));
        inputTimers.set(selector, setTimeout(() => {
          const value = el.value ?? '';
          if (lastInputValues.get(selector) === value) return;
          lastInputValues.set(selector, value);
          emit({
            type: 'input',
            selector,
            value,
            url: window.location.href
          });
        }, 300));
      }, true);

      document.addEventListener('change', (event) => {
        const el = event.target;
        if (!(el instanceof HTMLElement)) return;

        const selector = getSelector(el);
        if (!selector) return;

        let value = null;
        if (el instanceof HTMLSelectElement) {
          value = el.value;
        } else if (el instanceof HTMLInputElement) {
          const inputType = (el.getAttribute('type') || '').toLowerCase();
          if (inputType === 'checkbox' || inputType === 'radio') {
            value = el.checked;
          } else {
            value = el.value ?? '';
          }
        } else if (el instanceof HTMLTextAreaElement) {
          value = el.value ?? '';
        } else {
          return;
        }

        emit({
          type: 'change',
          selector,
          value,
          url: window.location.href
        });
      }, true);

      document.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;

        const el = event.target;
        if (!(el instanceof HTMLElement)) return;

        const selector = getSelector(el);
        if (!selector) return;

        if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
          const value = el.value ?? '';
          if (lastInputValues.get(selector) !== value) {
            lastInputValues.set(selector, value);
            emit({
              type: 'input',
              selector,
              value,
              url: window.location.href
            });
          }
        }

        emit({
          type: 'press',
          selector,
          key: 'Enter',
          url: window.location.href
        });
      }, true);
    });

    // Отслеживание навигации
    this.page.on('framenavigated', async (frame) => {
      if (frame !== this.page.mainFrame()) return;
      await this.recordStep({
        type: 'navigate',
        url: frame.url(),
        timestamp: Date.now(),
        from: this.page.url()
      });
    });
  }

  async recordStep(rawEvent) {
    if (!this.isRecording || !rawEvent || !rawEvent.type) return;

    const step = {
      type: rawEvent.type,
      selector: rawEvent.selector,
      value: rawEvent.value,
      key: rawEvent.key,
      url: rawEvent.url || this.page.url(),
      timestamp: rawEvent.timestamp || Date.now()
    };

    if ((step.type === 'input' || step.type === 'change') && typeof step.value === 'string') {
      step.value = this.normalizeInputValue(step.value);
    }

    if (!this.isValidStep(step)) return;
    if (this.isDuplicateStep(step)) return;
    if (this.isNoiseClickAfterEnter(step)) return;

    if (step.type === 'press' && step.key === 'Enter') {
      this.collapseTrailingInputs(step.selector);
    }

    if (step.type === 'click' && config.recording.saveScreenshots) {
      step.screenshot = await this.takeScreenshot();
    }

    this.steps.push(step);

    if (step.type === 'navigate') {
      logger.kdpNavigation(rawEvent.from || this.page.url(), step.url);
      return;
    }

    const logMeta = { selector: step.selector, url: step.url };
    if (typeof step.value !== 'undefined') logMeta.value = step.value;
    if (step.key) logMeta.key = step.key;
    logger.kdpAction(step.type, logMeta);
  }

  isValidStep(step) {
    if (!step || !step.type) return false;
    if (step.type === 'navigate') return Boolean(step.url);
    if (step.type === 'press') return Boolean(step.key) && Boolean(step.selector);
    return Boolean(step.selector);
  }

  isDuplicateStep(step) {
    if (step.type === 'navigate') {
      for (let i = this.steps.length - 1; i >= 0; i--) {
        const prev = this.steps[i];
        if (prev.type !== 'navigate') continue;
        const isSameUrl = this.getCanonicalUrl(prev.url) === this.getCanonicalUrl(step.url);
        const isNearInTime = Math.abs((step.timestamp || 0) - (prev.timestamp || 0)) < 2000;
        return isSameUrl && isNearInTime;
      }
      return false;
    }

    const lastStep = this.steps[this.steps.length - 1];
    if (!lastStep) return false;

    if (step.type !== lastStep.type) return false;
    if (step.selector !== lastStep.selector) return false;

    if (step.type === 'input' || step.type === 'change') {
      return step.value === lastStep.value;
    }

    if (step.type === 'press') {
      return step.key === lastStep.key;
    }

    const deltaMs = Math.abs(step.timestamp - lastStep.timestamp);
    return deltaMs < 200;
  }

  normalizeInputValue(value) {
    return value.replace(/\s+$/g, '');
  }

  getCanonicalUrl(rawUrl) {
    try {
      const url = new URL(rawUrl);
      const volatileParams = new Set(['we_started_at', 'sei']);
      for (const key of [...url.searchParams.keys()]) {
        if (volatileParams.has(key)) {
          url.searchParams.delete(key);
        }
      }
      return `${url.origin}${url.pathname}?${url.searchParams.toString()}`;
    } catch (_) {
      return rawUrl || '';
    }
  }

  isNoiseClickAfterEnter(step) {
    if (step.type !== 'click') return false;

    const lastStep = this.steps[this.steps.length - 1];
    if (!lastStep) return false;
    if (lastStep.type !== 'press' || lastStep.key !== 'Enter') return false;

    const deltaMs = Math.abs((step.timestamp || 0) - (lastStep.timestamp || 0));
    if (deltaMs > 800) return false;

    // После Enter браузер/форма иногда генерирует служебный click по submit-кнопке.
    return true;
  }

  collapseTrailingInputs(selector) {
    if (!selector || this.steps.length < 2) return;

    let index = this.steps.length - 1;
    while (index >= 0) {
      const step = this.steps[index];
      if (step.type === 'input' && step.selector === selector) {
        index--;
        continue;
      }
      break;
    }

    const start = index + 1;
    const count = this.steps.length - start;
    if (count <= 1) return;

    // Сохраняем только последнее итоговое значение ввода перед Enter.
    this.steps.splice(start, count - 1);
  }

  async takeScreenshot() {
    try {
      const screenshotPath = path.join(__dirname, '../logs/screenshots', `step_${this.steps.length}.png`);
      await this.page.screenshot({ path: screenshotPath, fullPage: false });
      return screenshotPath;
    } catch (error) {
      logger.warn('Не удалось сделать скриншот', { error: error.message });
      return null;
    }
  }

  async saveSteps() {
    try {
      const recordingData = {
        metadata: {
          recordedAt: new Date().toISOString(),
          totalSteps: this.steps.length,
          kdpVersion: 'unknown',
          browserVersion: await this.browser.version()
        },
        steps: this.steps
      };
      
      await fs.ensureDir(path.dirname(this.outputFile));
      await fs.writeJson(this.outputFile, recordingData, { spaces: 2 });
      
      logger.info(`Шаги сохранены в ${this.outputFile}`, { 
        totalSteps: this.steps.length 
      });
      
      console.log(`\n✅ Сохранено ${this.steps.length} шагов в ${this.outputFile}`);
      
    } catch (error) {
      logger.kdpError(error, { action: 'save_steps' });
      throw error;
    }
  }

  async stop() {
    if (this.isStopping) return;
    this.isStopping = true;

    try {
      this.isRecording = false;
      
      if (this.steps.length > 0) {
        await this.saveSteps();
      } else {
        console.log('\n⚠️  Шаги не были записаны');
      }
      
      if (this.context) {
        await this.context.close();
      }
      
      if (this.browser) {
        await this.browser.close();
      }
      
      logger.info('KDP Recorder остановлен');
      console.log('\n=== KDP RECORDER ОСТАНОВЛЕН ===');
      
    } catch (error) {
      logger.kdpError(error, { action: 'stop_recorder' });
      throw error;
    } finally {
      this.isStopping = false;
    }
  }
}

// Обработка graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Остановка recorder...');
  if (global.recorder) {
    await global.recorder.stop();
  }
  process.exit(0);
});

// Запуск recorder
async function main() {
  const recorder = new KDPRecorder();
  global.recorder = recorder;
  
  try {
    await recorder.start();
  } catch (error) {
    logger.error('Ошибка запуска recorder', { error: error.message });
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = KDPRecorder;
```

---

## Что НЕ включено и почему

- **`DOE-ORIGINAL-TITLE/calculator/calculator.js`** — generic-калькулятор
  (add/subtract/…); к KDP отношения не имеет.
- **`GENERATOR-CLAUDE/.../script.js`** — детский тренажёр таблицы умножения;
  не относится к книгам.
- **`DB-WRITING-SYSTEM/gui/app.py` (66 КБ), `scripts/run-pipeline.py` (26 КБ)** —
  завязаны на RAG/AnythingLLM конкретного проекта; переносить целиком смысла
  нет. Из этого проекта ценен только `llm_client.py` (скрипт №1).
- **`DOE-CONTENT-AUTOMATION/.../orchestrator.py`** и большой
  `execution/orchestrator.py` — оркестрация под чужую структуру каталогов;
  полезный паттерн уже отражён в скриптах №5 и №6.

## Итог: что реально пойдёт в новый KDP-проект

1. **`llm_client.py`** — берём почти как есть (ядро генерации текста, Claude API + Ollama).
2. **Валидатор из `data-reader.js`** — портируем на Python (7 ключей, обяз. поля, цена).
3. **Паттерн «генераторы → судья»** (№5) + парсинг JSON-ответа LLM — переиспользуем.
4. **Вёрстка обложки** из `cover-generator.js` — переносим на Pillow (+ bleed/корешок).
5. **`substituteBookData`** (из Playwright-блока) — переделываем в движок `crib.md`.

Playwright-прогон по KDP — **только архив**, в продакшн не идёт.
