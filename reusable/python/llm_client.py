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
