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
