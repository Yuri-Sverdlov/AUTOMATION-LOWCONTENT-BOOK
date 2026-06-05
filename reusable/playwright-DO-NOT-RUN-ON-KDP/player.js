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
