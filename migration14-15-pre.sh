#!/bin/bash

## website modules ##
# https://github.com/OCA/website
# website_crm_quick_answer
# website_google_tag_manager
# website_legal_page
# website_odoo_debranding
## ##

REPO=product-pack
MODULE=product_pack
USER_ORG=ragabnet

#git clone https://github.com/OCA/$REPO -b 15.0
#cd $REPO
#git checkout -b 15.0-mig-$MODULE origin/15.0
#git format-patch --keep-subject --stdout origin/15.0..origin/14.0 -- $MODULE | git am -3 --keep
##
# Bump module version to 15.0.1.0.0.
# Remove any possible migration script from previous version.
# Squash administrative commits (if any) with the previous commit for reducing commit noise.
# They are named as "[UPD] README.rst", "[UPD] Update $MODULE.pot", "Update translation files"
# and similar names, and comes from OCA-git-bot, oca-travis or oca-transbot.
# IMPORTANT: Don't squash legit translation commits, authored by their translators,
# with the message "Translated using Weblate (...)".
##
pre-commit run -a  # to run black, isort and prettier (ignore pylint errors at this stage)
git add -A
git commit -m "[IMP] $MODULE: black, isort, prettier"  --no-verify  # it is important to do all formatting in one commit the first time
