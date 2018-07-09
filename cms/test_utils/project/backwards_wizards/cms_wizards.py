from cms.test_utils.project.backwards_wizard.wizards import wizard


# NOTE: We keep this line separate from the actual wizard definition
# because if both are in the same file then importing the wizard causes
# this line to run, which makes it impossible to test properly
wizard_pool.register(wizard)
