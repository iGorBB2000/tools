#!/usr/bin/env python3
"""
ASCII Tree Generator - Navigate and visualize directory structures

Usage:
    python tree.py [path] [options]

Examples:
    python tree.py
    python tree.py /home/user/project --depth 3
    python tree.py . --gitignore --max-files 100
    python tree.py ../src --dirs-only --sort-by size
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Set, Optional, Callable
import fnmatch


class TreeConfig:
    """Configuration for tree generation"""
    def __init__(self):
        self.max_depth: Optional[int] = None
        self.max_files: Optional[int] = None
        self.dirs_only: bool = False
        self.files_only: bool = False
        self.show_hidden: bool = False
        self.follow_links: bool = False
        self.use_gitignore: bool = False
        self.custom_ignore: List[str] = []
        self.sort_by: str = 'name'  # name, size, modified
        self.reverse_sort: bool = False
        self.show_size: bool = False
        self.show_permissions: bool = False
        self.full_path: bool = False
        self.gitignore_patterns: Set[str] = set()


class TreeGenerator:
    """Generate ASCII tree structure of directories"""
    
    # Box drawing characters
    PIPE = "│   "
    TEE = "├── "
    ELBOW = "└── "
    BLANK = "    "
    
    def __init__(self, config: TreeConfig):
        self.config = config
        self.file_count = 0
        self.dir_count = 0
        
        if config.use_gitignore:
            self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """Load patterns from .gitignore files"""
        gitignore_path = Path('.gitignore')
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.config.gitignore_patterns.add(line)
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        name = path.name
        
        # Hidden files
        if not self.config.show_hidden and name.startswith('.'):
            return True
        
        # Custom ignore patterns
        for pattern in self.config.custom_ignore:
            if fnmatch.fnmatch(name, pattern):
                return True
        
        # Gitignore patterns
        if self.config.use_gitignore:
            for pattern in self.config.gitignore_patterns:
                # Remove trailing slashes for directory patterns
                pattern = pattern.rstrip('/')
                if fnmatch.fnmatch(name, pattern):
                    return True
                # Check full relative path for patterns with /
                if '/' in pattern:
                    rel_path = str(path.relative_to(Path.cwd()))
                    if fnmatch.fnmatch(rel_path, pattern):
                        return True
        
        return False
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:6.1f} {unit}"
            size /= 1024.0
        return f"{size:6.1f} PB"
    
    def _get_sort_key(self) -> Callable:
        """Get sorting key function based on config"""
        if self.config.sort_by == 'size':
            return lambda p: p.stat().st_size if p.is_file() else 0
        elif self.config.sort_by == 'modified':
            return lambda p: p.stat().st_mtime
        else:  # name
            return lambda p: p.name.lower()
    
    def _get_entries(self, directory: Path) -> List[Path]:
        """Get sorted and filtered directory entries"""
        try:
            entries = [e for e in directory.iterdir() if not self._should_ignore(e)]
        except PermissionError:
            return []
        
        # Filter by type
        if self.config.dirs_only:
            entries = [e for e in entries if e.is_dir()]
        elif self.config.files_only:
            entries = [e for e in entries if e.is_file()]
        
        # Sort entries
        entries.sort(key=self._get_sort_key(), reverse=self.config.reverse_sort)
        
        # Separate directories and files for better organization
        if not self.config.files_only and not self.config.dirs_only:
            dirs = [e for e in entries if e.is_dir()]
            files = [e for e in entries if e.is_file()]
            entries = sorted(dirs, key=self._get_sort_key(), reverse=self.config.reverse_sort) + \
                     sorted(files, key=self._get_sort_key(), reverse=self.config.reverse_sort)
        
        return entries
    
    def _format_entry(self, path: Path) -> str:
        """Format a single entry with optional metadata"""
        name = str(path) if self.config.full_path else path.name
        
        # Add directory indicator
        if path.is_dir():
            name += "/"
        
        # Add size
        if self.config.show_size and path.is_file():
            try:
                size = self._format_size(path.stat().st_size)
                name = f"{name} ({size})"
            except:
                pass
        
        # Add permissions
        if self.config.show_permissions:
            try:
                mode = path.stat().st_mode
                perms = oct(mode)[-3:]
                name = f"[{perms}] {name}"
            except:
                pass
        
        return name
    
    def generate(self, directory: Path, prefix: str = "", depth: int = 0) -> str:
        """Generate tree structure recursively"""
        # Check depth limit
        if self.config.max_depth is not None and depth >= self.config.max_depth:
            return ""
        
        # Check file count limit
        if self.config.max_files is not None and self.file_count >= self.config.max_files:
            return ""
        
        if not directory.is_dir():
            return ""
        
        entries = self._get_entries(directory)
        output = []
        
        for i, entry in enumerate(entries):
            # Check file count limit
            if self.config.max_files is not None and self.file_count >= self.config.max_files:
                output.append(f"{prefix}{self.ELBOW}... (file limit reached)")
                break
            
            is_last = i == len(entries) - 1
            connector = self.ELBOW if is_last else self.TEE
            
            # Format and add entry
            formatted_name = self._format_entry(entry)
            output.append(f"{prefix}{connector}{formatted_name}")
            
            # Update counters
            if entry.is_dir():
                self.dir_count += 1
            else:
                self.file_count += 1
            
            # Recurse into directories
            if entry.is_dir():
                if self.config.follow_links or not entry.is_symlink():
                    extension = self.BLANK if is_last else self.PIPE
                    subtree = self.generate(entry, prefix + extension, depth + 1)
                    if subtree:
                        output.append(subtree)
        
        return '\n'.join(output)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate ASCII tree structure of directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Current directory, unlimited depth
  %(prog)s /path/to/dir --depth 3   # Limit to 3 levels deep
  %(prog)s . --gitignore            # Respect .gitignore patterns
  %(prog)s . --dirs-only            # Show only directories
  %(prog)s . --ignore "*.pyc" "*.log"  # Ignore specific patterns
  %(prog)s . --sort-by size --show-size  # Sort by size and show sizes
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory to visualize (default: current directory)'
    )
    
    parser.add_argument(
        '-d', '--depth',
        type=int,
        metavar='N',
        help='Maximum depth to traverse'
    )
    
    parser.add_argument(
        '-L', '--max-files',
        type=int,
        metavar='N',
        help='Maximum number of files to display'
    )
    
    parser.add_argument(
        '--dirs-only',
        action='store_true',
        help='Show only directories'
    )
    
    parser.add_argument(
        '--files-only',
        action='store_true',
        help='Show only files'
    )
    
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        dest='show_hidden',
        help='Show hidden files (starting with .)'
    )
    
    parser.add_argument(
        '-l', '--follow-links',
        action='store_true',
        help='Follow symbolic links'
    )
    
    parser.add_argument(
        '--gitignore',
        action='store_true',
        dest='use_gitignore',
        help='Respect .gitignore patterns'
    )
    
    parser.add_argument(
        '-I', '--ignore',
        nargs='+',
        metavar='PATTERN',
        default=[],
        help='Patterns to ignore (supports wildcards)'
    )
    
    parser.add_argument(
        '--sort-by',
        choices=['name', 'size', 'modified'],
        default='name',
        help='Sort entries by: name (default), size, or modified time'
    )
    
    parser.add_argument(
        '-r', '--reverse',
        action='store_true',
        dest='reverse_sort',
        help='Reverse sort order'
    )
    
    parser.add_argument(
        '-s', '--size',
        action='store_true',
        dest='show_size',
        help='Show file sizes'
    )
    
    parser.add_argument(
        '-p', '--permissions',
        action='store_true',
        dest='show_permissions',
        help='Show file permissions'
    )
    
    parser.add_argument(
        '-f', '--full-path',
        action='store_true',
        help='Show full path for each entry'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create config from arguments
    config = TreeConfig()
    config.max_depth = args.depth
    config.max_files = args.max_files
    config.dirs_only = args.dirs_only
    config.files_only = args.files_only
    config.show_hidden = args.show_hidden
    config.follow_links = args.follow_links
    config.use_gitignore = args.use_gitignore
    config.custom_ignore = args.ignore
    config.sort_by = args.sort_by
    config.reverse_sort = args.reverse_sort
    config.show_size = args.show_size
    config.show_permissions = args.show_permissions
    config.full_path = args.full_path
    
    # Validate path
    root_path = Path(args.path).resolve()
    if not root_path.exists():
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: Path '{args.path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Generate tree
    print(f"{root_path}/")
    generator = TreeGenerator(config)
    tree = generator.generate(root_path)
    if tree:
        print(tree)
    
    # Print summary
    print()
    print(f"{generator.dir_count} directories", end="")
    if not config.dirs_only:
        print(f", {generator.file_count} files", end="")
    print()


if __name__ == '__main__':
    main()