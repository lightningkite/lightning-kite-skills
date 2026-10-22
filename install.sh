#!/bin/bash
# Install or update Lightning Kite Skills for Claude Code
# Usage: ./install.sh [--no-pull] [--uninstall] [--help]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
BACKUP_DIR="$HOME/.claude/skills-backups"

# A skill is any top-level directory holding a SKILL.md (or skill.md), so new skills install without editing this file.
find_skills() {
    for dir in "$SCRIPT_DIR"/*/; do
        dir="${dir%/}"
        if [ -f "$dir/SKILL.md" ] || [ -f "$dir/skill.md" ]; then
            basename "$dir"
        fi
    done
}

pull() {
    if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Pulling latest skills..."
        git -C "$SCRIPT_DIR" pull --ff-only || echo "  WARNING: git pull failed; installing the skills already checked out"
    else
        echo "Skipping pull: git can't read $SCRIPT_DIR as a repository; installing the skills already checked out"
    fi
    echo ""
}

# Removes links in the skills directory that point into this repo at skills that no longer exist.
remove_stale_links() {
    for target in "$SKILLS_DIR"/*; do
        [ -L "$target" ] || continue
        link=$(readlink "$target")
        case "$link" in
            "$SCRIPT_DIR"/*)
                if [ ! -e "$link" ]; then
                    echo "  Removing stale link: $(basename "$target")"
                    rm "$target"
                fi
                ;;
        esac
    done
}

uninstall() {
    echo "Uninstalling Lightning Kite Skills..."
    for skill in $(find_skills); do
        target="$SKILLS_DIR/$skill"
        if [ -L "$target" ]; then
            echo "  Removing symlink: $target"
            rm "$target"
        elif [ -e "$target" ]; then
            echo "  WARNING: $target exists but is not a symlink, skipping"
        else
            echo "  Skipping $skill (not installed)"
        fi
    done
    remove_stale_links
    echo "Uninstall complete."
}

install() {
    echo "Installing Lightning Kite Skills..."
    mkdir -p "$SKILLS_DIR"

    for skill in $(find_skills); do
        source="$SCRIPT_DIR/$skill"
        target="$SKILLS_DIR/$skill"

        if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
            echo "  Up to date: $skill"
            continue
        fi

        if [ -L "$target" ]; then
            echo "  Relinking: $skill"
            rm "$target"
        elif [ -e "$target" ]; then
            # Claude: a copied install never sees updates, so swap it for a link, keeping the copy in case it was edited.
            # The backup goes outside the skills directory, or Claude Code would load it as a second copy of the skill.
            backup="$BACKUP_DIR/$skill-$(date +%Y%m%d%H%M%S)"
            echo "  Replacing copy with link: $skill (old copy moved to $backup)"
            mkdir -p "$BACKUP_DIR"
            mv "$target" "$backup"
        else
            echo "  Installing: $skill"
        fi
        ln -s "$source" "$target"
    done

    remove_stale_links

    echo ""
    echo "Installation complete! Skills are symlinked, so later edits in this repo apply immediately."
    echo "Run ./install.sh again after pulling to pick up added or removed skills."
}

do_pull=true
action=install
for arg in "$@"; do
    case "$arg" in
        --no-pull)
            do_pull=false
            ;;
        --uninstall|-u)
            action=uninstall
            ;;
        --help|-h)
            echo "Lightning Kite Skills Installer"
            echo ""
            echo "Usage:"
            echo "  ./install.sh              Pull the repo, then install or update every skill (symlinks)"
            echo "  ./install.sh --no-pull    Install or update without pulling first"
            echo "  ./install.sh --uninstall  Remove all skill symlinks"
            echo "  ./install.sh --help       Show this help"
            echo ""
            echo "Skills included:"
            for skill in $(find_skills); do
                echo "  - $skill"
            done
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$action" = install ]; then
    if [ "$do_pull" = true ]; then
        pull
    fi
    install
else
    uninstall
fi
