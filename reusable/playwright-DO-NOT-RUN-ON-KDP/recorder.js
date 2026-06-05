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
