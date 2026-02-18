# Shell Scripts Compatibility Guide

This document describes the cross-platform compatibility approach used in the scripts folder for Linux and macOS.

## Overview

All shell scripts in this folder are designed to work on both **Linux** and **macOS** despite differences in:
- Command-line tool versions (especially GNU vs BSD variants)
- Tool availability (e.g., `realpath` not in older macOS versions)
- Command syntax variations (e.g., `sed -i` syntax differs)

## Key Compatibility Issues & Solutions

### 1. **realpath Command**

**Problem:** `realpath` is not available on older macOS versions.

**Solution:** A `realpath()` wrapper function is defined in `scripts/functions`:
- On Linux and newer macOS: Uses the native `realpath` command
- On older macOS: Falls back to Python's `os.path.realpath()`

```bash
SCRIPTS=$(dirname "$(realpath "$0")")
```

### 2. **sed -i (in-place editing)**

**Problem:**
- macOS (BSD sed): requires `sed -i ''` (space before empty string)
- Linux (GNU sed): requires `sed -i` (no space, no empty string)

**Solution:** A `sed_inplace()` wrapper function is provided:
```bash
# Don't use sed -i directly!
# Use sed_inplace instead:
sed_inplace -e 's/old/new/' file.txt

# The function automatically handles both:
# - macOS: sed -i '' -e 's/old/new/' file.txt
# - Linux: sed -i -e 's/old/new/' file.txt
```

**Current Usage:** Some migration is still in progress. Scripts directly use:
- `sed -i ''` for macOS/BSD compatibility (works with both)
- Avoid GNU sed specific flags when possible

### 3. **awk Compatibility**

**Problem:** GNU awk and macOS awk have subtle differences:
- `-e` flag syntax differs
- Some built-in functions differ (e.g., `gensub`)
- Extended regex support varies

**Solution:** Avoid problematic patterns:
- ❌ DON'T: `awk -e '/pattern/ { print }' file`
- ✅ DO: `awk '/pattern/ { print }' file`
- Remove `-e` flags; they are not needed for basic operations

### 4. **apt-get (Linux-specific)**

**Problem:** `apt-get` only exists on Debian-based Linux systems.

**Solution:** Detect OS and use appropriate package manager:
```bash
if command -v apt-get &>/dev/null; then
    sudo apt-get -qq install gettext &>/dev/null
elif command -v brew &>/dev/null; then
    brew install gettext &>/dev/null
else
    error "Cannot install gettext: neither apt-get nor brew found."
fi
```

### 5. **Variable Quoting**

**Problem:** Unquoted variables can cause word splitting and globbing issues.

**Solution:** Always quote variables:
```bash
# ✅ DO: Quote variables
echo "$var"
test -z "${var}"

# ❌ DON'T: Unquoted variables
echo $var
test -z $var
```

## Best Practices

1. **Always source the functions file** before using compatibility helpers:
   ```bash
   source "${SCRIPTS}/functions"
   ```

2. **Use compatibility helpers** instead of raw commands:
   - Use `realpath` wrapper for path resolution
   - Use `sed_inplace` for in-place file editing

3. **Avoid platform-specific tools**:
   - Use `grep` instead of GNU-specific options
   - Use basic awk/sed patterns only
   - Use `command -v` to detect tools before using them

4. **Test on both platforms**:
   - Test scripts on Linux before pushing
   - Test scripts on macOS before pushing

5. **Quote everything**:
   - Quote variable expansions: `"$var"` not `$var`
   - Quote command substitutions: `"$(cmd)"` not `$(cmd)`

## Testing Compatibility

To test your changes:

### On Linux:
```bash
./script-name
```

### On macOS:
```bash
./script-name
```

## Common Tools & Their Versions

| Tool | Linux (GNU) | macOS (BSD) | Notes |
|------|------------|-----------|-------|
| awk | gawk | mawk | Avoid GNU-specific features |
| sed | GNU sed | BSD sed | Different `-i` syntax |
| grep | GNU grep | BSD grep | Generally compatible |
| realpath | ✓ | ✗ (older) | Use wrapper function |
| python | python3 | python3 | Should be available on both |

## Files Modified for Compatibility

- `scripts/functions` - Compatibility helper functions
- `scripts/filter-locale-changes` - Removed `-e` from awk
- `scripts/make-changelog` - Fixed sed -i and awk
- `scripts/make-release` - Fixed sed -i and awk
- `scripts/prepare-buildenv` - Added apt-get/brew detection
