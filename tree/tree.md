# tree
Generates ASCII tree structure of files and directories

## Usage
```bash
python tree.py [-h] [-d N] [-L N] [--dirs-only] [--files-only] [-a] [-l] [--gitignore] [-I PATTERN [PATTERN ...]] [--sort-by {name,size,modified}] [-r] [-s] [-p] [-f] [path]
```
### Postional arguments
 | Name | Description |
 | --- | --- |
 | path | Directory to visualize (default: current directory) |

### Options
 | Name | Description |
 | --- | --- |
 | -h, --help | Show help message and exit |
 | -d N, --depth N | Maximum depth to traverse |
 | -L N, --max-files N | Maximum number of files to display |
 | --dirs-only | Show only directories |
 | --files-only | Show only files |
 | -a, --all | Show hidden files (starting with .) |
 | -l, --follow-links | Follow symbolic links |
 | --gitignore | Respect .gitignore patterns |
 | -I PATTERN [PATTERN ...], --ignore PATTERN [PATTERN ...] | Patterns to ignore (supports wildcards) |
 | --sort-by {name,size,modified} | Sort entries by: name (default), size, or modified time |
 | -r, --reverse | Reverse sort order |
 | -s, --size | Show file sizes |
 | -p, --permissions | Show file permissions |
 | -f, --full-path | Show full path for each entry |