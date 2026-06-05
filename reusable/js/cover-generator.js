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
