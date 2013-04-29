# Require any additional compass plugins here.

# Set this to the root of your project when deployed:
http_path = "" # use if other than /
sass_dir = "sass"
css_dir = "css"
images_dir = "images"
javascripts_dir = "js"

# be: :production or :development
environment = :production

# You can select your preferred output style here (can be overridden via the command line):
# output_style = :expanded or :nested or :compact or :compressed
output_style = (environment == :production) ? :compressed : :nested

# To enable relative paths to assets via compass helper functions. Uncomment:
# relative_assets = true

# To disable debugging comments that display the original location of your selectors. Uncomment:
line_comments = false

# If you prefer the indented syntax, you might want to regenerate this
# project again passing --syntax sass, or you can uncomment this:
# preferred_syntax = :sass
# and then run:
# sass-convert -R --from scss --to sass sass scss && rm -rf sass && mv scss sass