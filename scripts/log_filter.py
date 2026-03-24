#!/usr/bin/env python3
"""
Log Filter and Search Utility for Docker/Nginx Logs
Helps filter and search through container logs to diagnose issues
"""

import re
import sys
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """Log levels"""
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"
    UNKNOWN = "unknown"


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: Optional[datetime]
    level: LogLevel
    source: str
    message: str
    raw_line: str
    line_number: int


class LogFilter:
    """Main log filtering and search class"""
    
    def __init__(self, log_content: str):
        self.log_content = log_content
        self.log_entries: List[LogEntry] = []
        self._parse_logs()
    
    def _parse_logs(self):
        """Parse log content into structured entries"""
        lines = self.log_content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            entry = self._parse_line(line, line_num)
            self.log_entries.append(entry)
    
    def _parse_line(self, line: str, line_num: int) -> LogEntry:
        """Parse a single log line"""
        timestamp = None
        level = LogLevel.UNKNOWN
        source = ""
        message = line
        
        # Try to parse nginx-style timestamp: 2026/03/24 06:00:57
        timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})', line)
        if timestamp_match:
            try:
                timestamp = datetime.strptime(timestamp_match.group(1), '%Y/%m/%d %H:%M:%S')
            except ValueError:
                pass
        
        # Try to parse Docker-style timestamp: Mar 24, 2026, 11:30 AM
        docker_timestamp_match = re.search(
            r'([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+[AP]M)', 
            line
        )
        if docker_timestamp_match and not timestamp:
            try:
                timestamp = datetime.strptime(
                    docker_timestamp_match.group(1), 
                    '%b %d, %Y, %I:%M %p'
                )
            except ValueError:
                pass
        
        # Extract log level
        level_match = re.search(r'\[(\w+)\]', line)
        if level_match:
            level_str = level_match.group(1).lower()
            try:
                level = LogLevel(level_str)
            except ValueError:
                level = LogLevel.UNKNOWN
        
        # Extract source (script/module name)
        source_patterns = [
            r'^(/docker-entrypoint\.sh):',
            r'^(\d+-[\w-]+\.sh):',
            r'^([\w/\.-]+):',
        ]
        
        for pattern in source_patterns:
            source_match = re.match(pattern, line)
            if source_match:
                source = source_match.group(1)
                break
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            source=source,
            message=message,
            raw_line=line,
            line_number=line_num
        )
    
    def filter_by_level(self, levels: List[LogLevel]) -> List[LogEntry]:
        """Filter logs by log level"""
        return [entry for entry in self.log_entries if entry.level in levels]
    
    def filter_by_source(self, source_pattern: str) -> List[LogEntry]:
        """Filter logs by source pattern (regex)"""
        pattern = re.compile(source_pattern, re.IGNORECASE)
        return [entry for entry in self.log_entries if pattern.search(entry.source)]
    
    def filter_by_time_range(
        self, 
        start: Optional[datetime] = None, 
        end: Optional[datetime] = None
    ) -> List[LogEntry]:
        """Filter logs by time range"""
        filtered = []
        for entry in self.log_entries:
            if entry.timestamp:
                if start and entry.timestamp < start:
                    continue
                if end and entry.timestamp > end:
                    continue
                filtered.append(entry)
        return filtered
    
    def search(self, pattern: str, case_sensitive: bool = False) -> List[LogEntry]:
        """Search logs using regex pattern"""
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_pattern = re.compile(pattern, flags)
        return [entry for entry in self.log_entries if compiled_pattern.search(entry.message)]
    
    def search_errors(self) -> List[LogEntry]:
        """Search for error-related logs"""
        error_patterns = [
            r'error',
            r'failed',
            r'failure',
            r'critical',
            r'fatal',
            r'exception',
        ]
        pattern = '|'.join(error_patterns)
        return self.search(pattern)
    
    def search_warnings(self) -> List[LogEntry]:
        """Search for warning-related logs"""
        warning_patterns = [
            r'warning',
            r'warn',
            r'deprecated',
            r'differs',
        ]
        pattern = '|'.join(warning_patterns)
        return self.search(pattern)
    
    def extract_worker_processes(self) -> List[Dict]:
        """Extract worker process information"""
        workers = []
        for entry in self.log_entries:
            match = re.search(r'start worker process (\d+)', entry.message)
            if match:
                workers.append({
                    'pid': int(match.group(1)),
                    'timestamp': entry.timestamp,
                    'line_number': entry.line_number
                })
        return workers
    
    def extract_timestamps(self) -> List[datetime]:
        """Extract all timestamps from logs"""
        return [entry.timestamp for entry in self.log_entries if entry.timestamp]
    
    def get_statistics(self) -> Dict:
        """Get log statistics"""
        stats = {
            'total_lines': len(self.log_entries),
            'by_level': {},
            'by_source': {},
            'time_range': None,
            'worker_processes': len(self.extract_worker_processes()),
        }
        
        # Count by level
        for entry in self.log_entries:
            level_name = entry.level.value
            stats['by_level'][level_name] = stats['by_level'].get(level_name, 0) + 1
        
        # Count by source
        for entry in self.log_entries:
            if entry.source:
                stats['by_source'][entry.source] = stats['by_source'].get(entry.source, 0) + 1
        
        # Time range
        timestamps = self.extract_timestamps()
        if timestamps:
            stats['time_range'] = {
                'start': min(timestamps),
                'end': max(timestamps),
                'duration_seconds': (max(timestamps) - min(timestamps)).total_seconds()
            }
        
        return stats
    
    def format_entry(self, entry: LogEntry, show_line_numbers: bool = False) -> str:
        """Format a log entry for display"""
        parts = []
        
        if show_line_numbers:
            parts.append(f"[L{entry.line_number}]")
        
        if entry.timestamp:
            parts.append(entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        
        if entry.level != LogLevel.UNKNOWN:
            parts.append(f"[{entry.level.value.upper()}]")
        
        if entry.source:
            parts.append(f"({entry.source})")
        
        parts.append(entry.message)
        
        return ' '.join(parts)


def print_entries(entries: List[LogEntry], title: str = "Results", show_line_numbers: bool = True):
    """Print log entries in a formatted way"""
    print(f"\n{'='*60}")
    print(f"{title} ({len(entries)} entries)")
    print(f"{'='*60}")
    
    if not entries:
        print("No entries found.")
        return
    
    # Create a temporary LogFilter instance to use format_entry
    log_filter = LogFilter("")
    for entry in entries:
        print(log_filter.format_entry(entry, show_line_numbers))


def print_statistics(stats: Dict):
    """Print log statistics"""
    print(f"\n{'='*60}")
    print("LOG STATISTICS")
    print(f"{'='*60}")
    print(f"Total lines: {stats['total_lines']}")
    print(f"Worker processes: {stats['worker_processes']}")
    
    print(f"\nBy Level:")
    for level, count in stats['by_level'].items():
        print(f"  {level}: {count}")
    
    print(f"\nBy Source:")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")
    
    if stats['time_range']:
        tr = stats['time_range']
        print(f"\nTime Range:")
        print(f"  Start: {tr['start']}")
        print(f"  End: {tr['end']}")
        print(f"  Duration: {tr['duration_seconds']:.1f} seconds")


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Filter and search Docker/Nginx logs'
    )
    parser.add_argument(
        'input', nargs='?', 
        help='Input log file (default: stdin)'
    )
    parser.add_argument(
        '-l', '--level', 
        action='append', 
        choices=['info', 'notice', 'warning', 'error', 'debug'],
        help='Filter by log level (can be used multiple times)'
    )
    parser.add_argument(
        '-s', '--search', 
        help='Search pattern (regex)'
    )
    parser.add_argument(
        '--source', 
        help='Filter by source pattern (regex)'
    )
    parser.add_argument(
        '--errors', 
        action='store_true', 
        help='Show only errors'
    )
    parser.add_argument(
        '--warnings', 
        action='store_true', 
        help='Show only warnings'
    )
    parser.add_argument(
        '--workers', 
        action='store_true', 
        help='Extract worker process info'
    )
    parser.add_argument(
        '--stats', 
        action='store_true', 
        help='Show statistics'
    )
    parser.add_argument(
        '--line-numbers', 
        action='store_true', 
        help='Show line numbers'
    )
    
    args = parser.parse_args()
    
    # Read input
    if args.input:
        with open(args.input, 'r') as f:
            log_content = f.read()
    else:
        log_content = sys.stdin.read()
    
    # Create filter
    log_filter = LogFilter(log_content)
    
    # Apply filters
    results = log_filter.log_entries
    
    if args.level:
        levels = [LogLevel(l) for l in args.level]
        results = log_filter.filter_by_level(levels)
    
    if args.source:
        results = [e for e in results if re.search(args.source, e.source, re.IGNORECASE)]
    
    if args.search:
        pattern = re.compile(args.search, re.IGNORECASE)
        results = [e for e in results if pattern.search(e.message)]
    
    if args.errors:
        results = log_filter.search_errors()
    
    if args.warnings:
        results = log_filter.search_warnings()
    
    # Output results
    if args.stats:
        print_statistics(log_filter.get_statistics())
    
    if args.workers:
        workers = log_filter.extract_worker_processes()
        print(f"\n{'='*60}")
        print(f"WORKER PROCESSES ({len(workers)} total)")
        print(f"{'='*60}")
        for w in workers:
            print(f"  PID: {w['pid']}, Started: {w['timestamp']}, Line: {w['line_number']}")
    
    if not args.stats and not args.workers:
        print_entries(results, "Filtered Results", args.line_numbers)
    
    # Show summary if filtering was applied
    if args.level or args.source or args.search or args.errors or args.warnings:
        print(f"\nShowing {len(results)} of {len(log_filter.log_entries)} total entries")


if __name__ == '__main__':
    main()