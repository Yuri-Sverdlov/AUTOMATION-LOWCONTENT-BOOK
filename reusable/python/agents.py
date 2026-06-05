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
            "engagement": "Увлекательность",
            "constraints": "Соблюдение ограничений (объем)",
            "theme_adherence": "Соответствие теме"
        }
    
    def evaluate(self, content: AgentResponse, constraints: Dict) -> AgentResponse:
        """Оценка контента"""
        print(f"\n[JUDGE] [{self.name}] Оценка контента...")
        
        evaluation = self._analyze(content.content, constraints)
        
        print(f"[SCORES] [{self.name}] Оценки:")
        for criterion, score in evaluation["scores"].items():
            bar = "█" * int(score / 2) + "░" * (5 - int(score / 2))
            print(f"   {criterion:20} {score}/10")
        
        print(f"   Общий балл: {evaluation['total_score']}/10")
        
        if evaluation["needs_refinement"]:
            print(f"   [!] Требуется доработка: {evaluation['improvement_areas']}")
        
        return AgentResponse(
            agent_name=self.name,
            content=content.content,
            feedback=evaluation,
            timestamp=datetime.now().isoformat(),
            iteration=content.iteration
        )
    
    def _analyze(self, text: str, constraints: Dict) -> Dict:
        """Анализ текста по критериям"""
        word_count = len(text.split())
        max_words = constraints.get("max_words", 400)
        
        # Симуляция анализа
        scores = {
            "originality": 9,
            "coherence": 8,
            "engagement": 8,
            "constraints": 10 if word_count <= max_words else 5,
            "theme_adherence": 9
        }
        
        total_score = sum(scores.values()) / len(scores)
        
        improvement_areas = []
        if scores["originality"] < 8:
            improvement_areas.append("усилить оригинальность")
        if scores["coherence"] < 8:
            improvement_areas.append("улучшить связность")
        if word_count > max_words:
            improvement_areas.append(f"сократить до {max_words} слов (сейчас {word_count})")
        
        return {
            "scores": scores,
            "total_score": round(total_score, 1),
            "word_count": word_count,
            "max_words": max_words,
            "needs_refinement": total_score < 8.5 or word_count > max_words,
            "improvement_areas": improvement_areas if improvement_areas else ["минимальные правки"],
            "strengths": ["интересная концепция", "хорошая атмосфера", "неожиданный финал"]
        }


class RefinerAgent:
    """
    Агент-редактор: улучшает контент на основе feedback
    """
    
    def __init__(self, name: str = "Refiner"):
        self.name = name
    
    def refine(self, content: AgentResponse, judge_feedback: Dict, 
               constraints: Dict, iteration: int) -> AgentResponse:
        """Улучшение контента"""
        print(f"\n[REFINE] [{self.name}] Доработка контента (итерация {iteration})...")
        
        original_text = content.content
        improvements = judge_feedback.get("feedback", {})
        
        # Симуляция доработки
        refined_text = self._apply_improvements(original_text, improvements, constraints)
        
        new_word_count = len(refined_text.split())
        print(f"[OK] [{self.name}] Доработано. Новый объем: {new_word_count} слов")
        
        return AgentResponse(
            agent_name=self.name,
            content=refined_text,
            feedback={
                "word_count": new_word_count,
                "improvements_applied": improvements.get("improvement_areas", []),
                "changes": ["оптимизация структуры", "усиление финала", "проверка объема"]
            },
            timestamp=datetime.now().isoformat(),
            iteration=iteration
        )
    
    def _apply_improvements(self, text: str, feedback: Dict, constraints: Dict) -> str:
        """Применение улучшений (симуляция)"""
        # В реальной системе здесь был бы LLM вызов с инструкциями
        # Для демонстрации возвращаем оптимизированный текст
        
        # Убедимся что текст соответствует лимиту
        max_words = constraints.get("max_words", 400)
        words = text.split()
        
        if len(words) > max_words:
            # Сокращаем, сохраняя суть
            truncated = words[:max_words]
            text = " ".join(truncated)
            # Добавляем завершающее предложение если нужно
            if not text.endswith('.'):
                text = text.rsplit(' ', 5)[0] + '."'
        
        return text


class ContentOrchestrator:
    """
    Оркестратор: управляет workflow агентов
    """
    
    def __init__(self, max_iterations: int = 3):
        self.generator = GeneratorAgent()
        self.judge = JudgeAgent()
        self.refiner = RefinerAgent()
        self.max_iterations = max_iterations
        self.history: List[AgentResponse] = []
    
    def run(self, topic: str, constraints: Dict) -> Dict:
        """Запуск полного цикла генерации"""
        print("=" * 60)
        print("MULTI-AGENT CONTENT GENERATION SYSTEM")
        print("=" * 60)
        print(f"\n[TOPIC] {topic}")
        print(f"[CONSTRAINTS] {constraints}")
        print(f"[MAX ITERATIONS] {self.max_iterations}")
        
        iteration = 1
        
        # Шаг 1: Генерация
        generated = self.generator.generate(topic, constraints)
        self.history.append(generated)
        
        current_content = generated
        
        # Цикл оценка → доработка
        while iteration <= self.max_iterations:
            print(f"\n{'-' * 60}")
            print(f"[ITERATION {iteration}]")
            print('-' * 60)
            
            # Шаг 2: Оценка
            evaluated = self.judge.evaluate(current_content, constraints)
            self.history.append(evaluated)
            
            feedback = evaluated.feedback
            
            # Проверяем качество
            if not feedback.get("needs_refinement", True):
                print(f"\n[QUALITY REACHED] На итерации {iteration}!")
                break
            
            if iteration >= self.max_iterations:
                print(f"\n[LIMIT REACHED] Достигнут лимит итераций")
                break
            
            # Шаг 3: Доработка
            refined = self.refiner.refine(
                current_content, 
                evaluated.__dict__, 
                constraints, 
                iteration + 1
            )
            self.history.append(refined)
            current_content = refined
            
            iteration += 1
        
        return self._compile_result()
    
    def _compile_result(self) -> Dict:
        """Сборка итогового результата"""
        final_content = None
        for response in reversed(self.history):
            if response.agent_name == "Refiner" or response.agent_name == "Generator":
                final_content = response.content
                break
        
        return {
            "final_content": final_content,
            "iterations": len([r for r in self.history if r.agent_name == "Judge"]),
            "history": [
                {
                    "agent": r.agent_name,
                    "iteration": r.iteration,
                    "timestamp": r.timestamp,
                    "feedback_summary": r.feedback
                }
                for r in self.history
            ],
            "word_count": len(final_content.split()) if final_content else 0
        }


# Запуск системы
if __name__ == "__main__":
    orchestrator = ContentOrchestrator(max_iterations=2)
    
    result = orchestrator.run(
        topic="Сказка 'Колобок' в новом исполнении (киберпанк/фантастика)",
        constraints={"max_words": 400, "style": "modern", "genre": "sci-fi"}
    )
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"\n{result['final_content']}")
    print(f"\n{'-' * 60}")
    print(f"[STATISTICS]")
    print(f"   - Words: {result['word_count']}")
    print(f"   - Refinement iterations: {result['iterations']}")
    print(f"   - Agents used: 3")
    print("=" * 60)
