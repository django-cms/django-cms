#!/bin/bash
# This script only exists for compatibility reasons to a legacy deploy system and
# will be removed. Please use the "start migrate" command to run migrations.
# Custom migrations can be added through the MIGRATION_COMMANDS setting.
set -x
start migrate
