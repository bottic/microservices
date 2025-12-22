const DEBUG = process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development';

export const logger = {
  debug: (...args: any[]) => {
    if (DEBUG) {
      console.log('[DEBUG]', ...args);
    }
  },
  
  info: (...args: any[]) => {
    console.log('[INFO]', ...args);
  },
  
  error: (...args: any[]) => {
    console.error('[ERROR]', ...args);
  },
  
  warn: (...args: any[]) => {
    console.warn('[WARN]', ...args);
  },
};

