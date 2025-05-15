import os
from pathlib import Path


def load_gitignore_patterns(gitignore_path):
    patterns = []
    if not os.path.exists(gitignore_path):
        return patterns
    with open(gitignore_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns


def is_ignored(path, patterns):
    from fnmatch import fnmatch
    for pattern in patterns:
        # Handle directory ignore
        if pattern.endswith("/"):
            if Path(pattern.rstrip("/")) in Path(path).parents:
                return True
        # Handle file ignore
        if fnmatch(path, pattern) or fnmatch(os.path.basename(path), pattern):
            return True
    return False


def walk_codebase(root, patterns):
    for dirpath, dirnames, filenames in os.walk(root):
        # Remove ignored directories in-place
        dirnames[:] = [d for d in dirnames if not is_ignored(
            os.path.relpath(os.path.join(dirpath, d), root), patterns)]
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root)
            if is_ignored(rel_path, patterns):
                continue
            yield rel_path


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    gitignore_path = os.path.join(root, ".gitignore")
    patterns = load_gitignore_patterns(gitignore_path)
    output_file = os.path.join(root, "codebase_dump.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        for rel_path in walk_codebase(root, patterns):
            abs_path = os.path.join(root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue  # skip binary or unreadable files
            out.write(f"filepath: {rel_path}\n")
            out.write(content)
            out.write("\n" + "="*80 + "\n")
    print(f"Codebase written to {output_file}")


if __name__ == "__main__":
    main()
