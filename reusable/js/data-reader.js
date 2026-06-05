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
