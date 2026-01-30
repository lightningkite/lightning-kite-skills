#!/bin/bash
# Install Lightning Kite Skills for Claude Code
# Usage: ./install.sh [--uninstall]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

# Skills defined in this repo
SKILLS=(
    "kiteui"
    "kiteui-theming"
    "lightning-server"
    "lightning-server-kiteui"
    "ls5-kui7-migration"
    "model-design"
    "service-abstractions"
)

uninstall() {
    echo "Uninstalling Lightning Kite Skills..."
    for skill in "${SKILLS[@]}"; do
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
    echo "Uninstall complete."
}

install() {
    echo "Installing Lightning Kite Skills..."

    # Create skills directory if it doesn't exist
    if [ ! -d "$SKILLS_DIR" ]; then
        echo "  Creating $SKILLS_DIR"
        mkdir -p "$SKILLS_DIR"
    fi

    for skill in "${SKILLS[@]}"; do
        source="$SCRIPT_DIR/$skill"
        target="$SKILLS_DIR/$skill"

        # Check source exists
        if [ ! -d "$source" ]; then
            echo "  WARNING: Source not found: $source"
            continue
        fi

        # Check if target already exists
        if [ -L "$target" ]; then
            existing_target=$(readlink "$target")
            if [ "$existing_target" = "$source" ]; then
                echo "  Already installed: $skill"
            else
                echo "  Updating symlink: $skill"
                rm "$target"
                ln -s "$source" "$target"
            fi
        elif [ -e "$target" ]; then
            echo "  WARNING: $target exists but is not a symlink, skipping"
        else
            echo "  Installing: $skill -> $target"
            ln -s "$source" "$target"
        fi
    done

    echo ""
    echo "Installation complete!"
    echo ""
    echo "Installed skills:"
    for skill in "${SKILLS[@]}"; do
        if [ -L "$SKILLS_DIR/$skill" ]; then
            echo "  - $skill"
        fi
    done
}

# Parse arguments
case "${1:-}" in
    --uninstall|-u)
        uninstall
        ;;
    --help|-h)
        echo "Lightning Kite Skills Installer"
        echo ""
        echo "Usage:"
        echo "  ./install.sh           Install all skills (creates symlinks)"
        echo "  ./install.sh --uninstall  Remove all skill symlinks"
        echo "  ./install.sh --help       Show this help"
        echo ""
        echo "Skills included:"
        for skill in "${SKILLS[@]}"; do
            echo "  - $skill"
        done
        ;;
    "")
        install
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
