from neverblock_client.constants import *
from neverblock_client.exceptions import *

import logging
import logging.handlers
import traceback

class LogHandler(logging.handlers.RotatingFileHandler):
    def emit(self, record):
        print self.format(record)
        logging.FileHandler.emit(self, record)

class LogFilter(logging.Filter):
    def filter(self, record):
        if record.levelno == logging.DEBUG:
            log_type = None
            if hasattr(record, 'type'):
                log_type = getattr(record, 'type')
            if log_type not in LOG_DEBUG_TYPES:
                return 0
        return 1

class LogFormatter(logging.Formatter):
    def format(self, record):
        try:
            formatted_record = ''

            try:
                formatted_record += logging.Formatter.format(self, record)
            except:
                try:
                    record.msg = record.msg.encode('string_escape')
                    formatted_record += logging.Formatter.format(self, record)
                except:
                    record.msg = 'Unreadable'
                    formatted_record += logging.Formatter.format(self, record)

            if hasattr(record, 'data') and record.data:
                traceback = record.data.pop('traceback', None)
                stdout = record.data.pop('stdout', None)
                stderr = record.data.pop('stderr', None)

                if record.data:
                    width = len(max(record.data, key=len))
                    for key, val in record.data.items():
                        formatted_record += '\n  %s = %r' % (
                            key.ljust(width), val)

                if stdout:
                    formatted_record += '\nProcess stdout:'
                    stdout_lines = stdout.split('\n')
                    if stdout_lines and not stdout_lines[-1]:
                        stdout_lines.pop()
                    for line in stdout_lines:
                        formatted_record += '\n  ' + line

                if stderr:
                    formatted_record += '\nProcess stderr:'
                    stderr_lines = stderr.split('\n')
                    if stderr_lines and not stderr_lines[-1]:
                        stderr_lines.pop()
                    for line in stderr_lines:
                        formatted_record += '\n  ' + line.decode('utf-8')

                if traceback:
                    formatted_record += \
                        '\nTraceback (most recent call last):\n'
                    formatted_record += ''.join(traceback).rstrip('\n')
        except:
            exception('Log format error')
            raise

        return formatted_record

def _log(log_level, log_msg, log_type, exc_info=None, **kwargs):
    getattr(logger, log_level)(log_msg, exc_info=exc_info, extra={
        'type': log_type,
        'data': kwargs,
    })

def debug(log_msg, log_type=None, **kwargs):
    _log('debug', log_msg, log_type, **kwargs)

def info(log_msg, log_type=None, **kwargs):
    _log('info', log_msg, log_type, **kwargs)

def warning(log_msg, log_type=None, **kwargs):
    kwargs['traceback'] = traceback.format_stack()
    _log('warning', log_msg, log_type, **kwargs)

def error(log_msg, log_type=None, **kwargs):
    kwargs['traceback'] = traceback.format_stack()
    _log('error', log_msg, log_type, **kwargs)

def critical(log_msg, log_type=None, **kwargs):
    kwargs['traceback'] = traceback.format_stack()
    _log('critical', log_msg, log_type, **kwargs)

def exception(log_msg, log_type=None, **kwargs):
    # Fix for python #15541
    _log('error', log_msg, log_type, exc_info=1, **kwargs)

if not os.path.exists(LOG_PATH):
    log_dir = os.path.dirname(LOG_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

logger = logging.getLogger(APP_NAME)
log_handler = LogHandler(LOG_PATH, backupCount=1, maxBytes=1000000)
log_filter = LogFilter()

logger.setLevel(logging.DEBUG)
logger.addFilter(log_filter)

log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(LogFormatter(
    '[%(asctime)s][%(levelname)s] %(message)s'))

logger.addHandler(log_handler)
