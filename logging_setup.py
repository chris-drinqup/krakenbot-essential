# Version: 1.5
# Revision Notes:
# - 1.0: Initial version with file-based logging for krakenbot and debug.log.
# - 1.1: Refactored to setup_logging function to avoid circular import.
# - 1.2: Restored module-level loggers, delayed config imports with init_logging.
# - 1.3: Set console logging to INFO unless args.verbose, kept DEBUG in files.
# - 1.4: Added ConsoleFilter, changed debug.log to errors_warnings.log, enhanced milestone filtering.
# - 1.5: Added update_fix_log function to append to fix_log.md for issues, fixes, and milestones. Added initialization logs and file write validation.

# Lessons Learned:
# - Use ConsoleFilter to suppress debug logs in console unless verbose to reduce noise.
# - Ensure errors_warnings.log for critical errors to align with log file naming.
# - Add update_fix_log to track issues and milestones for easier debugging.
# - Avoid circular imports by initializing loggers after config imports.
# - Request previous file version (e.g., logging_setup.py v1.4, logging_setup.py.bak3) if not provided to avoid missing functionality.
# - Never assume file content or version; verify explicitly with user-provided files.
# - Do not omit critical functions (e.g., update_fix_log, ConsoleFilter) unless intentionally deprecated.
# - Log initialization and file write attempts to diagnose logging setup issues.
# - Preserve all logic unless proven inferior; do not simplify complex logging configuration.

import logging
import os
from logging.handlers import RotatingFileHandler
from config import args, DEPENDENCY_DIR, RUN_ID

class ConsoleFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING or any(
            msg in record.getMessage() for msg in [
                "Generating OHLC", "Calculating features", "Training model",
                "switching to live trading", "Executing gobbler.sh", "Retraining model",
                "Enriching data"
            ]
        )

# Initialize main logger
logger = logging.getLogger('krakenbot')
logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
log_file = os.path.join(DEPENDENCY_DIR, 'krakenbot.log')
os.makedirs(DEPENDENCY_DIR, exist_ok=True)
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - RunID: %(run_id)s', defaults={'run_id': RUN_ID}))
logger.addHandler(file_handler)
if not args.no_nohup:
    console_handler = logging.StreamHandler()
    console_handler.addFilter(ConsoleFilter())
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

# Initialize debug logger
debug_logger = logging.getLogger('krakenbot.debug')
debug_logger.setLevel(logging.DEBUG)
debug_file = os.path.join(DEPENDENCY_DIR, 'errors_warnings.log')
debug_handler = RotatingFileHandler(debug_file, maxBytes=10*1024*1024, backupCount=5)
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - RunID: %(run_id)s', defaults={'run_id': RUN_ID}))
debug_logger.addHandler(debug_handler)
if args.verbose and not args.no_nohup:
    debug_console_handler = logging.StreamHandler()
    debug_console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    debug_logger.addHandler(debug_console_handler)

# Log initialization
logger.info(f"Initialized logger: level={'DEBUG' if args.verbose else 'INFO'}, log_file={log_file}, debug_file={debug_file}", extra={'run_id': RUN_ID})
debug_logger.debug(f"Logger handlers: main={logger.handlers}, debug={debug_logger.handlers}", extra={'run_id': RUN_ID})

def update_fix_log(issue_id, status, description, versions=None, outcome=None, notes=None, file_name=None):
    """Append an issue, fix, or milestone to fix_log.md."""
    fix_log_path = os.path.join(DEPENDENCY_DIR, 'fix_log.md')
    try:
        os.makedirs(DEPENDENCY_DIR, exist_ok=True)
        entry = [f"\n## {issue_id}", f"- **Status**: {status}", f"- **Description**: {description}"]
        if versions:
            entry.append("- **Versions**:")
            for v in versions:
                entry.append(f"  - {v}")
        if outcome:
            entry.append(f"- **Outcome**: {outcome}")
        if notes:
            entry.append(f"- **Notes**: {notes}")
        if file_name:
            entry.append(f"- **File**: {file_name}")
        entry.append(f"- **Timestamp**: {logging.Formatter().formatTime(logging.makeLogRecord({}))}")
        with open(fix_log_path, 'a') as f:
            f.write('\n'.join(entry) + '\n')
        logger.debug(f"Updated fix_log.md with {issue_id}", extra={'run_id': RUN_ID})
    except Exception as e:
        logger.error(f"Failed to update fix_log.md: {str(e)}", extra={'run_id': RUN_ID})
        debug_logger.debug(f"Detailed error in update_fix_log: {traceback.format_exc()}", extra={'run_id': RUN_ID})
        update_fix_log(
            issue_id="FixLogWriteError",
            status="Error",
            description=f"Failed to write to fix_log.md: {str(e)}",
            versions=[f"logging_setup.py v1.5"],
            notes="Check file permissions or DEPENDENCY_DIR path",
            file_name="logging_setup.py"
        )
